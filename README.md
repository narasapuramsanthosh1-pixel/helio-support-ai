# Helio Support AI

This workspace contains a production-style customer support RAG starter built with a Python FastAPI backend and a React + TypeScript frontend scaffold.

## Backend

- Python 3.12
- FastAPI + SQLAlchemy + SQLite
- ChromaDB-backed vector store
- Ollama integration for local LLM chat
- Document ingestion for PDF, DOCX, TXT, CSV, and Markdown

Run:

```bash
cd backend
python3 -m pip install -r requirements.txt
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Frontend

The frontend is scaffolded for Vite + React + TypeScript + Tailwind CSS.

```bash
cd frontend
npm install
npm run dev -- --host 0.0.0.0
```

## Notes

- The backend is already wired to a local SQLite database under `data/helio.db`.
- The vector store uses the local `data/chroma` directory.
- Model availability is checked through the installed Ollama runtime, and the primary model is configured as `qwen3.6:latest` by default.
- The app intentionally avoids hard-coded production statistics; dashboard metrics come from API responses and empty-state values when no data exists.
