# ADI — MLflow Integration Guide (multi-microservice rollout)

> **Audience:** engineers working on **ADI (Axis Deep Intelligence)** — the
> internal, employee-facing banking assistant at Axis Bank spread across
> ~52 microservice repositories — and AI assistants helping them.
>
> **Relationship to Vartalap:** [वार्तालाप (Vartalap)](../README.md) is a
> **single-repository reference implementation** of the ADI architecture.
> It mirrors ADI's message schema (§3/§12 of the ADI architecture doc) and
> pipeline, and it is where the MLflow instrumentation patterns were proven.
> This guide shows how to lift those patterns from Vartalap into the real,
> distributed ADI.
>
> **Companion document:** [docs/MLFLOW_INTEGRATION_GUIDE.md](MLFLOW_INTEGRATION_GUIDE.md) —
> the generic step-by-step recipe (one service). Read that first if you
> haven't; this guide assumes you know it and focuses on what is
> *ADI-specific*: scale (52 repos), banking compliance, and distributed
> tracing.

---

## 1. The Vartalap ↔ ADI relationship (read this first)

Vartalap is ADI's **observability testbed**. Everything ADI needs was first
made to work in Vartalap so the patterns could be validated without touching
production:

| ADI (real) | Vartalap (mirror) |
| --- | --- |
| ~52 microservice repos | 1 repo, `backend/` |
| Azure AI Search (top-50 → re-rank → top-5) | Chroma-style pure-Python vector store (same numbers: 50/5) |
| GPT-4o mini synthesis via internal gateway | OpenRouter (OpenAI-compatible) with offline stub |
| Real ESB / core-banking / Unidesk / Finacle / Tradax | Deterministic mock status tools |
| Real employee data | Synthetic policy corpus |
| ADI message schema (doc §3/§12) | `MessageEnvelope` in `backend/app/schemas/message.py` |
| Kytee + MLflow observability | `EventEmitter` + `MLflowSink` (the Kytee seam) |
| Evaluations on real SME-labelled sheets | `jev_judge_eval/` synthetic benchmark |

**What carries over 1:1** (proven in Vartalap, take as-is):

- The message schema → `MessageEnvelope` design (`extra="allow"`, nullable
  strings, `identifiermessageid`, `identifiersessionid`, `identifieruserid`).
- The run model: **run = session, trace = turn, span = stage**.
- The `mlflow.chat.*` GenAI conventions on LLM spans.
- Feedback attached to the existing trace (no new traces).
- Heuristic eval metrics → LLM-judge swap path.
- Cost tracking per model.
- The best-effort/no-crash policy.

**What must be extended for ADI** (not present in Vartalap):

- Cross-service trace propagation (a turn spans many microservices).
- A shared observability SDK consumable by all 52 repos.
- Banking-grade data controls (PII, DPDP, RBI expectations).
- Centralized, governed tracking infrastructure.

---

## 2. What the ADI architecture looks like (as understood today)

*From the ADI architecture doc mirrored by Vartalap, and the eval harness in
`jev_judge_eval/`.*

ADI is an internal employee assistant covering **products/subproducts**:
HR, CRES, Ops, product SOPs, policies, status queries (SR / credit card /
account opening / trade), structured DB lookups, conversational BI — roughly
the bubble tabs Vartalap's frontend shows. One user question flows through:

```
UI / channels
  → orchestration service
      ├─ preprocessing        (language detect → translate → spell → glossary)
      ├─ input guardrails
      ├─ routing / intent     (product, subproduct, use-case tagging)
      ├─ tool selection       (reactive agent)
      │     ├─ FAQ store      (FAQ-first policy)
      │     ├─ RAG over Azure AI Search   (retrieve top-50 → rerank top-5)
      │     ├─ status APIs    (Unidesk, Kaleidoscope, eForms, SDL, …)
      │     ├─ status DBs     (Finacle, Tradax, TRRACS, GPS, …)
      │     └─ Text2SQL       (structured banking tables)
      ├─ QA LLM               (GPT-4o mini synthesis w/ citations)
      ├─ Reflexion review     (doc §7.2 — retry with refined query)
      └─ output guardrails    (PII scrub)
```

In ADI each of those boxes is a separate microservice (hence ~52 repos:
frontends, orchestration, each tool family, retrieval, embeddings,
guardrails, gateway, plus platform services). The **message schema** is the
contract between them: one event row per stage with fields such as
`class`, `messagetype`, `apiname`, `additionalinfouserquery`,
`processedquery`, `additionalinfotags`, `additionalinfomodel`,
`additionalinfotokeninfo`, `additionalinfosources`,
`additionalinfotext2sqlquery`, `identifiersessionid`, `identifieruserid`,
`identifiermessageid`, `createddate`, `dt` — exactly the fields in
[`backend/app/schemas/message.py`](../backend/app/schemas/message.py).

> **Action item for your current architecture-study phase:** fill in the
> §9 inventory table as you map the repos — it doubles as the MLflow
> rollout plan.

---

## 3. Integration strategy overview

```
Phase 0  Shared observability SDK            (1 new internal repo, ~1 week)
Phase 1  Central MLflow infrastructure       (tracking server + Postgres, governed)
Phase 2  Instrument the critical path        (orchestration, RAG, QA LLM, gateway)
Phase 3  Fan out to all 52 repos             (standard per-service playbook)
Phase 4  Dashboards, eval, feedback loops    (system-wide roll-ups, LLM judges)
```

Ground rules:

1. **Observability is best-effort.** A downed MLflow server must never break
   an employee-facing answer. Every call guarded — the Vartalap `_try_init()`
   pattern, but in the SDK.
2. **The message schema stays the source of truth.** MLflow spans are a
   *view* of the same events, never a replacement for the event bus/log.
3. **One team owns the SDK; every repo consumes it.** No per-repo
   re-implementation of tracing.
4. **Banking data rules apply to traces.** PII and sensitive query text are
   redacted/truncated at emit time (see §7).

---

## 4. Phase 0 — the shared observability SDK

Do not copy `mlflow_sink.py` into 52 repos. Extract Vartalap's
`observability/` package into an internal SDK (e.g. `adi-observability`
PyPI/Artifactory package) that provides:

| SDK component | From Vartalap | ADI changes |
| --- | --- | --- |
| `EventEmitter` | [`emitter.py`](../backend/app/observability/emitter.py) | add async batch sink; wire to ADI's event bus instead of local JSONL |
| `MLflowSink` | [`mlflow_sink.py`](../backend/app/observability/mlflow_sink.py) | add cross-service trace propagation (§5.2); add redaction hook (§7) |
| `Settings` | [`config.py`](../backend/app/config.py) | add `ADI_SERVICE_NAME`, `ADI_ENV`, `ADI_REGION` tags |
| Schema enums | [`schemas/message.py`](../backend/app/schemas/message.py) | promote to the canonical ADI schema (it already mirrors it) |

SDK API shape that every ADI service calls (same ergonomics as Vartalap):

```python
from adi_observability import EventEmitter

emitter = EventEmitter(session_id=sid, user_id=uid, service="rag-service")
emitter.start_turn(query=q)

with emitter.span("azure_search.retrieve", kind="RETRIEVER", inputs={"query": q}):
    hits = azure_search.search(q, top=50)
    emitter.set_span_attributes(top_k=50, index=index_name)
    emitter.set_span_outputs({"doc_ids": [h.id for h in hits]})

emitter.finalize(response=resp, quality=quality)
```

Repos only call `emitter.*` — never `mlflow.*` directly. This is the single
most important architectural decision for 52 services.

---

## 5. Phase 1 — central MLflow infrastructure

### 5.1 Topology (banking constraints)

The public-demo topology from
[`mlflow_server/README.md`](../mlflow_server/README.md) (Render + Neon) is
**not** acceptable for ADI. For internal use:

| Choice | Recommendation | Why |
| --- | --- | --- |
| Tracking server | **Self-hosted `mlflow server`** in the bank's network | DPDP / RBI expectations; traces contain employee queries |
| Backend store | **PostgreSQL** (bank-managed instance) | runs/metrics/traces/tags durable; standard DBA governance |
| Artifact store | **S3-compatible / object storage** (internal) | durable `feedback_*.md` + any model artifacts |
| AuthN/AuthZ | SSO reverse proxy in front of MLflow | MLflow's own auth is basic; gate it with enterprise IdP |
| Kytee | Evaluate alongside; likely the sanctioned platform | Vartalap's `_sink()` seam exists precisely for this |

Start command (same as `mlflow_server/README.md`, but internal):

```bash
mlflow server \
  --backend-store-uri "$MLFLOW_BACKEND_STORE_URI" \
  --artifacts-destination s3://adi-mlflow/artifacts \
  --serve-artifacts \
  --host 0.0.0.0 --port $PORT
```

### 5.2 Experiment & run model at ADI scale

Vartalap uses a single experiment. With 52 services, adopt:

- **One experiment per environment + product family** or **one experiment
  per environment with a `service` tag on every run** — choose per team
  preference, but standardize. Vartalap's `MLFLOW_EXPERIMENT=vartalaap` maps
  to e.g. `adi-prod`.
- Every run gets the ADI version of Vartalap's session tags:

```python
mlflow.set_tags({
    "session_id": sid,
    "user_id": uid,              # hashed employee id — see §7
    "service": "rag-service",    # NEW for ADI
    "env": "prod",
    "region": "in-south",
    "bubble": bubble,            # product/subproduct
    "kind": "session",
})
```

- **Run model stays Vartalap's:** run = user session, trace = one turn.
  Add `service` as a tag so the trace table filters by microservice.

### 5.3 Cross-service distributed tracing (the big ADI extension)

In Vartalap everything runs in one process, so spans nest naturally. In ADI a
turn hops across services over HTTP/message bus. Extend the SDK:

1. **Pass the trace context forward.** The orchestration service creates the
   root span (per turn) and writes `mlflow_trace_id` (the root span's
   `request_id`) into the downstream call headers / message envelope:

   ```python
   # orchestration service
   headers["x-adi-trace-id"] = emitter.mlflow_trace_id
   headers["x-adi-session-id"] = session_id
   ```

2. **Child services join the trace.** Each service opens a span for its part
   of the turn and tags it with the upstream trace id (MLflow's trace is
   per-root-span, so the convention is explicit linking):

   ```python
   with emitter.span("rag.retrieve", kind="RETRIEVER") as span:
       span.set_attribute("adi.parent_trace_id", upstream_trace_id)
       span.set_attribute("adi.service", "rag-service")
       …
   ```

3. **Event bus services** (if ADI is event-driven) simply emit schema events;
   the consumer-side SDK attaches them to the current turn trace using the
   `identifiersessionid` already in the message schema — the schema *is* the
   correlation id.

This is the pattern to validate during your architecture study: which
services are synchronous HTTP hops vs. asynchronous bus hops, and where the
session id already flows.

---

## 6. Phase 2 & 3 — instrumenting the services

### 6.1 Which services first (critical path)

Instrument in this order — these are the stages whose spans appear in every
Vartalap trace tree (`backend/app/agents/supervisor.py`):

| # | ADI service | Vartalap equivalent | Spans / events to emit |
| --- | --- | --- | --- |
| 1 | Orchestration / supervisor | `agents/supervisor.py` | root span per turn, `USER_QUERY`, routing events, `CHAT_RESPONSE` |
| 2 | RAG retrieval | `rag/retriever.py`, `tools/kb_function.py` | `RETRIEVER` spans, `KNOWLEDGE_BASE_*` events, per-doc `RESPONSE_DOC` |
| 3 | QA LLM / gateway | `llm/openai_client.py`, `tools/kb_function.py` | `LLM` spans with `mlflow.chat.*` |
| 4 | Guardrails | `guardrails/filters.py` | `GUARDRAILS_*` events |
| 5 | Preprocessing | `preprocessing/*` | translate/refine spans + events |
| 6 | Status / Text2SQL tools | `tools/status.py`, `tools/text2sql.py` | `TOOL` spans |
| 7 | Reflexion | `agents/reflexion.py` | `reflexion.review` LLM span |
| 8 | Frontend(s) | `frontend/` | forward `mlflow_trace_id` to `/feedback` |

### 6.2 The per-repo playbook (do this 52 times)

For each ADI repo, open the companion
[MLFLOW_INTEGRATION_GUIDE.md](MLFLOW_INTEGRATION_GUIDE.md) and apply:

1. Add SDK dependency + `MLFLOW_*` + `ADI_SERVICE_NAME` env config (§3 of that guide).
2. Safe init / no-crash policy (§4).
3. Root span per unit of work, with `service` tag (§5–6).
4. Span per stage with correct span type (§7).
5. Schema events as span events, truncated content (§8).
6. `mlflow.chat.*` on every LLM span (§9) — mandatory for the QA LLM gateway.
7. `turn.*` / `eval.*` metrics + trace tags (§10–11).
8. Feedback on existing traces (§12).
9. Roll-ups into a shared `system::adi` run (§13).
10. `/health` reports `mlflow_enabled` + resolved URI (§15).

**CI enforcement:** add a lint/import check per repo (Vartalap's
[`.github/workflows/ci.yml`](../.github/workflows/ci.yml) does
`compileall` + AST parse with `MLFLOW_ENABLED=false` — copy that pattern) so
a missing optional `mlflow` import can never break a service.

---

## 7. Banking-grade data controls (mandatory for ADI)

Vartalap logs freely because everything is synthetic. ADI cannot. The SDK
must enforce, at emit time:

1. **Never log raw employee PII.** `user_id` = hashed employee id
   (`sha256(emp_id)`), never the raw id — Vartalap's `user_id` field already
   sits in the schema for exactly this swap.
2. **Truncate query/answer content.** Vartalap caps span event previews at
   280 chars and attributes at 2000 — keep those caps as *defaults*, and
   add an explicit deny-list redactor for account numbers, PAN, Aadhaar,
   mobile numbers before any span attribute or event is written.
3. **Redact, don't drop.** The trace must stay navigable — replace matches
   with `[REDACTED]`, don't remove the field.
4. **Feedback comments** (`feedback_comment` tag, `feedback_<id>.md`
   artifact) can contain free text — route artifacts to the governed
   object store and apply the same redactor.
5. **Retention & access.** Define TTL for trace data with the DBA team;
   restrict the MLflow UI to approved viewers via the SSO gateway (§5.1).
   Align with the DPDP obligations your compliance team specifies — this
   guide states the *technical* levers, not the legal policy.
6. **Compliance signals to track.** The eval harness in
   [`jev_judge_eval/`](../jev_judge_eval/README.md) already names the
   dimensions ADI cares about (RBI / DPDP / SEBI / IRDAI conduct standards) —
   mirror them as trace tags (`adi.compliance.dpdp=ok`, …) so audits can be
   answered from MLflow.

---

## 8. Evaluation & feedback at ADI scale

- **Inline heuristic metrics first** (Vartalap's `metrics/evaluators.py`),
  computed per turn in the orchestration service.
- **LLM-as-judge where it matters:** the `jev_judge_eval` benchmark compared
  GPT-4o vs TypeSafe JEV on ADI-style rows (agreement, hallucination recall,
  cost, latency — see its README). Use a sampled judge pipeline writing
  `eval.judge.*` metrics into the same runs.
- **Feedback loop stays Vartalap's:** `/feedback` with
  `mlflow_run_id` + `mlflow_trace_id` echoed back by every channel/frontend,
  tagging the existing trace. Never spawn new traces.

---

## 9. Architecture inventory — fill this in as you map the 52 repos

*This is the working table for your current study. One row per repo.*

| Repo / service | Stage in pipeline (doc §) | Sync HTTP or event bus? | Session id available? | LLM calls? | Instrumentation status |
| --- | --- | --- | --- | --- | --- |
| *(e.g. orchestration)* | supervisor (§2/§4) | http | yes | yes | Phase 2 |
| *(e.g. azure-search-retrieval)* | KB (§5.2/§5.3) | http | yes | no | Phase 2 |
| … | … | … | … | … | … |

Fields to record during architecture study because they change the MLflow
design:

- **Transport** — HTTP hops can carry `x-adi-trace-id` headers; bus hops
  must rely on `identifiersessionid` in the message schema.
- **Language** — Python services use the SDK directly; if ADI has non-Python
  services, the SDK needs an HTTP-sidecar or a spec (OpenTelemetry-compatible
  trace ids) that MLflow can import.
- **Gateway** — the LLM gateway is the natural place to set
  `mlflow.chat.*` attributes once for all services.

---

## 10. Rollout checklist (per phase)

**Phase 0 — SDK**
- [ ] `adi-observability` package published internally; Vartalap's
      `observability/` extracted and adapted (async sink, redaction hook).
- [ ] Schema enums promoted to canonical ADI schema.

**Phase 1 — Infrastructure**
- [ ] Self-hosted `mlflow server` + Postgres + internal object store up.
- [ ] SSO-gated UI reachable by the team.
- [ ] `system::adi` roll-up run design agreed (totals: turns, sessions,
      tokens, cost; averages: eval metrics; likes/dislikes).

**Phase 2 — Critical path**
- [ ] Orchestration, retrieval, QA LLM, guardrails instrumented.
- [ ] One end-to-end turn visible as a full trace with all span types.
- [ ] GenAI dashboards populated (Requests / Latency / Token Usage).

**Phase 3 — Fan out**
- [ ] Every repo has `ADI_SERVICE_NAME` + `MLFLOW_*` config.
- [ ] CI import check present in every repo.
- [ ] `/health` reports MLflow status in every service.

**Phase 4 — Value**
- [ ] `eval.*` metrics on every turn; sampled LLM-judge pipeline live.
- [ ] Feedback tags on traces; like/dislike roll-ups trending.
- [ ] Cost dashboard per product/subproduct (the metric that justifies ADI).

---

## 11. Success criteria (what "done" looks like)

1. Pick any employee query from the event log and pull up its **full trace**
   across every microservice it touched — one trace, all spans, correlated by
   session id.
2. Every LLM span shows tokens, model, and latency; dashboards show cost per
   product/subproduct.
3. Feedback on an answer is visible on that answer's trace.
4. MLflow downtime has zero effect on ADI answering employees.
5. A compliance reviewer can see what ADI logged about a turn — and confirm
   no raw PII is in it.

---

## 12. Open questions to resolve during the architecture study

- Which of the 52 repos are runtime path vs. platform/data repos?
- Is there already an event bus carrying the ADI message schema? (If yes,
  the SDK should sink into it, and MLflow should consume from it.)
- Does a Kytee deployment already exist, and is it the sanctioned platform?
  (Vartalap's `_sink()` seam supports both simultaneously.)
- Non-Python services: how many, and do they emit the message schema?
- Who owns the central Postgres/object-store governance?

---

## 13. Document map

| Doc | Use it for |
| --- | --- |
| [MLFLOW_INTEGRATION_GUIDE.md](MLFLOW_INTEGRATION_GUIDE.md) | The step-by-step instrumentation recipe for **one** service |
| [VARTALAP_GUIDE.md](VARTALAP_GUIDE.md) | Full project context; §5 is the MLflow reference |
| [mlflow_server/README.md](../mlflow_server/README.md) | Hosted tracking server setup |
| [docs/DEPLOY.md](DEPLOY.md) §3 | Server + Postgres walkthrough |
| [jev_judge_eval/README.md](../jev_judge_eval/README.md) | Judge/eval strategy for ADI-style answers |
