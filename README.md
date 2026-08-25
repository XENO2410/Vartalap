# वार्तालाप (Vartalaap)

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
![Backend: FastAPI](https://img.shields.io/badge/backend-FastAPI-009485)
![Frontend: Next.js 14](https://img.shields.io/badge/frontend-Next.js%2014-black)
![Observability: MLflow](https://img.shields.io/badge/observability-MLflow-0194E2)

A dummy conversational assistant that **mirrors the ADI (Axis Deep Intelligence)
architecture** end-to-end — purpose-built to exercise
**MLflow-based GenAI observability** (traces, per-turn eval metrics, cost tracking,
cross-session roll-ups, feedback attached to traces) on a realistic multi-stage
RAG pipeline.

- Preprocessing (language detect → translate → spell correct → glossary)
- Input & output **guardrails**
- **Supervisor Agent** with **Reactive** tool selection and **Reflexion** review loop
- Three tools: **RAG Knowledge Base** (FAQ + docs), **Status Retrieval** (mock ESB/DB),
  **Text2SQL** (SQLite mock of bank tables)
- Every stage is wrapped in an **MLflow span** and emits a **schema-conformant
  event** (matches the message table in the architecture doc)
- Heuristic **eval metrics** per turn: context relevance, faithfulness, answer
  relevance, tone, toxicity, composite RAG score
- **Per-session run** (one MLflow run) + a shared **`system::vartalaap` run**
  with cross-session totals + rolling averages
- **👍 / 👎 / None feedback** attached as tags on the **existing trace** — no
  spawned traces

> The bot's public name is **वार्तालाप** ("conversation"). Everything below is
> synthetic sample data — not real Axis Bank content.

---

## Screenshots

| Landing / chat | MLflow trace tree | Per-turn eval metrics |
| --- | --- | --- |
| ![landing](docs/screenshots/landing.png) | ![trace tree](docs/screenshots/mlflow-traces.png) | ![metrics](docs/screenshots/mlflow-metrics.png) |

(Place your PNGs under [docs/screenshots](docs/screenshots/) using the file names
above — GitHub will render them here automatically.)

---

## Quick start — with Docker (one command)

Prerequisites: **Docker Desktop 4.x** (or any Docker Engine ≥ 20.10 + Docker Compose v2).

```powershell
git clone https://github.com/XENO2410/ADI.git
cd ADI
Copy-Item .env.example .env
# Open .env and paste your OpenRouter API key:
#   OPENROUTER_API_KEY=sk-or-v1-...
docker compose up --build
```

That builds and runs three containers on the following ports:

| URL | Service |
| --- | --- |
| http://localhost:3000 | **वार्तालाप** frontend (Next.js) |
| http://localhost:8000/docs | Backend Swagger UI (FastAPI) |
| http://localhost:5000 | **MLflow UI** with the `vartalaap` experiment |

The backend seeds the Chroma index automatically on first boot (about 60 s while
`sentence-transformers` downloads the embedding model). Subsequent starts are
instant. Volumes persist the KB (`chroma`), the MLflow store (`mlruns`), the
event JSONL log (`logs`) and the HuggingFace cache (`hf-cache`).

Stop everything with `docker compose down`. Wipe state with
`docker compose down -v`.

> **Note:** the OpenRouter key you set via `.env` is loaded into the backend
> container's environment — it is not baked into the image. If no key is set,
> the LLM falls through to a deterministic offline stub and every stage still
> runs so you can exercise the pipeline.

---

## Quick start — local development (no Docker)

If you'd rather run the components directly, see the "Local dev" section below.

---

## Repository layout

```
ADI/
├── backend/                 # FastAPI + RAG + agents
│   ├── app/
│   │   ├── main.py                    # FastAPI entrypoint
│   │   ├── config.py                  # env-driven settings
│   │   ├── schemas/message.py         # schema table + message tags
│   │   ├── observability/emitter.py   # <-- MLflow / Kytee seam
│   │   ├── llm/openai_client.py       # OpenRouter (OpenAI-compatible) client
│   │   ├── rag/                       # store, embedder, reranker, ingest, retriever
│   │   ├── preprocessing/             # glossary, translation, spell
│   │   ├── routing/                   # bubble + hashtag + intent classifier
│   │   ├── guardrails/                # input & output filters
│   │   ├── tools/                     # kb_function, status, text2sql
│   │   └── agents/                    # supervisor, reactive, reflexion
│   ├── data/
│   │   ├── documents/                 # synthetic HR/IT/LAW/AHA/CR + 2 Wikipedia-derived docs
│   │   └── faqs.csv                   # sample FAQ store
│   ├── scripts/seed_kb.py             # builds the Chroma index
│   └── requirements.txt
├── frontend/                # Next.js 14 + Tailwind, Axis-styled UI
│   ├── app/                           # App router entry
│   ├── components/                    # Header, BubbleTabs, ChatWindow, SourceCard, ...
│   ├── lib/api.ts                     # backend client
│   ├── types/chat.ts
│   └── Dockerfile
├── docs/screenshots/        # drop your PNGs here
├── .env.example
├── docker-compose.yml
├── LICENSE                  # MIT
└── .gitignore
```

---

## Local dev — prerequisites

- **Python 3.12+** (3.11 works too)
- **Node.js 20+ / npm** (or pnpm / yarn)
- An **OpenRouter API key** (optional — a deterministic offline stub is used
  when no key is present, so every stage still runs)

The first backend run will download the embedding model
(`sentence-transformers/all-MiniLM-L6-v2`, ~90 MB) and — if enabled — the
reranker (`BAAI/bge-reranker-base`, ~280 MB) into your HuggingFace cache.

---

## 1. Configure secrets

```powershell
Copy-Item .env.example .env
```

Then open `.env` and set at least:

```
OPENROUTER_API_KEY=sk-or-v1-...   # paste yours; DO NOT commit this file
LLM_MODEL=openai/gpt-4o-mini      # cheap default; change as you like
```

`.env` is gitignored. If a key was ever committed by accident, rotate it on
OpenRouter immediately.

---

## 2. Backend — install, seed, run

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Build the Chroma index from bundled sample data (once).
python -m scripts.seed_kb --reset

# Run FastAPI.
python -m app.main
# or: uvicorn app.main:app --reload --port 8000
```

Endpoints:

| Method | Path              | Purpose                                      |
| ------ | ----------------- | -------------------------------------------- |
| GET    | `/`               | Landing JSON                                 |
| GET    | `/health`         | LLM key present? collection size? models?    |
| POST   | `/chat`           | Main chat turn                               |
| POST   | `/kb/reindex`     | Rebuild the KB index (`?reset=true` to drop) |
| GET    | `/docs`           | OpenAPI Swagger                              |

Every `/chat` response includes a full `events[]` array — one row per stage,
schema-conformant, ready to be teed into MLflow / Kytee.

Event log is also written to `backend/logs/events-YYYY-MM-DD.jsonl`.

---

## 3. Frontend — install, run

```powershell
cd frontend
Copy-Item .env.example .env.local   # or set NEXT_PUBLIC_API_BASE_URL another way
npm install
npm run dev
```

Open http://localhost:3000

The UI mirrors the ADI screens: bubble tabs (`All`, `HR`, `Download`, `Status`,
`Aha`, `Law`, `Conversational BI`, `Axis Phone`, `Financial Advisor`,
`IT Helpdesk`, `CR`), landing hero **"वार्तालाप & Me — That's How I Win at Work"**,
chat view with **Relevancy / Type** source cards, suggestion chips, "Show more
sources", and thumbs feedback.

---

## 4. How the runtime maps to the architecture doc

```
UI → /chat → Supervisor Agent
     ├─ emit USER_QUERY
     ├─ preprocessing
     │    ├─ emit LLM_LANG_REQUEST / LLM_LANG_RESPONSE   (translate → English)
     │    ├─ spell correction (deterministic, rapidfuzz)
     │    ├─ glossary expansion (KYC, AML, ESB, ...)
     │    └─ emit LLM_REFINE_QUERY_RESPONSE
     ├─ input guardrails
     │    └─ emit GUARDRAILS_QUERY_FILTER_REQUEST / _RESPONSE
     ├─ router (bubble / #hashtag / keywords) → Reactive Agent
     │    ├─ #status or Status bubble → Status API tool  (mock Unidesk / PrimeCTL / …)
     │    │                            or Status DB tool  (mock Finacle / Tradax / …)
     │    ├─ analytical intent + bank keywords → Text2SQL tool (SQLite in-memory)
     │    └─ else → Knowledge Base tool (FAQ-first, then Chroma retrieval + rerank)
     ├─ tool run
     │    ├─ KB: emit KNOWLEDGE_BASE_REQUEST, per-doc KNOWLEDGE_BASE_RESPONSE_DOC,
     │    │     PROMPT_BUILDER_QA_RESPONSE, LLM_QA_REQUEST / LLM_QA_RESPONSE,
     │    │     KNOWLEDGE_BASE_RESPONSE
     │    ├─ Status: emit KNOWLEDGE_BASE_REQUEST / _RESPONSE_DOC / _RESPONSE
     │    └─ Text2SQL: emit LLM_QA_REQUEST / _RESPONSE + fills
     │                additionalinfotext2sqlquery / additionalinfoformattedsqlquery /
     │                additionalinfosqlquery
     ├─ Reflexion Agent reviews; retries with a refined query up to
     │    REFLEXION_MAX_ITERATIONS (default 2)
     ├─ output guardrails (PII scrub)
     └─ emit CHAT_RESPONSE → back to UI
```

Every `emit(...)` populates the schema fields from the architecture doc
(`class`, `additionalinfouserquery`, `additionalinfotags`, `processedquery`,
`historyrelevancyscore`, `identifiersessionid`, `originallanguage`, `apiname`,
`additionalinfotranslatedprompttokeninfo`, `content`, `createddate`,
`identifieruserid`, `additionalinfotext2sqlquery`, `additionalinfomlglossary`,
`messagetype`, `islanguagetranslation`, `additionalinfosources`,
`additionalinfosqlquery`, `additionalinfotranslatedpromptclass`,
`additionalinfotokeninfo`, `identifiermessageid`, `isspellcorrection`,
`msgcontent`, `msgcommand`, `azurekbresponsedocumentattributes`, `dt`, …).

---

## 5. Adding MLflow / Kytee

You only need to touch one file:

```python
# backend/app/observability/emitter.py
def _sink(self, envelope: MessageEnvelope) -> None:
    payload = envelope.model_dump(by_alias=True, exclude_none=False)
    # existing JSONL sink stays for local dev …
    # add:
    mlflow.log_dict(payload, f"events/{envelope.identifiermessageid}.json")
    kytee_client.emit(payload)
```

No call-site changes anywhere else.

### MLflow is now wired in

MLflow logging is **on by default** (`MLFLOW_ENABLED=true`, tracking URI
`file://backend/mlruns/`). Every `/chat` turn opens a run named
`turn::<sess_id>` and logs:

- **Tags** — `session_id`, `user_id`, `bubble`, `tool_used`, `use_case`,
  `message_id`, plus one `stage.NN.<TAG>` tag per emitted event so you can
  see the pipeline order.
- **Metrics** — `reflexion_iterations`, `num_events`, `num_sources`,
  `prompt_tokens_total`, `completion_tokens_total`, `total_tokens`.
- **Artifacts** — `events.json` (full schema-conformant trail),
  `sources.json`, `answer.md`.

Feedback events (`POST /feedback`) either re-open the parent turn's run (if
`mlflow_run_id` is passed back) and add `feedback_score` / a `feedback`
tag, or open a linked run tagged with the target `message_id`.

Open the MLflow UI in a separate terminal:

```powershell
cd backend
mlflow ui --backend-store-uri mlruns
# → http://localhost:5000
```

Disable with `MLFLOW_ENABLED=false` in `.env`.

### Feedback API

```
POST /feedback
{
  "session_id":   "sess_...",
  "message_id":   "...",
  "user_id":      "u_abc123",
  "feedback":     "up" | "down" | "none",
  "mlflow_run_id": "..."     // optional; frontend forwards from ChatResponse
}
```

The frontend exposes 👍 / 👎 / ⬜ None buttons on every assistant reply and
tracks the active choice per message.

### Dummy login

On first load the frontend shows a modal asking for a display name. It
generates a stable `user_id` (e.g. `u_9a3f2b1c…`) stored in
`localStorage`, and attaches it to every `/chat` and `/feedback` call, so
each MLflow run and every schema event carries `identifieruserid`. Use the
**Sign out** button in the header to reset.

---

## 6. Try it

- `hi tell me new hr policies` (bubble `HR`)
- `where can I download the FEMA declaration form?` (bubble `Download`)
- `#status SR-991002 credit card application`
- `how many customers opened SAVINGS accounts?` (bubble `Conversational BI`)
- `explain KYC` (bubble `All`, uses Wikipedia-derived KYC background doc)
- `what is RAG?` (bubble `IT Helpdesk`, uses Wikipedia-derived RAG background doc)

---

## Notes and known limits

- The status tool returns deterministic pseudo-data — no real ESB / core-banking is called.
- Text2SQL runs against an in-memory SQLite with a handful of rows; the schema is
  documented inline in `backend/app/tools/text2sql.py`.
- Without an OpenRouter key, every LLM call falls through to a deterministic
  stub — the pipeline stays runnable end-to-end for observability testing.
- The two Wikipedia-derived files under
  `backend/data/documents/GENERAL` are redistributed under CC-BY-SA 4.0
  (attribution included in each file).
- Eval scores are heuristics computed inline — retrieval-score-based context
  relevance, citation-based faithfulness, keyword-overlap answer relevance,
  lexicon-based tone / toxicity. Good enough to exercise the dashboards; drop
  an LLM-as-judge in `backend/app/metrics/evaluators.py` when you need real numbers.
- Cost estimates use the OpenRouter list prices in
  `backend/app/metrics/costs.py` — update the table when you switch models.

---

## Security

- Never commit `.env`. `.gitignore` already excludes it.
- If you accidentally paste your OpenRouter key in a public log, rotate it on
  [openrouter.ai/keys](https://openrouter.ai/keys) — this repo does not persist
  keys anywhere and reads them only from environment variables at boot.
- Guardrails (input + output) are heuristic and meant for a demo. Do not deploy
  this as a customer-facing assistant without a proper safety layer.

---

## Contributing

PRs welcome — issues even more so. Please keep the schema in
`backend/app/schemas/message.py` in sync with any new pipeline stages you add,
and prefer wrapping new stages in `emitter.span(...)` so they show up in the
MLflow trace tree.

---

## License

[MIT](LICENSE) © 2026 XENO2410 and contributors.

