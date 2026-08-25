---
title: वार्तालाप — Backend
emoji: 🌸
colorFrom: red
colorTo: pink
sdk: gradio
sdk_version: 5.0.0
app_file: space.py
pinned: false
license: mit
short_description: "RAG + agents + MLflow observability backend for वार्तालाप"
suggested_hardware: cpu-basic
tags:
  - fastapi
  - rag
  - mlflow
  - openrouter
  - observability
---

# वार्तालाप — Backend

FastAPI + RAG backend for the [Vartalaap](https://github.com/XENO2410/ADI)
demo assistant. On Hugging Face Spaces this folder runs under the free
**Gradio SDK** — the `space.py` shim launches the full FastAPI stack on
port 7860 and mounts a tiny Gradio landing card at `/_ui`.

## Endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Model + collection status |
| `GET` | `/docs` | Interactive OpenAPI (Swagger) |
| `POST` | `/chat` | Main chat turn (returns `mlflow_trace_id` etc.) |
| `POST` | `/feedback` | 👍 / 👎 / ⬜ — tags the parent trace |
| `POST` | `/kb/reindex` | Rebuild the vector store |

## Environment

Copy `../.env.example` → `.env` and set at least:

```env
OPENROUTER_API_KEY=sk-or-v1-...
LLM_MODEL=openai/gpt-4o-mini
CORS_ORIGINS=http://localhost:3000
```

On **Hugging Face Spaces**, set the same values under
**Settings → Repository secrets** (they're exposed to the container as env vars).

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate            # PowerShell: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m scripts.seed_kb --reset    # builds data/chroma
python -m app.main
```

Server on <http://localhost:8000>.

## Architecture

See the [main README](https://github.com/XENO2410/ADI#readme). Every pipeline
stage is wrapped in an MLflow span; one trace per turn, one run per session,
plus a shared `system::vartalaap` run with cross-session totals.
