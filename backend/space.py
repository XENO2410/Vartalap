"""Hugging Face Space entrypoint.

HF's free **Gradio SDK** just runs `python app.py`, so we shim our real
FastAPI backend behind a tiny Gradio landing card and listen on the
Gradio-standard port 7860. Everything else in the repo is untouched —
this file is only used on the Space.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))


def _seed_if_needed() -> None:
    from app.config import BACKEND_ROOT, get_settings

    settings = get_settings()
    marker = Path(settings.chroma_abs_path) / f"{settings.chroma_collection}.jsonl"
    if marker.exists():
        return
    print(f"[vartalaap] Seeding KB (first boot) → {marker}", flush=True)
    try:
        from app.rag import ingest

        stats = ingest(
            documents_root=BACKEND_ROOT / "data" / "documents",
            faqs_csv=BACKEND_ROOT / "data" / "faqs.csv",
            reset=True,
        )
        print(f"[vartalaap] Ingested: {stats}", flush=True)
    except Exception as exc:  # noqa: BLE001
        print(f"[vartalaap] Seed failed — continuing anyway: {exc!r}", flush=True)


_seed_if_needed()


import gradio as gr  # noqa: E402
from app.main import app as fastapi_app  # noqa: E402


with gr.Blocks(title="वार्तालाप — Backend API", analytics_enabled=False) as demo:
    gr.Markdown(
        """
        # वार्तालाप — Backend API

        This Hugging Face Space hosts the **FastAPI backend** for the
        [Vartalaap](https://github.com/XENO2410/ADI) demo chatbot. The web UI
        is deployed separately on Vercel — this endpoint is what it calls.

        - Interactive OpenAPI: [/docs](/docs)
        - Health check: [/health](/health)
        - Main chat: `POST /chat`
        - Feedback (tags the parent trace): `POST /feedback`

        Every turn is instrumented with an **MLflow trace**: one span per
        pipeline stage (preprocess → guardrails → route → retrieve → LLM →
        reflexion → guardrails), plus rolling business + eval metrics on a
        shared `system::vartalaap` run.

        MLflow runs are stored on this Space's ephemeral filesystem, so
        they reset when the Space sleeps. For a persistent MLflow UI, run
        the repo locally with `docker compose up`.
        """
    )

# Mount Gradio inside our FastAPI at /_ui so the real API paths stay at root.
app = gr.mount_gradio_app(fastapi_app, demo, path="/_ui")


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", "7860"))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
