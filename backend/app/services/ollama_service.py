import time
from collections.abc import Sequence
from typing import Any

import httpx

from app.core.config import settings


class OllamaService:
    """Small wrapper around the local Ollama API."""

    def __init__(self) -> None:
        self.base_url = settings.ollama_base_url.rstrip("/")

    def list_models(self) -> list[str]:
        try:
            response = httpx.get(f"{self.base_url}/api/tags", timeout=15)
            response.raise_for_status()
            payload = response.json()
            models = payload.get("models", [])
            return [model.get("name", "") for model in models if model.get("name")]
        except Exception:
            return []

    def resolve_model(self, preferred: str | None = None) -> str:
        known_models = self.list_models()
        candidates = [
            preferred,
            settings.ollama_primary_model,
            settings.ollama_fast_model,
            settings.ollama_fallback_model,
        ]
        seen: set[str] = set()
        for candidate in candidates:
            if not candidate or candidate in seen:
                continue
            seen.add(candidate)
            if candidate in known_models:
                return candidate
        if known_models:
            return known_models[0]
        return preferred or settings.ollama_primary_model or "qwen3.6:latest"

    def chat(self, messages: Sequence[dict[str, Any]], model: str | None = None) -> dict[str, Any]:
        ordered_candidates = []
        preferred = model or settings.ollama_primary_model
        seen: set[str] = set()
        for candidate in [preferred, settings.ollama_primary_model, settings.ollama_fast_model, settings.ollama_fallback_model]:
            if not candidate or candidate in seen:
                continue
            seen.add(candidate)
            ordered_candidates.append(candidate)

        last_error: str | None = None
        for candidate in ordered_candidates:
            try:
                response = httpx.post(
                    f"{self.base_url}/api/chat",
                    json={
                        "model": candidate,
                        "messages": list(messages),
                        "stream": False,
                        "options": {"temperature": 0.2},
                    },
                    timeout=90,
                )
                if response.status_code >= 400:
                    last_error = response.text
                    continue
                payload = response.json()
                content = payload.get("message", {}).get("content")
                if content:
                    return {"model": candidate, "content": content}
                last_error = payload.get("error", str(payload))
            except Exception as exc:  # pragma: no cover - network failure path
                last_error = str(exc)
                continue

        if last_error:
            raise RuntimeError(f"Ollama request failed: {last_error}")
        raise RuntimeError("Ollama returned no usable generation output.")


ollama_service = OllamaService()


def get_reply(messages: Sequence[dict[str, Any]], model: str | None = None) -> tuple[str, str, int]:
    start = time.perf_counter()
    payload = ollama_service.chat(messages, model=model)
    elapsed_ms = int((time.perf_counter() - start) * 1000)
    return payload["content"], payload["model"], elapsed_ms
