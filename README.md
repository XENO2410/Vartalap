# वार्तालाप (Vartalaap)

A dummy conversational assistant that **mirrors the ADI (Axis Deep Intelligence)
architecture** end-to-end, purpose-built so you can later attach
**MLflow** and **Kytee** for observability.

- Preprocessing (language detect → translate → spell correct → glossary)
- Input & output **guardrails**
- **Supervisor Agent** with **Reactive** tool selection and **Reflexion** review loop
- Three tools: **RAG Knowledge Base** (FAQ + docs), **Status Retrieval** (mock ESB/DB),
  **Text2SQL** (SQLite mock of bank tables)
- Every stage emits a **schema-conformant event** (matches the message table in the
  architecture doc) via a single `EventEmitter` — that is the seam MLflow/Kytee will
  plug into.

> The bot's public name is **वार्तालाप** ("conversation"). Everything below is
> synthetic sample data — not real Axis Bank content.

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
│   └── types/chat.ts
├── .env.example
└── .gitignore
```

---

## Prerequisites

- **Python 3.11+**
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
