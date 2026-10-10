import csv
import hashlib
import re
from pathlib import Path

import fitz
from docx import Document

from app.core.config import settings


def hash_file(path: str | Path) -> str:
    hasher = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def extract_text_from_file(file_path: str | Path) -> str:
    path = Path(file_path)
    suffix = path.suffix.lower()

    if suffix == ".pdf":
        text_parts: list[str] = []
        with fitz.open(path) as document:
            for page in document:
                text = page.get_text("text")
                if text:
                    text_parts.append(text)
        return normalize_text("\n".join(text_parts))

    if suffix == ".docx":
        document = Document(path)
        paragraphs = [paragraph.text for paragraph in document.paragraphs if paragraph.text.strip()]
        return normalize_text("\n".join(paragraphs))

    if suffix in {".txt", ".md", ".markdown"}:
        return normalize_text(path.read_text(encoding="utf-8", errors="ignore"))

    if suffix == ".csv":
        lines: list[str] = []
        with path.open("r", encoding="utf-8", errors="ignore", newline="") as handle:
            reader = csv.reader(handle)
            for row in reader:
                if row:
                    lines.append(" | ".join(part.strip() for part in row if part and part.strip()))
        return normalize_text("\n".join(lines))

    raise ValueError(f"Unsupported file type: {suffix}")


def split_text(text: str, chunk_size: int | None = None, chunk_overlap: int | None = None) -> list[str]:
    chunk_size = chunk_size or settings.chunk_size
    chunk_overlap = chunk_overlap or settings.chunk_overlap
    if len(text) <= chunk_size:
        return [text.strip()] if text.strip() else []

    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        segment = text[start:end].strip()
        if segment:
            chunks.append(segment)
        if end >= len(text):
            break
        start = max(start + 1, end - chunk_overlap)
    return [chunk for chunk in chunks if chunk]


class EmbeddingService:
    """Sentence transformer wrapper with a lightweight fallback for offline runs."""

    def __init__(self) -> None:
        self._model = None

    def _load_model(self):
        if self._model is not None:
            return self._model
        try:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(settings.embedding_model)
            return self._model
        except Exception:
            return None

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        model = self._load_model()
        if model is not None:
            embeddings = model.encode(texts, convert_to_numpy=True)
            return [list(map(float, vector)) for vector in embeddings]
        return [self._fallback_embedding(text) for text in texts]

    @staticmethod
    def _fallback_embedding(text: str) -> list[float]:
        vector = [0.0] * 384
        for index, character in enumerate(text.encode("utf-8")[:384]):
            vector[index % 384] += float(character)
        magnitude = sum(value * value for value in vector) ** 0.5
        if magnitude:
            vector = [value / magnitude for value in vector]
        return vector


class VectorStore:
    """Simplified Chroma client wrapper for storing chunks and metadata."""

    def __init__(self, collection_name: str = "helio-support") -> None:
        import chromadb

        self.client = chromadb.PersistentClient(path=settings.chroma_dir)
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        self.embedding_service = EmbeddingService()

    def add_chunks(self, document_id: str, filename: str, chunks: list[str]) -> None:
        if not chunks:
            return
        ids = [f"{document_id}:{index}" for index in range(len(chunks))]
        embeddings = self.embedding_service.embed_texts(chunks)
        metadatas = [
            {
                "document_id": document_id,
                "filename": filename,
                "chunk_index": index,
                "source": filename,
            }
            for index in range(len(chunks))
        ]
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=chunks,
            metadatas=metadatas,
        )

    def search(self, query: str, top_k: int = 5) -> list[dict[str, object]]:
        query_embedding = self.embedding_service.embed_texts([query])[0]
        result = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )
        hits: list[dict[str, object]] = []
        for index, document in enumerate(result.get("documents", [[]])[0]):
            metadata = result.get("metadatas", [[]])[0][index]
            distance = result.get("distances", [[]])[0][index]
            hit = {
                "text": document,
                "document_id": metadata.get("document_id"),
                "filename": metadata.get("filename"),
                "score": max(0.0, 1.0 - float(distance)),
                "chunk_index": metadata.get("chunk_index"),
            }
            hits.append(hit)
        return hits

    def delete_document(self, document_id: str) -> None:
        self.collection.delete(where={"document_id": document_id})
