"""FastAPI entrypoint for वार्तालाप (Vartalaap)."""
from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .agents import Supervisor
from .config import BACKEND_ROOT, get_settings
from .observability import EventEmitter, log_feedback
from .rag import VectorStore, ingest
from .schemas import (
    ChatRequest,
    ChatResponse,
    FeedbackRequest,
    FeedbackResponse,
    MessageClass,
    MessageTag,
)


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
        "mlflow_enabled": settings.mlflow_enabled,
        "mlflow_tracking_uri": settings.mlflow_tracking_uri_resolved,
        "mlflow_experiment": settings.mlflow_experiment,
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


@app.post("/feedback", response_model=FeedbackResponse)
def feedback(request: FeedbackRequest) -> FeedbackResponse:
    if not request.message_id.strip():
        raise HTTPException(status_code=400, detail="message_id is required")

    emitter = EventEmitter(
        session_id=request.session_id,
        user_id=request.user_id,
    )
    emitter.emit(
        MessageTag.USER_FEEDBACK,
        content=request.comment or request.feedback.value,
        msg_class=MessageClass.QUERY,
        apiname="vartalaap.feedback",
        extra={
            "additionalinfotags": json.dumps(
                {
                    "feedback": request.feedback.value,
                    "target_message_id": request.message_id,
                    "parent_mlflow_run_id": request.mlflow_run_id,
                    "parent_mlflow_trace_id": request.mlflow_trace_id,
                    "comment": request.comment,
                }
            ),
        },
    )
    log_feedback(
        session_id=request.session_id,
        user_id=request.user_id,
        message_id=request.message_id,
        feedback=request.feedback.value,
        comment=request.comment,
        parent_run_id=request.mlflow_run_id,
        trace_id=request.mlflow_trace_id,
    )
    return FeedbackResponse(
        session_id=request.session_id,
        message_id=request.message_id,
        feedback=request.feedback,
    )


@app.post("/kb/reindex")
def reindex(reset: bool = False) -> dict:
    docs_root: Path = BACKEND_ROOT / "data" / "documents"
    faqs_csv: Path = BACKEND_ROOT / "data" / "faqs.csv"
    return ingest(documents_root=docs_root, faqs_csv=faqs_csv, reset=reset)


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import os
    import uvicorn

    # Render (and many PaaS) inject $PORT; honour it if set.
    port = int(os.environ.get("PORT", settings.api_port))
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=port,
        reload=os.environ.get("UVICORN_RELOAD", "1") == "1",
    )
