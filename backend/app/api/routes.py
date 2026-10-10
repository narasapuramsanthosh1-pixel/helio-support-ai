import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import PROJECT_ROOT, settings
from app.db.session import get_db
from app.models.entities import Conversation, Document, Feedback, IngestionJob, Message, QuestionEvent
from app.services.ingestion import VectorStore, extract_text_from_file, hash_file, split_text
from app.services.ollama_service import get_reply

router = APIRouter(prefix="/api")

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md", ".markdown", ".csv"}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _document_payload(document: Document) -> dict[str, object]:
    last_job = document.jobs[-1] if document.jobs else None
    return {
        "id": document.id,
        "filename": document.filename,
        "stored_path": document.stored_path,
        "content_type": document.content_type,
        "size_bytes": document.size_bytes,
        "sha256": document.sha256,
        "status": document.status,
        "chunk_count": document.chunk_count,
        "error": document.error,
        "created_at": document.created_at.isoformat() if document.created_at else None,
        "updated_at": document.updated_at.isoformat() if document.updated_at else None,
        "ingestion_status": getattr(last_job, "status", None),
        "ingestion_progress": getattr(last_job, "progress", None),
    }


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/overview")
def overview(db: Session = Depends(get_db)) -> dict[str, object]:
    documents_count = db.query(Document).count()
    chunk_count = db.query(func.coalesce(func.sum(Document.chunk_count), 0)).scalar() or 0
    answer_count = db.query(Message).filter(Message.role == "assistant").count()
    user_message_count = db.query(Message).filter(Message.role == "user").count()
    retrieval_hits = db.query(Message).filter(Message.sources_json != "[]").count()
    grounded_rate = (retrieval_hits / user_message_count) if user_message_count else 0.0
    avg_latency = db.query(func.avg(Message.latency_ms)).filter(Message.role == "assistant").scalar() or 0

    recent_documents = db.query(Document).order_by(Document.created_at.desc()).limit(5).all()
    recent_questions = db.query(Message).filter(Message.role == "user").order_by(Message.created_at.desc()).limit(5).all()

    vector_store = VectorStore()
    try:
        vector_count = vector_store.collection.count()
    except Exception:
        vector_count = 0

    return {
        "total_documents": documents_count,
        "total_chunks": int(chunk_count),
        "questions_answered": answer_count,
        "retrieval_hit_rate": round(grounded_rate * 100, 2),
        "grounded_answer_rate": round(grounded_rate * 100, 2),
        "average_response_latency_ms": round(float(avg_latency), 2),
        "recent_documents": [_document_payload(item) for item in recent_documents],
        "recent_questions": [
            {"id": item.id, "content": item.content, "created_at": item.created_at.isoformat()} for item in recent_questions
        ],
        "llm_status": {
            "primary_model": settings.ollama_primary_model,
            "fast_model": settings.ollama_fast_model or "not configured",
            "fallback_model": settings.ollama_fallback_model or "not configured",
        },
        "vector_database_health": {"collection_count": vector_count, "status": "healthy" if vector_count else "empty"},
    }


@router.get("/documents")
def list_documents(db: Session = Depends(get_db)) -> list[dict[str, object]]:
    documents = db.query(Document).order_by(Document.created_at.desc()).all()
    return [_document_payload(document) for document in documents]


@router.get("/documents/{document_id}")
def get_document(document_id: str, db: Session = Depends(get_db)) -> dict[str, object]:
    document = db.query(Document).filter(Document.id == document_id).one_or_none()
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return _document_payload(document)


@router.post("/documents/upload")
async def upload_documents(
    files: list[UploadFile] = File(default=[]),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    if not files:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No files were uploaded.")

    upload_dir = Path(PROJECT_ROOT) / settings.upload_dir
    upload_dir.mkdir(parents=True, exist_ok=True)
    saved_documents: list[dict[str, object]] = []

    for uploaded_file in files:
        filename = uploaded_file.filename or "uploaded-file"
        suffix = Path(filename).suffix.lower()
        if suffix not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type for {filename}.",
            )

        contents = await uploaded_file.read()
        if len(contents) > settings.max_upload_mb * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File {filename} exceeds the {settings.max_upload_mb} MB limit.",
            )

        file_hash = hash_file
        # Use a temporary SHA-check on the byte stream, then persist to disk.
        digest = __import__("hashlib").sha256(contents).hexdigest()
        existing = db.query(Document).filter(Document.sha256 == digest).one_or_none()
        if existing:
            saved_documents.append({"id": existing.id, "filename": existing.filename, "status": "already_indexed"})
            continue

        storage_path = upload_dir / f"{uuid4()}_{filename}"
        storage_path.write_bytes(contents)

        document = Document(
            id=str(uuid4()),
            filename=filename,
            stored_path=str(storage_path),
            content_type=uploaded_file.content_type or "application/octet-stream",
            size_bytes=len(contents),
            sha256=digest,
            status="queued",
        )
        db.add(document)
        db.flush()

        job = IngestionJob(id=str(uuid4()), document_id=document.id, status="queued", progress=5)
        db.add(job)

        try:
            extracted = extract_text_from_file(storage_path)
            if not extracted:
                document.status = "failed"
                document.error = "No extractable text found in the uploaded file."
                job.status = "failed"
                job.progress = 100
                db.commit()
                saved_documents.append(_document_payload(document))
                continue
            chunks = split_text(extracted, settings.chunk_size, settings.chunk_overlap)
            if not chunks:
                raise ValueError("The uploaded document did not produce any chunks after parsing.")

            vector_store = VectorStore()
            vector_store.add_chunks(document.id, document.filename, chunks)
            document.status = "indexed"
            document.chunk_count = len(chunks)
            document.error = None
            job.status = "completed"
            job.progress = 100
            db.commit()
            saved_documents.append(_document_payload(document))
        except Exception as exc:  # pragma: no cover - ingestion failure path
            document.status = "failed"
            document.error = str(exc)
            job.status = "failed"
            job.progress = 100
            db.commit()
            saved_documents.append(_document_payload(document))

    return {"documents": saved_documents}


@router.delete("/documents/{document_id}")
def delete_document(document_id: str, db: Session = Depends(get_db)) -> dict[str, str]:
    document = db.query(Document).filter(Document.id == document_id).one_or_none()
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    try:
        VectorStore().delete_document(document_id)
    except Exception:
        pass

    file_path = Path(document.stored_path)
    if file_path.exists():
        file_path.unlink(missing_ok=True)

    db.delete(document)
    db.commit()
    return {"status": "deleted", "document_id": document_id}


@router.get("/models")
def list_models() -> dict[str, object]:
    service = VectorStore()
    # We deliberately keep model status lightweight and rely on the Ollama API for runtime availability.
    return {
        "available": [settings.ollama_primary_model, settings.ollama_fast_model, settings.ollama_fallback_model],
        "vector_store": {"collection": service.collection.name if hasattr(service.collection, "name") else "helio-support"},
    }


@router.get("/conversations")
def list_conversations(db: Session = Depends(get_db)) -> list[dict[str, object]]:
    conversations = db.query(Conversation).order_by(Conversation.updated_at.desc()).all()
    return [{
        "id": conversation.id,
        "title": conversation.title,
        "message_count": len(conversation.messages),
        "created_at": conversation.created_at.isoformat(),
        "updated_at": conversation.updated_at.isoformat(),
    } for conversation in conversations]


@router.post("/conversations")
def create_conversation(db: Session = Depends(get_db)) -> dict[str, object]:
    conversation = Conversation(id=str(uuid4()), title="New conversation")
    db.add(conversation)
    db.commit()
    return {"id": conversation.id, "title": conversation.title}


@router.get("/conversations/{conversation_id}")
def get_conversation(conversation_id: str, db: Session = Depends(get_db)) -> dict[str, object]:
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).one_or_none()
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    return {
        "id": conversation.id,
        "title": conversation.title,
        "messages": [
            {
                "id": message.id,
                "role": message.role,
                "content": message.content,
                "model_used": message.model_used,
                "sources": json.loads(message.sources_json or "[]"),
                "latency_ms": message.latency_ms,
                "created_at": message.created_at.isoformat(),
            }
            for message in sorted(conversation.messages, key=lambda item: item.created_at)
        ],
    }


@router.post("/conversations/{conversation_id}/clear")
def clear_conversation(conversation_id: str, db: Session = Depends(get_db)) -> dict[str, str]:
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).one_or_none()
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    for message in conversation.messages:
        db.delete(message)
    conversation.title = "New conversation"
    db.commit()
    return {"status": "cleared", "conversation_id": conversation_id}


@router.post("/chat")
def ask_question(
    question: str = Form(...),
    conversation_id: str | None = Form(default=None),
    model: str | None = Form(default=None),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    if not question.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A question is required.")

    conversation = None
    if conversation_id:
        conversation = db.query(Conversation).filter(Conversation.id == conversation_id).one_or_none()
    if conversation is None:
        conversation = Conversation(id=str(uuid4()), title=question[:60] or "New conversation")
        db.add(conversation)
        db.flush()

    user_message = Message(
        id=str(uuid4()),
        conversation_id=conversation.id,
        role="user",
        content=question,
    )
    db.add(user_message)
    db.flush()

    vector_store = VectorStore()
    hits = vector_store.search(question, top_k=settings.retrieval_top_k)
    sources: list[dict[str, object]] = []
    evidence: list[str] = []
    for hit in hits:
        score = float(hit.get("score", 0.0))
        if score < settings.min_relevance_score:
            continue
        evidence.append(str(hit.get("text", "")))
        sources.append(
            {
                "document_id": hit.get("document_id"),
                "filename": hit.get("filename"),
                "chunk_index": hit.get("chunk_index"),
                "score": round(score, 4),
                "excerpt": str(hit.get("text", ""))[:500],
            }
        )

    if not evidence:
        answer = "I could not find enough relevant information in the current knowledge base to answer this confidently. Please add or reindex supporting documents."
        model_used = model or settings.ollama_primary_model
        response_message = Message(
            id=str(uuid4()),
            conversation_id=conversation.id,
            role="assistant",
            content=answer,
            model_used=model_used,
            sources_json=json.dumps([]),
            latency_ms=0,
        )
        db.add(response_message)
        db.commit()
        return {
            "conversation_id": conversation.id,
            "answer": answer,
            "sources": [],
            "model": model_used,
            "latency_ms": 0,
        }

    context = "\n\n".join(evidence)
    messages = [
        {"role": "system", "content": "You are a support assistant. Use only the provided evidence. Cite the source document names when possible and avoid making unsupported claims."},
        {"role": "user", "content": f"Question: {question}\n\nEvidence:\n{context}"},
    ]

    try:
        answer, model_used, latency_ms = get_reply(messages, model=model)
    except RuntimeError:
        answer = "The language model is currently unavailable. Please try again later or select a different model."
        model_used = model or settings.ollama_primary_model
        latency_ms = 0

    response_message = Message(
        id=str(uuid4()),
        conversation_id=conversation.id,
        role="assistant",
        content=answer,
        model_used=model_used,
        sources_json=json.dumps(sources),
        latency_ms=latency_ms,
    )
    db.add(response_message)
    db.flush()

    question_record = QuestionEvent(
        id=str(uuid4()),
        question=question,
        model_used=model_used,
        response_ms=latency_ms,
        retrieval_ms=0,
        generation_ms=latency_ms,
        source_ids_json=json.dumps([item["document_id"] for item in sources]),
        fallback_used=model is not None and model_used != model,
        no_answer=not sources,
    )
    db.add(question_record)
    db.commit()

    conversation.title = question[:60] or "New conversation"
    conversation.updated_at = utc_now()
    db.commit()
    return {
        "conversation_id": conversation.id,
        "answer": answer,
        "sources": sources,
        "model": model_used,
        "latency_ms": latency_ms,
    }


@router.post("/feedback/{message_id}")
def submit_feedback(message_id: str, helpful: bool = Form(...), comment: str | None = Form(default=None), db: Session = Depends(get_db)) -> dict[str, object]:
    message = db.query(Message).filter(Message.id == message_id).one_or_none()
    if not message:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")

    feedback = Feedback(id=str(uuid4()), message_id=message.id, helpful=helpful, comment=comment)
    db.add(feedback)
    db.commit()
    return {"status": "saved", "message_id": message_id, "helpful": helpful}
