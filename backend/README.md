# वार्तालाप — Backend

FastAPI + RAG backend for the [Vartalaap](https://github.com/XENO2410/ADI)
demo assistant.

## What's inside

- **`app/`** — the pipeline (agents, tools, RAG, preprocessing, guardrails,
  metrics, MLflow observability, schemas).
- **`data/documents/`** — synthetic policy corpus + Wikipedia-derived
  background docs.
- **`data/faqs.csv`** — bundled FAQ store.
- **`data/chroma/`** — **pre-computed chunk embeddings** shipped in the
  repo so runtime doesn't need torch. See
  [`data/chroma/README.md`](data/chroma/README.md).
- **`scripts/seed_kb.py`** — rebuilds `data/chroma/*` when the corpus
  changes. Requires `sentence-transformers` (optional dev dep) or an HF
  Inference API token.

## Endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Model + collection status |
| `GET` | `/docs` | Interactive OpenAPI (Swagger) |
| `POST` | `/chat` | Main chat turn (returns `mlflow_trace_id` etc.) |
| `POST` | `/feedback` | 👍 / 👎 / ⬜ — tags the parent trace |
| `POST` | `/kb/reindex` | Rebuild the vector store from source docs |

## Environment

Copy `../.env.example` → `../.env` and set at least:

```env
OPENROUTER_API_KEY=sk-or-v1-...
HF_INFERENCE_TOKEN=hf_...           # free tier — https://huggingface.co/settings/tokens
LLM_MODEL=openai/gpt-4o-mini
CORS_ORIGINS=http://localhost:3000
```

`HF_INFERENCE_TOKEN` is used only for the **one query embedding per turn**.
Chunk embeddings are shipped pre-computed in `data/chroma/`.

## Run locally (slim, no torch)

```bash
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1        # PowerShell (Linux/macOS: source .venv/bin/activate)
pip install -r requirements.txt
python -m app.main
```

Server on <http://localhost:8000> · Swagger on <http://localhost:8000/docs>.

## Run locally with the fast embeddings path (optional)

If you want zero-latency embeddings (no HF API roundtrip), install the
optional dev deps:

```bash
pip install sentence-transformers==3.1.1
$env:EMBEDDING_BACKEND = "sentence_transformers"
python -m app.main
```

## Regenerating the KB

Whenever you change files under `data/documents/` or `data/faqs.csv`:

```bash
pip install sentence-transformers==3.1.1
python -m scripts.seed_kb --reset
```

Commit the resulting `data/chroma/vartalaap_kb.jsonl` + `.npy`.

## Public deployment

Backend deploys to **Render Free** (512 MB, no CC required). See
[../docs/DEPLOY.md](../docs/DEPLOY.md).
