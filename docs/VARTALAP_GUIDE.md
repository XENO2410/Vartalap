# वार्तालाप (Vartalap) — Project Guide & MLflow Integration Reference

> **Audience:** developers onboarding onto this repository, and AI assistants /
> LLMs that need a complete, fact-dense description of the project to answer
> questions or make changes.
>
> **Repository:** `XENO2410/ADI` · **License:** MIT · **Latest release:** v1.0.0
>
> Every statement in this guide is grounded in the current code. When code and
> guide disagree, trust the code and update this file.

---

## 1. What Vartalap is (TL;DR)

**वार्तालाप** ("conversation" in Hindi, transliterated *Vartalaap*) is a
**dummy conversational assistant** that mirrors the **ADI (Axis Deep
Intelligence) architecture** end-to-end. ADI is an internal, employee-facing
banking assistant architecture; Vartalap is a synthetic, non-customer-facing
clone of that architecture whose real purpose is to exercise
**MLflow-based GenAI observability** on a realistic multi-stage RAG pipeline.

Concretely, Vartalap demonstrates:

| Capability | How |
| --- | --- |
| Multi-stage RAG pipeline | preprocess → guardrails → route → tool → reflexion → guardrails |
| Agent orchestration | Supervisor + Reactive tool selection + Reflexion review loop |
| MLflow tracing | one run per session, one trace per turn, one span per stage |
| GenAI conventions | `mlflow.chat.messages`, `mlflow.chat.tokenUsage`, `mlflow.chat.model` |
| Per-turn eval metrics | 7 heuristic quality metrics per turn |
| Cost tracking | per-model USD/1M-token pricing → `cost_usd` metrics |
| Cross-session roll-ups | shared `system::vartalaap` run |
| Feedback on traces | 👍/👎/⬜ tags attached to the existing trace (no new trace) |

**Tech stack:** FastAPI (Python 3.12) backend · Next.js 14 + Tailwind frontend ·
MLflow ≥ 2.17 observability · Docker Compose for local dev · Render + Vercel +
Neon Postgres for the free public deployment.

**All content is synthetic** — there is no real Axis Bank data anywhere in the
repo. The knowledge base is synthetic HR/IT/Law/AHA/CR policy documents plus
two Wikipedia-derived background docs (KYC, RAG, CC-BY-SA 4.0).

---

## 2. Repository map

```
ADI/                                  (repo root; python 3.12 per .python-version)
├── backend/                          FastAPI backend (Python)
│   ├── app/
│   │   ├── main.py                   FastAPI entrypoint: /health, /chat, /feedback, /kb/reindex
│   │   ├── config.py                 env-driven settings (pydantic-settings)
│   │   ├── schemas/message.py        ADI message schema (MessageEnvelope) + API models
│   │   ├── observability/
│   │   │   ├── emitter.py            EventEmitter — central event/span seam (JSONL + MLflow tee)
│   │   │   └── mlflow_sink.py        MLflowSink — all MLflow tracing/run/metric logic
│   │   ├── llm/openai_client.py      OpenRouter (OpenAI-compatible) client + offline stub
│   │   ├── rag/                      store.py, embedder.py, reranker.py, ingest.py, retriever.py
│   │   ├── preprocessing/            translation.py, spell.py, glossary.py
│   │   ├── routing/router.py         keyword/hashtag/bubble router
│   │   ├── guardrails/filters.py     input & output guardrails
│   │   ├── tools/                    kb_function.py, status.py, text2sql.py
│   │   ├── agents/                   supervisor.py, reactive.py, reflexion.py
│   │   └── metrics/                  evaluators.py (heuristic eval), costs.py (USD/1M tokens)
│   ├── data/
│   │   ├── documents/                synthetic policy corpus (HR, LAW, IT_HELPDESK, AHA, CR, ...)
│   │   ├── faqs.csv                  bundled FAQ store
│   │   └── chroma/                   PRE-COMPUTED embeddings (vartalaap_kb.jsonl + .npy)
│   ├── scripts/seed_kb.py            rebuilds data/chroma from documents + faqs
│   ├── logs/events-YYYY-MM-DD.jsonl  per-day JSONL event log (runtime output)
│   ├── mlruns/                       local MLflow store (runtime output, gitignored)
│   ├── requirements.txt              runtime deps (mlflow>=2.17,<4.0)
│   └── Dockerfile
├── frontend/                         Next.js 14 (TypeScript, Tailwind, App Router)
│   ├── app/                          layout.tsx, page.tsx, globals.css
│   ├── components/                   ChatWindow, MessageBubble, SourceCard, QueryInput,
│   │                                 BubbleTabs, SuggestionChips, LoginGate, Header, ...
│   ├── lib/api.ts                    backend client (sendChat / sendFeedback / fetchHealth)
│   └── types/chat.ts                 shared request/response types
├── mlflow_server/                    hosted MLflow tracking server (Render + Neon Postgres)
│   ├── README.md
│   └── requirements.txt              mlflow + psycopg2-binary + gunicorn
├── jev_judge_eval/                   JEV vs LLM-as-judge evaluation harness (independent)
├── docs/                             DEPLOY.md, RELEASE_NOTES_v1.0.0.md, screenshots/
├── .github/workflows/                ci.yml (compile/import + frontend build), release.yml (GHCR images)
├── docker-compose.yml                3 services: backend, frontend, mlflow-ui
├── .env.example                      environment template
├── CHANGELOG.md
└── LICENSE                            MIT
```

---

## 3. The chat pipeline (one `/chat` turn)

```
UI (Next.js) ──POST /chat──▶ Supervisor.handle()                     [backend/app/agents/supervisor.py]
   │
   ├─ 0. EventEmitter created per turn; emitter.start_turn() opens the MLflow trace
   │      emit USER_QUERY
   ├─ 1. preprocess.translate      (LLM span)  language detect → translate to English
   │      emit LLM_LANG_REQUEST / LLM_LANG_RESPONSE  (mlflow.chat.* set if LLM was used)
   ├─ 2. preprocess.refine         (CHAIN span) rapidfuzz spell correction + glossary expansion
   │      emit LLM_REFINE_QUERY_RESPONSE
   ├─ 3. guardrails.input          (CHAIN span) heuristic input filter
   │      emit GUARDRAILS_QUERY_FILTER_REQUEST / _RESPONSE
   │      └─ blocked → answer refusal, use_case=guardrailed, tool=guardrails, stop
   ├─ 4. route                     (AGENT span)  router.classify() → reactive.select_tool()
   │      emit PROMPT_BUILDER_LANG_REQUEST / _RESPONSE
   │      routes: rag | status_api | status_db | text2sql
   ├─ 5. iteration.NN × (up to REFLEXION_MAX_ITERATIONS, default 2)
   │      ├─ tool.kb      (RETRIEVER span) → FAQ-first; else Chroma retrieve → rerank → LLM synthesize
   │      │     emit KNOWLEDGE_BASE_REQUEST, KNOWLEDGE_BASE_RESPONSE_DOC (per doc),
   │      │           PROMPT_BUILDER_QA_RESPONSE, LLM_QA_REQUEST, LLM_QA_RESPONSE,
   │      │           KNOWLEDGE_BASE_RESPONSE
   │      ├─ tool.status_api / tool.status_db   mock ESB / core-banking status payloads
   │      └─ tool.text2sql      LLM generates SQL over in-memory SQLite mock bank tables
   │      └─ reflexion.review  (LLM span) verdict {valid, score, reason, refined_query}
   │           break when valid || score ≥ 0.75 || last iteration
   ├─ 6. guardrails.output        (CHAIN span) PII scrub
   └─ 7. emitter.finalize()       closes trace; logs per-turn metrics, trace tags,
                                   system roll-up metrics; returns ChatResponse
                                   (includes answer, sources, events[], mlflow_run_id, mlflow_trace_id)
```

Each stage is wrapped in `emitter.span(name, kind=...)` (span kinds used:
`CHAIN`, `LLM`, `AGENT`, `RETRIEVER`, `TOOL`) and each stage emits one or
more schema-conformant `MessageEnvelope` events.

---

## 4. Backend deep dive (module by module)

### 4.1 `app/config.py` — `Settings`

pydantic-settings `BaseSettings` reading env (and `../.env` / `.env`).
All values have aliases (e.g. `OPENROUTER_API_KEY`). Cached via
`get_settings()` (`@lru_cache`). Key groups:

- **LLM:** `OPENROUTER_API_KEY`, `OPENROUTER_BASE_URL` (default
  `https://openrouter.ai/api/v1`), `LLM_MODEL` (`openai/gpt-4o-mini`),
  `LLM_FALLBACK_MODEL` (`google/gemini-flash-1.5`), `LLM_TEMPERATURE=0.2`,
  `LLM_MAX_TOKENS=800`.
- **Embeddings:** `EMBEDDING_BACKEND=auto` (resolves `sentence_transformers`
  if importable → else `hf_inference` if `HF_INFERENCE_TOKEN` set → else
  `hash`), `EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2`.
- **Retrieval:** `RETRIEVER_TOP_K_CANDIDATES=50`, `RETRIEVER_TOP_K_FINAL=5`,
  `FAQ_HIGH_CONFIDENCE=0.85`, `FAQ_MEDIUM_CONFIDENCE=0.60`.
- **Reflexion:** `REFLEXION_ENABLED=true`, `REFLEXION_MAX_ITERATIONS=2`.
- **MLflow:** `MLFLOW_ENABLED=true`, `MLFLOW_TRACKING_URI=./mlruns`,
  `MLFLOW_EXPERIMENT=vartalaap`.
- Property `mlflow_tracking_uri_resolved`: passes through `http(s)://`,
  `file:`, `sqlite:`, `databricks:` prefixes unchanged; any other path is
  resolved relative to `backend/` and returned as an absolute `file://` URI.

### 4.2 `app/schemas/message.py` — the ADI message schema

The observability contract. `MessageEnvelope` contains **every field from the
ADI architecture doc §3/§12** as nullable strings (identity fields,
`content`, `msgcontent`, `msgcommand`, `processedquery`, `originallanguage`,
`islanguagetranslation`, `isspellcorrection`,
`additionalinfotokeninfo`, `additionalinfosources`,
`additionalinfotext2sqlquery`, `additionalinfoformattedsqlquery`,
`additionalinfosqlquery`, `historyrelevancyscore`, …). `extra="allow"` means
any additional field can be attached.

Enums:

- `MessageTag` — the `messagetype` column:
  `USER_QUERY`, `LLM_LANG_REQUEST`, `LLM_LANG_RESPONSE`,
  `GUARDRAILS_QUERY_FILTER_REQUEST`, `GUARDRAILS_QUERY_FILTER_RESPONSE`,
  `LLM_REFINE_QUERY_RESPONSE`, `PROMPT_BUILDER_REFINE_QUERY_RESPONSE`,
  `PROMPT_BUILDER_LANG_REQUEST`, `PROMPT_BUILDER_LANG_RESPONSE`,
  `LLM_QA_REQUEST`, `LLM_QA_RESPONSE`, `PROMPT_BUILDER_QA_RESPONSE`,
  `KNOWLEDGE_BASE_REQUEST`, `KNOWLEDGE_BASE_RESPONSE`,
  `KNOWLEDGE_BASE_RESPONSE_DOC`, `CHAT_RESPONSE`, `USER_FEEDBACK`.
- `MessageClass` — `query` | `response` | `system`.
- `UseCase` — `generic_rag`, `status_api`, `status_db`, `text2sql`,
  `guardrailed`, `out_of_scope`.

API models: `ChatRequest` (query, session_id?, user_id?, bubble?, history[]),
`ChatResponse` (answer, sources[], suggestions[], use_case, tool_used,
reflexion_iterations, events[], **mlflow_run_id?, mlflow_trace_id?**),
`FeedbackRequest/Response` (session_id, message_id, feedback up|down|none,
optional comment + mlflow ids).

### 4.3 `app/llm/openai_client.py` — `LLMClient`

Thin `openai` SDK wrapper pointed at OpenRouter, with `tenacity` retry
(3 attempts, exponential backoff). If the primary model call fails, it
retries once with `LLM_FALLBACK_MODEL`. If no API key is configured, every
call returns a **deterministic offline stub** (`_stub_response`) so the whole
pipeline stays runnable for observability testing.

### 4.4 Preprocessing

- `translation.py` — `Translator.to_english()`: langdetect-based detection;
  English passes through; otherwise LLM translation with token info.
- `spell.py` — `spell_correct()`: deterministic rapidfuzz against the KB
  vocabulary (threshold 88).
- `glossary.py` — `GlossaryExpander.apply()`: expands known acronyms
  (KYC, AML, ESB, …) into the query.

### 4.5 Routing (`routing/router.py`, `agents/reactive.py`)

Deterministic keyword tables:

- `#status` hashtag or `Status` bubble → `status_api` (keywords: sr, ticket,
  unidesk, kaleidoscope, eforms, sdl, …) or `status_db` (keywords: balance,
  finacle, tradax, trracs, gps, …).
- Aggregative keywords (`how many`, `count of`, `sum of`, `average`, `top 10`,
  `trend`, …) **plus** bank nouns (account/loan/customer/transaction) →
  `text2sql`.
- Everything else → `kb` (RAG).

`select_tool()` maps the route to a `ToolSelection {tool_name, use_case, reason}`.

### 4.6 Tools

- **`kb_function.py` — `KnowledgeBaseTool`** (the RAG path):
  1. `retriever.retrieve()` — FAQ-first: best-FAQ confidence ≥ 0.85 answers
     directly (model `faq-direct`, zero tokens); otherwise Chroma retrieval
     (top-50 candidates → optional BGE rerank → top-5 final chunks).
  2. Builds context block with `[S1]..[S5]` citations + optional chat history.
  3. LLM synthesizes the answer; each retrieved doc emits a
     `KNOWLEDGE_BASE_RESPONSE_DOC` event.
- **`status.py` — `StatusTool`** — deterministic mock payloads for ticket /
  transaction status lookups (no real ESB or core-banking calls).
- **`text2sql.py` — `Text2SQLTool`** — LLM generates SQL against an
  **in-memory SQLite** DB with a handful of mock bank tables; runs it, formats
  rows, returns the answer.

### 4.7 Reflexion (`agents/reflexion.py`)

`ReflexionReviewer.review()` calls the LLM to judge the candidate answer;
`_parse_verdict` extracts `{valid, score, reason, refined_query}` from the
LLM text. The supervisor retries with the refined query until
`valid || score >= 0.75 || iterations >= max`.

### 4.8 Metrics

- `evaluators.py` — `evaluate()` returns `QualityMetrics` with 7 heuristic
  0–1 scores computed inline (no ground truth needed):
  `context_relevance` (mean of top-5 retrieval scores), `faithfulness`
  (citation-count or refusal heuristics), `answer_relevance` (keyword
  overlap), `chat_history_relevance`, `tone_appropriateness` (politeness
  lexicon), `toxicity` (toxic-word lexicon), and composite `rag_score`
  (weighted 0.25/0.30/0.25/0.20, multiplied by `1 - toxicity`).
- `costs.py` — `usd_cost(model, prompt_tokens, completion_tokens)` using a
  hardcoded USD-per-1M-token table for common OpenRouter models.

---

## 5. MLflow integration — the complete reference

### 5.1 Mental model

```
1 session  ───▶ 1 MLflow run      (run name: session::<first-14-chars>)
1 chat turn ───▶ 1 MLflow trace   (root span: turn.NN :: <query[:60]>)
1 pipeline stage ▶ 1 span         (nested, with inputs/outputs/attributes/latency)
1 emitted event ▶ 1 span.add_event() + 1 JSONL line
1 feedback     ▶ trace tags on the existing trace (no new trace)
all sessions  ─▶ shared system::vartalaap run (cross-session aggregates)
```

Enforced in two files only:

- `backend/app/observability/emitter.py` — `EventEmitter`: session-scoped;
  wraps `MLflowSink`; exposes `start_turn`, `span`, `set_span_*`,
  `set_span_chat`, `emit`, `finalize`.
- `backend/app/observability/mlflow_sink.py` — `MLflowSink` + module-level
  `log_feedback()`: all MLflow API calls.

All other modules never touch `mlflow` directly — they only call
`emitter.span(...)` and `emitter.emit(...)`.

### 5.2 Configuration

| Env var | Default | Meaning |
| --- | --- | --- |
| `MLFLOW_ENABLED` | `true` | master switch; sink becomes a safe no-op when false |
| `MLFLOW_TRACKING_URI` | `./mlruns` | local path → absolute `file://` URI; `http(s)://` passed through |
| `MLFLOW_EXPERIMENT` | `vartalaap` | experiment name (auto-created by `mlflow.set_experiment`) |

On init (`_try_init`): `mlflow.set_tracking_uri(resolved)`,
`mlflow.set_experiment(...)`, system-metrics logging enabled
(`MLFLOW_ENABLE_SYSTEM_METRICS_LOGGING=true` +
`mlflow.enable_system_metrics_logging()`, needs psutil).

**Failure policy:** every MLflow call is wrapped in try/except. If `mlflow`
is not installed or the tracking URI is unreachable, tracing silently
degrades — `/chat` always succeeds. The same applies to the offline-stub LLM:
you can exercise the entire observability surface without any API keys.

### 5.3 Session runs

`_get_or_create_session_run()` keeps an in-memory dict
`_SESSION_RUNS: {session_id: run_id}`. First turn creates the run with tags
`session_id`, `user_id`, `bubble`, `app=vartalaap`, `kind=session` and param
`first_seen`; later turns reopen the same run. In-memory cache means the
mapping resets on process restart (fresh runs per boot) — acceptable for a
demo; see §5.9 for caveats.

### 5.4 Traces, spans, and events

- `start_turn(query)` reopens the session run, then opens the root span
  (`turn.NN :: <query[:60]>`, span type `CHAIN`) and records
  `trace_id` (= `request_id` on the span). Turn counter per session:
  `_SESSION_TURNS`.
- `span(name, kind, inputs, attributes)` opens a child span
  (`mlflow.start_span`), stacks it in `_span_stack`, and yields it;
  `set_current_outputs/attributes` target the top of the stack.
- `log_event(envelope)` accumulates tokens/models and calls
  `span.add_event(name=messagetype, attributes={message_id, class, api,
  content_preview[:280]})`.

### 5.5 MLflow GenAI conventions (the important part)

MLflow ≥ 2.17 renders the GenAI dashboard panels ("Requests", "Latency",
"Token Usage", "Tokens per Trace") **only when spans carry the
`mlflow.chat.*` attributes**. `set_current_chat()` sets them on LLM spans:

| Attribute | Value |
| --- | --- |
| `mlflow.chat.messages` | list of `{role, content}` (system/user/assistant) |
| `mlflow.chat.tokenUsage` | `{input_tokens, output_tokens, total_tokens}` |
| `mlflow.chat.model` | model id string |

Where they are set in code (any span that actually calls the LLM):

- `supervisor.py` — `preprocess.translate` span when translation invoked the LLM.
- `agents/reflexion.py` — `reflexion.review` span.
- `tools/kb_function.py` — KB LLM synthesis span.
- `tools/text2sql.py` — SQL generation span.
- `mlflow_sink.finalize()` — root span gets `mlflow.chat.tokenUsage` +
  `mlflow.chat.model` with per-turn totals (this is what feeds the trace
  table and dashboards for every turn, including FAQ-direct turns).

### 5.6 `finalize()` — what is logged when a turn ends

On the **root span** (attributes + outputs):

- attributes: `message_id`, `tool_used`, `use_case`, `reflexion_iterations`,
  `num_events`, `num_sources`, `prompt_tokens`, `completion_tokens`,
  `total_tokens`, `cost_usd`, `model_primary`, `models_used`,
  plus `eval.*` (7 metrics) when quality metrics were computed.
- GenAI attributes: `mlflow.chat.tokenUsage`, `mlflow.chat.model`.
- outputs: `{answer, sources:[{title, type, relevancy, score}], message_id}`.

On the **session run** (step-indexed time series, `step = turn_index`):

- metrics: `turn.prompt_tokens`, `turn.completion_tokens`,
  `turn.total_tokens`, `turn.cost_usd`, `turn.num_sources`,
  `turn.num_events`, `turn.reflexion_iterations`, and `eval.*` metrics.
- tags: `turn.NN.tool`, `turn.NN.use_case`, `turn.NN.model`.

On the **trace row** (`MlflowClient.set_trace_tag`, visible in the trace
table's Tags column): `tool`, `use_case`, `user_id`, `bubble`, `model`,
`total_tokens`, `cost_usd`, `eval.rag_score`, `eval.context_relevance`,
`eval.faithfulness`, `eval.answer_relevance`, `eval.toxicity`.

### 5.7 The shared `system::vartalaap` run

`_get_or_create_system_run()` creates one run tagged `kind=system` and
`_log_system_aggregates()` appends step-indexed metrics on every turn
(`step = total turns`):

- Totals: `system.total_turns`, `system.total_sessions`,
  `system.unique_users`, `system.total_prompt_tokens`,
  `system.total_completion_tokens`, `system.total_tokens`,
  `system.total_cost_usd`, `system.likes`, `system.dislikes`,
  `system.no_feedback`, `system.guardrailed`, `system.reflexion_retries`.
- Rolling averages: `system.avg_cost_per_turn_usd`,
  `system.avg_tokens_per_turn`, `system.avg_sources_per_turn`,
  `system.eval.avg_context_relevance`, `system.eval.avg_faithfulness`,
  `system.eval.avg_answer_relevance`, `system.eval.avg_history_relevance`,
  `system.eval.avg_tone`, `system.eval.avg_toxicity`,
  `system.eval.avg_rag_score`.

### 5.8 Feedback (`POST /feedback`)

`log_feedback()` (called from `main.py`):

1. **Trace tags** on the parent trace via
   `MlflowClient.set_trace_tag(trace_id, ...)`: `feedback` (`up`/`down`/`none`),
   `feedback_score` (1.0 / −1.0 / 0.0), optional `feedback_comment`.
2. **Session run**: tag `feedback.<message_id[:8]>` and metric
   `feedback_score_last`.
3. **System run**: increments likes/dislikes/no-feedback counters and logs
   `system.likes`, `system.dislikes`, `system.no_feedback`,
   `system.like_ratio`.

No new trace or run is spawned for feedback — it attaches to the existing
trace, which is the whole point of the demo.

### 5.9 MLflow server options & persistence

| Mode | Tracking URI | Where data lives |
| --- | --- | --- |
| Local dev / docker | `./mlruns` (file store) | `backend/mlruns/` or the `mlruns` docker volume |
| Hosted (public demo) | `https://vartalaap-mlflow-XXXX.onrender.com` | **Neon Postgres** backend store |
| Disabled | `MLFLOW_ENABLED=false` | — (JSONL events still written to `backend/logs/`) |

Docker Compose (`docker-compose.yml`) runs three containers:

- `backend` — FastAPI on `:8000`, `MLFLOW_TRACKING_URI=/app/mlruns`,
  `MLFLOW_EXPERIMENT=vartalaap`.
- `frontend` — Next.js on `:3000` (`NEXT_PUBLIC_API_BASE_URL=http://localhost:8000`).
- `mlflow-ui` — `mlflow ui --backend-store-uri /app/mlruns --port 5000`,
  sharing the `mlruns` volume with the backend.

`mlflow_server/` is the **hosted tracking server** (Render Free web service,
Neon Postgres): start command
`mlflow server --backend-store-uri "$MLFLOW_BACKEND_STORE_URI"
--artifacts-destination /tmp/mlflow-artifacts --serve-artifacts --host 0.0.0.0
--port $PORT`. Runs/metrics/traces/tags live in Postgres; artifacts are
ephemeral on Render (only optional `feedback_<id>.md` artifacts are written).
Optional Cloudflare R2 S3 config for durable artifacts — see
`mlflow_server/README.md` and `docs/DEPLOY.md` §3.

Known caveats:

- `_SESSION_RUNS` is in-memory → restart creates new session runs.
- `system::vartalaap` counters are in-memory → totals reset on restart.
- Multiple backend workers would each keep their own counters (single-worker
  by design).

### 5.10 Swapping the sink (the Kytee seam)

`emitter._sink()` is the single chokepoint that writes every event. To add a
different backend (e.g. Kytee), change only `_sink` in
`backend/app/observability/emitter.py` — no call-site changes anywhere else.
MLflow-specific work already lives in `mlflow_sink.py`, so an alternative
sink would mirror that class.

### 5.11 Extending the pipeline (checklist for adding a stage/tool)

1. Add your stage/tool code under `app/`.
2. Wrap it in `emitter.span("name", kind="LLM|CHAIN|RETRIEVER|TOOL|AGENT",
   inputs={...})`.
3. `emitter.emit(MessageTag.X, content=..., msg_class=..., extra={...})`
   for schema events. Add new `MessageTag` values in `schemas/message.py`
   if needed.
4. If the stage calls an LLM, attach GenAI conventions via
   `emitter.set_span_chat(messages=..., input_tokens=..., output_tokens=...,
   model=...)`.
5. Call `emitter.set_span_outputs({...})` before the `with` block exits.
6. Keep schema additions in sync with the ADI doc fields in
   `schemas/message.py`; keep `metrics/evaluators.py` in sync if you change
   retrieval or answering behaviour.

---

## 6. Event log (JSONL)

Every emitted envelope is appended to
`backend/logs/events-YYYY-MM-DD.jsonl` (UTC partition), optionally mirrored
to stdout (`OBSERVABILITY_STDOUT=true`). Each line is a `MessageEnvelope`
dump: `identifiersessionid`, `identifieruserid`, `identifiermessageid`,
`messagetype`, `class`, `apiname`, `content`, `processedquery`,
`additionalinfo*`, `createddate`, `dt`. The full `events[]` array is also
returned inside every `ChatResponse` payload.

---

## 7. Frontend

Next.js 14 (App Router, TypeScript, Tailwind), Axis-styled pink/maroon theme.

- `app/page.tsx` — landing + chat composition.
- `components/ChatWindow.tsx` — main chat flow: sends `POST /chat` via
  `lib/api.ts`, renders messages, source cards (Relevancy/Type), thumbs
  feedback (👍/👎/⬜), and forwards `mlflow_run_id`/`mlflow_trace_id` back
  on `/feedback`.
- `components/LoginGate.tsx` — dummy login: display name → stable `user_id`
  in `localStorage`, attached to every request (`identifieruserid`).
- `components/BubbleTabs.tsx` — `All`, `HR`, `Download`, `Status`, `Aha`,
  `Law`, `Conversational BI`, `Axis Phone`, `Financial Advisor`,
  `IT Helpdesk`, `CR`.
- `lib/api.ts` — `sendChat`, `sendFeedback`, `fetchHealth`; base URL from
  `NEXT_PUBLIC_API_BASE_URL` (default `http://localhost:8000`).
- `components/Header.tsx` — includes an MLflow link
  (`NEXT_PUBLIC_MLFLOW_URL`) in the hosted demo.

---

## 8. Running the project

### 8.1 Docker (one command)

```powershell
git clone https://github.com/XENO2410/ADI.git
cd ADI
Copy-Item .env.example .env   # paste your OpenRouter key
docker compose up --build
```

| URL | Service |
| --- | --- |
| http://localhost:3000 | frontend |
| http://localhost:8000/docs | backend Swagger |
| http://localhost:5000 | MLflow UI (experiment `vartalaap`) |

Volumes persist `chroma`, `mlruns`, `logs`, and the HuggingFace cache.
`docker compose down -v` wipes state. Without an OpenRouter key the backend
runs on the deterministic offline stub and the pipeline remains fully
exercisable.

### 8.2 Local development

Backend:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m scripts.seed_kb --reset   # rebuild KB (needs sentence-transformers or HF token)
python -m app.main                  # or: uvicorn app.main:app --reload --port 8000
```

Frontend:

```powershell
cd frontend
Copy-Item .env.example .env.local
npm install
npm run dev                        # http://localhost:3000
```

### 8.3 API endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/` | landing JSON |
| `GET` | `/health` | LLM key, model, collection size, mlflow config |
| `POST` | `/chat` | main chat turn (returns `mlflow_run_id` + `mlflow_trace_id`) |
| `POST` | `/feedback` | 👍/👎/⬜ + optional comment → tags parent trace |
| `POST` | `/kb/reindex` | rebuild vector store (`?reset=true` to drop) |
| `GET` | `/docs` | OpenAPI Swagger |

---

## 9. Deployment (free public demo)

See `docs/DEPLOY.md` for step-by-step instructions. Summary:

| Component | Host | Notes |
| --- | --- | --- |
| Backend | Render Free | 512 MB, sleeps after 15 min idle; no torch (HF Inference API for query embeddings; pre-computed KB shipped in repo); `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| Frontend | Vercel Hobby | `NEXT_PUBLIC_API_BASE_URL` → backend URL |
| MLflow | 2nd Render service + Neon Postgres | `mlflow_server/` folder |

Release: tagging `v*.*.*` triggers `.github/workflows/release.yml`, pushing
`ghcr.io/xeno2410/vartalaap-backend:latest` and
`ghcr.io/xeno2410/vartalaap-frontend:latest` and drafting a GitHub Release.

CI (`.github/workflows/ci.yml`): backend `compileall` + AST parse on
Python 3.12; frontend `npm install` + `npm run build` on Node 20.

---

## 10. Evaluation harness — `jev_judge_eval/`

An independent benchmarking project that compares **TypeSafe JEV**
(`jev-1.13.0` — a typed-scoring model that returns probabilities, not text)
against **GPT-4o LLM-as-a-judge** arms for evaluating ADI-style chatbot
answers.

Fair-comparison arms (`--arms`): `ragas-gpt` (our metric definitions,
RAGAS-style claim decomposition), `matched-gpt` (GPT-4o answering JEV's exact
rubrics), `jev`, legacy `llm`, plus optional `gpt-mini`, `hybrid`, `hhem`.

Key scripts:

| Script | Purpose |
| --- | --- |
| `adi_gt_evaluator.py` | GPT-4o judge via OpenRouter (5 rows/call) |
| `jev_judge.py` | JEV judge, same sheet in / same metric columns out + confidence |
| `judge_arms.py` | extra arms (RAGAS-GPT, matched-rubric, hybrid) |
| `compare_judges.py` | runs arms on same rows; writes comparison workbook + CSVs |
| `build_presentation.py` | regenerates the 8-slide leadership PPTX (no API calls) |
| `data/build_synthetic_dataset.py`, `build_session_dataset.py` | regenerate datasets |

Run examples:

```powershell
python compare_judges.py --arms ragas-gpt matched-gpt jev   # fair three-way
python compare_judges.py --split dev --tune                 # dev split + threshold sweep
python compare_judges.py --split test                       # held-out test (--tune refused)
```

Datasets: `data/synthetic_adi_gt_35.csv` (35 rows) and
`data/synthetic_adi_gt_100_sessions_250_queries.csv` (100 sessions / 250
turns, with serialized history and gold labels). All data is synthetic.

Reported results (35 synthetic rows, 2 runs per judge, 2026-10-12): JEV agrees
with designer labels 98.6% vs GPT-4o 94.6%; catches 10/10 vs 5/10
hallucinations; median latency 0.35 s vs 4.1 s; cost per 1,000 rows $0.046 vs
$2.23. Full details and caveats in `jev_judge_eval/README.md`.

---

## 11. Environment variable reference

Full template in `.env.example`. The most important variables:

| Variable | Default | Purpose |
| --- | --- | --- |
| `OPENROUTER_API_KEY` | *(none)* | LLM access; empty → offline stub |
| `LLM_MODEL` / `LLM_FALLBACK_MODEL` | `openai/gpt-4o-mini` / `google/gemini-flash-1.5` | models |
| `HF_INFERENCE_TOKEN` | *(none)* | HF Inference API for query embeddings |
| `EMBEDDING_BACKEND` | `auto` | `sentence_transformers` \| `hf_inference` \| `hash` |
| `RERANKER_ENABLED` | `false` | BGE reranker (needs torch locally) |
| `RETRIEVER_TOP_K_CANDIDATES` / `_FINAL` | 50 / 5 | retrieval |
| `FAQ_HIGH_CONFIDENCE` / `_MEDIUM` | 0.85 / 0.60 | FAQ-first policy |
| `HISTORY_TURNS` | 2 | chat history window |
| `REFLEXION_ENABLED` / `_MAX_ITERATIONS` | true / 2 | reflexion loop |
| `MLFLOW_ENABLED` | true | observability switch |
| `MLFLOW_TRACKING_URI` | `./mlruns` | local path or http(s) URL |
| `MLFLOW_EXPERIMENT` | `vartalaap` | experiment name |
| `OBSERVABILITY_LOG_DIR` / `_STDOUT` | `./logs` / true | JSONL event log |
| `CORS_ORIGINS` | `http://localhost:3000` | comma-separated |
| `NEXT_PUBLIC_API_BASE_URL` | `http://localhost:8000` | frontend → backend |
| `NEXT_PUBLIC_MLFLOW_URL` | *(none)* | MLflow link in the header (hosted demo) |

---

## 12. Known limitations (by design)

- Status and Text2SQL tools are **mocks** (no real bank systems).
- Eval metrics are **heuristics**, not LLM-as-judge; swap in
  `metrics/evaluators.py` for real numbers (the `jev_judge_eval` harness
  exists for exactly this).
- Cost table in `metrics/costs.py` is approximate and must be updated when
  models change.
- Guardrails are demo-grade; not a production safety layer.
- `_SESSION_RUNS` / system counters are in-memory (reset on restart,
  single-worker assumption).
- The two Wikipedia-derived docs are CC-BY-SA 4.0 with attribution.

---

## 13. Security notes

- Never commit `.env` (gitignored). Keys are read only from environment at
  boot.
- If a key is ever committed/pasted publicly, rotate it immediately
  (OpenRouter, Hugging Face, TypeSafe, …).
- Do not deploy as a customer-facing assistant without a real safety layer.

---

## 14. Further reading (within the repo)

- [docs/ADI_MLFLOW_INTEGRATION_GUIDE.md](ADI_MLFLOW_INTEGRATION_GUIDE.md) — integrating MLflow across **ADI's ~52 microservices** (this repo's patterns lifted to the real system)
- [docs/MLFLOW_INTEGRATION_GUIDE.md](MLFLOW_INTEGRATION_GUIDE.md) — generic, step-by-step recipe for integrating MLflow into **any** system, using Vartalap as the reference
- [README.md](../README.md) — quick start, pipeline map, example prompts
- [docs/DEPLOY.md](DEPLOY.md) — Render/Vercel/Neon deployment walkthrough
- [mlflow_server/README.md](../mlflow_server/README.md) — hosted MLflow server
- [jev_judge_eval/README.md](../jev_judge_eval/README.md) — evaluation harness
- [backend/README.md](../backend/README.md) — backend runbook
- [CHANGELOG.md](../CHANGELOG.md) — release history
- [backend/app/observability/mlflow_sink.py](../backend/app/observability/mlflow_sink.py) — the MLflow sink (source of truth)
