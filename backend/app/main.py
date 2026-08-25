"""FastAPI entrypoint for वार्तालाप (Vartalaap)."""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .agents import Supervisor
from .config import BACKEND_ROOT, get_settings
from .rag import VectorStore, ingest
from .schemas import ChatRequest, ChatResponse


settings = get_settings()
supervisor = Supervisor()

app = FastAPI(
    title="वार्तालाप (Vartalaap) API",
    description=(
        "Dummy RAG-based chatbot mirroring the ADI (Axis Deep Intelligence) "
        "architecture. Instrumented so MLflow / Kytee can be attached later."
    ),
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
@app.get("/health")
def health() -> dict:
    store = VectorStore()
    try:
        collection_size = store.count()
    except Exception as exc:  # noqa: BLE001
        collection_size = -1
        error = str(exc)
    else:
        error = None
    return {
        "status": "ok",
        "llm_configured": settings.has_llm_key,
        "llm_model": settings.llm_model,
        "embedding_model": settings.embedding_model,
        "reranker_enabled": settings.reranker_enabled,
        "collection": settings.chroma_collection,
        "collection_size": collection_size,
        "collection_error": error,
    }


@app.get("/")
def root() -> dict:
    return {
        "name": "वार्तालाप",
        "latin": "Vartalaap",
        "docs": "/docs",
        "health": "/health",
        "chat": "POST /chat",
        "reindex": "POST /kb/reindex",
    }


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    if not request.query or not request.query.strip():
        raise HTTPException(status_code=400, detail="query is required")
    return supervisor.handle(request)


@app.post("/kb/reindex")
def reindex(reset: bool = False) -> dict:
    docs_root: Path = BACKEND_ROOT / "data" / "documents"
    faqs_csv: Path = BACKEND_ROOT / "data" / "faqs.csv"
    return ingest(documents_root=docs_root, faqs_csv=faqs_csv, reset=reset)


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
    )
