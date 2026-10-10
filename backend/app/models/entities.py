from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    filename: Mapped[str] = mapped_column(String(255))
    stored_path: Mapped[str] = mapped_column(String(1000))
    content_type: Mapped[str] = mapped_column(String(150))
    size_bytes: Mapped[int] = mapped_column(Integer)
    sha256: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    status: Mapped[str] = mapped_column(String(30), default="queued", index=True)
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
    jobs: Mapped[list["IngestionJob"]] = relationship(back_populates="document", cascade="all, delete-orphan")


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    title: Mapped[str] = mapped_column(String(255), default="New conversation")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
    messages: Mapped[list["Message"]] = relationship(back_populates="conversation", cascade="all, delete-orphan")


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    conversation_id: Mapped[str] = mapped_column(ForeignKey("conversations.id", ondelete="CASCADE"), index=True)
    role: Mapped[str] = mapped_column(String(20))
    content: Mapped[str] = mapped_column(Text)
    model_used: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sources_json: Mapped[str] = mapped_column(Text, default="[]")
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    conversation: Mapped[Conversation] = relationship(back_populates="messages")
    feedback: Mapped["Feedback | None"] = relationship(back_populates="message", cascade="all, delete-orphan", uselist=False)


class Feedback(Base):
    __tablename__ = "feedback"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    message_id: Mapped[str] = mapped_column(ForeignKey("messages.id", ondelete="CASCADE"), unique=True)
    helpful: Mapped[bool] = mapped_column(Boolean)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    message: Mapped[Message] = relationship(back_populates="feedback")


class IngestionJob(Base):
    __tablename__ = "ingestion_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), index=True)
    status: Mapped[str] = mapped_column(String(30), default="queued")
    progress: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
    document: Mapped[Document] = relationship(back_populates="jobs")


class ModelConfiguration(Base):
    __tablename__ = "model_configurations"

    role: Mapped[str] = mapped_column(String(40), primary_key=True)
    provider: Mapped[str] = mapped_column(String(40), default="ollama")
    model_tag: Mapped[str] = mapped_column(String(255))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)


class QuestionEvent(Base):
    __tablename__ = "question_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    question: Mapped[str] = mapped_column(Text)
    model_used: Mapped[str | None] = mapped_column(String(255), nullable=True)
    response_ms: Mapped[int] = mapped_column(Integer)
    retrieval_ms: Mapped[int] = mapped_column(Integer)
    generation_ms: Mapped[int] = mapped_column(Integer)
    source_ids_json: Mapped[str] = mapped_column(Text, default="[]")
    fallback_used: Mapped[bool] = mapped_column(Boolean, default=False)
    no_answer: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class EvaluationResult(Base):
    __tablename__ = "evaluation_results"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    dataset_name: Mapped[str] = mapped_column(String(255))
    metrics_json: Mapped[str] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
