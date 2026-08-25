# वार्तालाप v1.0.0 — first public release

**A dummy conversational assistant that mirrors the ADI (Axis Deep Intelligence)
architecture end-to-end, purpose-built to exercise MLflow-based GenAI
observability on a realistic multi-stage RAG pipeline.**

---

## What's in the box

- Full **preprocessing → guardrails → routing → tool → reflexion → guardrails**
  pipeline, wrapped in MLflow spans so every stage shows up in the trace tree
  with inputs, outputs, latency, model and token counts.
- Three tools — **RAG Knowledge Base** (Chroma-free numpy store), mock
  **Status Retrieval** (Unidesk / Finacle / Tradax patterns), in-memory
  **Text2SQL** over a bank-shaped SQLite.
- **Heuristic eval metrics** per turn — context relevance, faithfulness,
  answer relevance, tone, toxicity, RAG score — logged as trace tags and as
  time-series metrics on the session run.
- **Cost tracking** in USD from OpenRouter list prices.
- **Cross-session roll-up** in a shared `system::vartalaap` run — total turns,
  sessions, tokens, likes/dislikes, running averages.
- **Feedback attached to the trace itself** via `MlflowClient.set_trace_tag`
  — no spawned traces.
- **Next.js 14 frontend** in the Axis pink/maroon theme with dummy login,
  👍 / 👎 feedback, source cards and MLflow chips on every reply.
- **Docker + docker-compose** — one command to bring up backend + frontend +
  MLflow UI with volume-persisted state.

## Quick start (Docker)

```bash
git clone https://github.com/XENO2410/ADI.git
cd ADI
cp .env.example .env       # paste OPENROUTER_API_KEY
docker compose up --build
```

- Frontend: <http://localhost:3000>
- Backend API: <http://localhost:8000/docs>
- MLflow UI: <http://localhost:5000> (experiment `vartalaap`)

## Also available

- **Container images** — pulled from
  `ghcr.io/xeno2410/vartalaap-backend:v1.0.0` and
  `ghcr.io/xeno2410/vartalaap-frontend:v1.0.0`
  (built and pushed automatically by the release workflow).
- **Live demo (optional)** — see [docs/DEPLOY.md](docs/DEPLOY.md) for
  Vercel (frontend) + Fly.io (backend) instructions.

## What's next

- LLM-as-judge eval scores in `backend/app/metrics/evaluators.py`.
- SQLite + object-store MLflow backend for a hosted MLflow UI in the public demo.
- Optional Kytee sink alongside MLflow in `backend/app/observability/emitter.py`.

## Credits

Wikipedia-derived docs under `backend/data/documents/GENERAL/` are
redistributed under CC-BY-SA 4.0 with attribution in-file.

**Full changelog:** [CHANGELOG.md](CHANGELOG.md)
