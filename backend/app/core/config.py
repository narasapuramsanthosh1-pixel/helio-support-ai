from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    app_env: str = "development"
    database_url: str = "sqlite:///../data/helio.db"
    upload_dir: str = "../data/uploads"
    chroma_dir: str = "../data/chroma"
    ollama_base_url: str = "http://localhost:11434"
    ollama_primary_model: str = "qwen3.6:latest"
    ollama_fast_model: str = ""
    ollama_fallback_model: str = ""
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    chunk_size: int = 900
    chunk_overlap: int = 140
    retrieval_top_k: int = 5
    min_relevance_score: float = 0.32
    max_upload_mb: int = 20
    cors_origins: list[str] = ["http://localhost:5173"]

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("chunk_size")
    @classmethod
    def valid_chunk_size(cls, value: int) -> int:
        if value < 100:
            raise ValueError("CHUNK_SIZE must be at least 100 characters.")
        return value

    @field_validator("chunk_overlap")
    @classmethod
    def valid_overlap(cls, value: int) -> int:
        if value < 0:
            raise ValueError("CHUNK_OVERLAP cannot be negative.")
        return value

    def data_path(self, value: str) -> Path:
        path = Path(value)
        return (PROJECT_ROOT / path).resolve() if not path.is_absolute() else path


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
