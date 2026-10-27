# ADI/Cerebro Local Multi-Service Mock — Design & Planning (rev. 2)

> **Status:** IDEATION / PLANNING ONLY — no code has been implemented.
> Nothing in this document modifies Vartalap, the original ADI repositories,
> or the existing OTel mocks.
>
> **Rev. 2 changes:** managed SageMaker MLflow compatibility spike is now
> Phase 0; cross-process tracing is a post-P0 decision; stable span names;
> traces-first run model (no roll-up runs); evaluation runs owned by workers;
> BM25/token-overlap retrieval; cardinality/payload rules; conditional debug
> fields; `compatibility/` folder; clarified env vars; new phase order;
> approved implementation choices recorded.
>
> **Reference implementations used for patterns (read-only):** Vartalap's
> [`backend/app/observability/mlflow_sink.py`](../backend/app/observability/mlflow_sink.py),
> [`backend/app/observability/emitter.py`](../backend/app/observability/emitter.py),
> [`backend/app/config.py`](../backend/app/config.py),
> [`backend/app/metrics/`](../backend/app/metrics/), and
> [docs/VARTALAP_GUIDE.md](VARTALAP_GUIDE.md).

---

## 1. Purpose and scope

Build a **local, synthetic, multi-service mock** of a subset of the ADI/Cerebro
**Kubernetes stack** that demonstrates how MLflow provides GenAI observability
for a realistic ADI Chat/RAG flow — with real service boundaries.

**First vertical slice (approved, unchanged):**

```
mock-client (synthetic, CLI)
   └─▶ ai-orchestrator-service-mlflow-mock      (owns the conversation trace)
         ├─▶ guardrails-service-mlflow-mock     (input)
         ├─▶ knowledge-base-service-mlflow-mock (retrieve, FAQ-first, no LLM)
         ├─▶ deterministic offline LLM (in-orchestrator) or optional configured LLM
         ├─▶ guardrails-service-mlflow-mock     (output)
         └─▶ final response  ──▶ feedback  ──▶ asynchronous evaluation
```

**In scope:** 3 mock services + 1 synthetic client + 1 shared observability
package + 1 evaluation worker + a Phase-0 compatibility spike. Synthetic data
only. Deterministic offline execution by default.

**Explicitly out of scope:** the other ~45 ADI repos, the entire Lambda stack,
streaming/WebSocket behaviour, Talk2Doc, real Azure/AWS services, PII-bearing
data, production-contract claims.

---

## 2. Approved implementation choices (locked)

These were reviewed and approved; they are the scaffold defaults:

| # | Choice | Value |
| --- | --- | --- |
| A1 | Workspace | sibling `adi-mlflow-mocks/`, standalone git repo, not inside the Vartalap repo |
| A2 | Ports | 8100 orchestrator · 8200 guardrails · 8300 KB · 8400 eval worker — **all env-configurable** |
| A3 | Venv | one **shared venv** for direct laptop development |
| A4 | Dependencies | **separate `requirements.txt` and Dockerfile per service**; one shared package |
| A5 | Feedback UX | **CLI feedback** in the first slice |
| A6 | Design doc | copied into the new workspace (`adi-mlflow-mocks/ADI_MULTISERVICE_MOCK_DESIGN.md`) at scaffold time |

---

## 3. Revised design decisions

| # | Decision | Choice | Why |
| --- | --- | --- | --- |
| D1 | Phase 0 | **Managed SageMaker MLflow compatibility spike first** (matrix in §5) | Every tracing/run choice after P0 must be grounded in what the managed backend actually supports |
| D2 | Cross-process tracing | **Decision deferred to after P0.** Three candidates compared (§6): native remote parent propagation, OTel trace-context, correlation-ID-linked per-service traces | Do not finalise before compatibility results |
| D3 | Language / runtime | Python 3.12, FastAPI + uvicorn, httpx | Matches Vartalap stack; zero new infra |
| D4 | Transport | HTTP/JSON REST between services | Contracts model **service responsibility and correlation only** — not production WebSocket compatibility (§8) |
| D5 | Online observability unit | **Trace is primary.** One trace per service per request. Session/message/turn ids are **trace metadata** | Traces are the unit the managed MLflow renders best |
| D6 | Run model | **One run per test execution / regression suite / configuration version** (per participating service); **separate evaluation runs owned by the eval worker**. No `system::*` roll-ups, no process-local counters in slice 1 | Runs = batch/experiment context, not online state (§7) |
| D7 | Span naming | **Stable names only** (§7.2). Query text never enters span names | Low-cardinality names keep traces searchable and PII-safe |
| D8 | Shared code | `adi_observability_mock` package in `shared/`, installed editable into the shared venv | One implementation of the sink/policy for all services |
| D9 | Retrieval | **Deterministic FAQ match + BM25/token-overlap** retrieval; hash/vector embeddings **deferred** until slice 1 is stable | No torch, no network, deterministic scores |
| D10 | LLM | Deterministic offline stub; optional OpenAI-compatible client if a key is present | Pipeline runs with zero network |
| D11 | MLflow connectivity | Env vars per §11; local `./mlruns` fallback when `MLFLOW_TRACKING_URI` unset; SigV4 only for remote URIs | Matches verified CML pattern |
| D12 | Fail-open | `MLFLOW_FAIL_OPEN=true` default; `false` reserved for tests | Observability errors never break answers |
| D13 | Payload discipline | Tags = bounded low-cardinality dimensions; attributes = bounded metadata; events = bounded diagnostics; artifacts = large reports; JSONL = local fallback (§10) | Prevents trace bloat and leakage |
| D14 | Debug payloads | `OBSERVABILITY_DEBUG_PAYLOADS` flag, **default off**. Full `events[]` and child-trace maps excluded from default responses | Keep the API contract clean |
| D15 | Naming | Every service folder ends in `-mlflow-mock`; no Lambda-stack components (`app-layer-service`, `llm-service`, `prompt-builder-service`) in this mock | Hard separation from the Lambda stack and old OTel mocks |
| D16 | Secrets | Managed ARN / AWS account ID **never** in committed files; compatibility report redacted (§5.4) | — |

---

## 4. Phases (revised order)

| Phase | Scope | Exit criteria |
| --- | --- | --- |
| **P0** | **Managed SageMaker MLflow compatibility spike** — smoke scripts against the managed endpoint (SigV4), full matrix §5, redacted `compatibility_report.md` | Matrix filled in; cross-process tracing approach (§6) selected; assessment support confirmed/refuted |
| **P1** | **Shared observability package** (`shared/adi_observability_mock`): config, correlation context, schemas, payload policy, emitter, sink, metrics helpers, http client | Unit tests green: env-var handling, fail-open, JSONL, caps, debug-flag behaviour |
| **P2** | **KB and guardrails mocks** — synthetic data, FAQ+BM25 retrieval, stable spans, own traces, JSONL | Each service independently verified: trace round-trip + contract tests |
| **P3** | **Orchestrator + mock-client + full offline turn** — routing, LLM stub, both guardrail hops, suite-execution run, turn metrics | Full vertical slice offline: one turn → one orchestrator trace + child traces + suite-run metrics |
| **P4** | **Feedback + asynchronous evaluation** — CLI feedback tags the existing trace; eval worker owns evaluation runs with link tags | Feedback on existing trace verified; evaluation linkage via 7 link tags verified |
| **P5** | **Concurrency, failure injection, Docker Compose, remote CML validation** — per-service Dockerfiles, compose, parallel-write test, fail-open drills, run against managed endpoint | Full acceptance matrix §12 green; compose up/down repeatable |

Later (not planned in detail): `api-invoker-service-mlflow-mock` (8500),
`db-connector-service-mlflow-mock` (8600, Text2SQL),
`content-parser-service-mlflow-mock` (8700), streaming, Talk2Doc-style Q&A.

---

## 5. Phase 0 — managed SageMaker MLflow compatibility spike

### 5.1 Goal

Prove, against the **managed SageMaker MLflow endpoint** available from the CML
environment, which MLflow capabilities the mock can rely on — before writing
the shared package or any service code.

### 5.2 Compatibility test matrix

All tests use the env-var config in §11; the endpoint URI is supplied at
runtime from the environment, never from committed files.

| # | Test | What it verifies | Pass criteria |
| --- | --- | --- | --- |
| C1 | SigV4 tracking | Auth path works with `MLFLOW_TRACKING_AWS_SIGV4=true` against the managed URI | `set_tracking_uri` + first API call succeed without embedded credentials |
| C2 | Experiment lookup | `get_experiment_by_name("ADI")` | Returns or auto-creates exactly one experiment, idempotently |
| C3 | Run creation / search | `start_run` + tags → `search_runs` with tag filter | Round-trip returns the run with tags intact |
| C4 | Trace creation / search | Root span (`request_id`) → `search_traces` by tag/filter | Round-trip; trace tags and timestamps present |
| C5 | Nested spans | 3-level span tree (`CHAIN` → `RETRIEVER` → `LLM`) | Parent-child structure and ordering preserved after search |
| C6 | Post-completion trace tags / assessments | `set_trace_tag` after root span close; trace assessment API if present | Recorded as **supported** or **unsupported**; assessment path only adopted if confirmed |
| C7 | `mlflow.chat.*` rendering | `mlflow.chat.messages` / `tokenUsage` / `model` on an LLM span | Attributes survive round-trip; UI render noted as a manual best-effort check |
| C8 | Artifacts | `log_text` / `log_artifact` to the managed artifact location | Upload + download works; artifact location written in the report as a redacted placeholder only |
| C9 | Concurrent writes | N parallel traces (e.g. 16 threads × 4 spans) | All traces/searchable, no corruption, no cross-talk |
| C10 | Unavailable-server behaviour | Point at a dead endpoint; run with `MLFLOW_FAIL_OPEN=true` and `=false` | `true`: app continues, no exception; `false`: failure is surfaced (test-only mode) |

### 5.3 What the matrix decides

- **Cross-process tracing approach** (§6) — C6/C4/C5 determine whether remote
  parents or OTel context are viable, or whether correlation-ID linking (always
  works) is the baseline.
- **Assessments vs trace tags for feedback/eval** — C6 decides.
- **Whether the sink may rely on trace-search APIs** for the stitch tool — C4.

### 5.4 `compatibility/` folder (proposed)

```
compatibility/
├── README.md                  # how to run against the managed endpoint (env-only config)
├── smoke_tests.py             # parametrised C1–C9 checks, one flag per test
├── concurrency_smoke.py       # C9
├── fail_open_smoke.py         # C10
└── compatibility_report.md    # completed results + the post-P0 decision
```

The report **must not contain** AWS account IDs, tracking ARNs, credentials,
or artifact-bucket paths — placeholders (`<managed-endpoint-host>`,
`<redacted>`) are required by the report template.

---

## 6. Cross-process tracing — decision deferred to after P0

One turn crosses three processes. Three candidate mechanisms are on the table;
**one is selected only after the P0 matrix results**:

| Candidate | Mechanism | Preconditions / rules |
| --- | --- | --- |
| **A. Native remote parent propagation** | Pass MLflow trace/request context across services so child services create spans inside the upstream trace | Only if P0 shows the managed MLflow supports remote parent context; never guess the API surface |
| **B. OpenTelemetry trace-context propagation** | `traceparent` header carrying a valid trace-context downstream | Use **only when valid**: 32-hex trace-id + 16-hex parent-span-id generated per hop. **Never reuse a trace ID as a parent span ID.** Never set `traceparent` when invalid. Adopt only if P0 confirms the managed backend imports/accepts OTel context |
| **C. Separate per-service traces linked by correlation ID** | Each service owns its trace; link tags (`adi.root_trace_id`, `adi.parent_trace_id`, `adi.session_id`, `adi.turn_id`, `adi.request_id`) connect them | Always works, lossless, no backend dependency; `stitch` CLI reconstructs the turn by filtering `search_traces` on `adi.root_trace_id` |

**Selection rule:** A if P0 proves it; else B if P0 proves OTel acceptance and
the `traceparent` validity rules can be enforced; **C is the guaranteed
baseline that every service implements regardless** (its link tags are set
in all three options, so the slice never blocks on the decision).

`traceparent` discipline (applies if B is chosen): generate a fresh 16-hex
parent-span-id for each outgoing hop; preserve the 32-hex trace-id; never
substitute the trace-id into the parent-span-id field.

---

## 7. Run / trace model (revised)

### 7.1 Traces — the primary online unit

- **One trace per service per request.** Root span name is the service's
  stable operation name (§7.2).
- **Session / message / turn ids are trace metadata** — trace tags
  (`adi.session_id`, `adi.turn_id`, `adi.message_id`, `adi.request_id`,
  correlation tags from §6) — never the identity of a run.
- Trace tags also carry the low-cardinality dimensions for filtering:
  `service`, `env`, `use_case`, `tool`, `bubble`, `model`.

### 7.2 Span naming (stable, no query text)

| Service | Root span | Child spans |
| --- | --- | --- |
| orchestrator | `adi.chat.turn` (CHAIN) | `preprocess.refine`, `guardrails.input.evaluate`, `route.select_tool` (AGENT), `knowledge_base.retrieve` (RETRIEVER hop), `llm.generate` (LLM), `guardrails.output.evaluate`, `reflexion.review` (LLM) |
| guardrails | `guardrails.input.evaluate` / `guardrails.output.evaluate` | `guardrails.rule.evaluate` |
| KB | `knowledge_base.retrieve` (RETRIEVER) | `kb.faq.match`, `kb.bm25.search`, `kb.rerank.top5` |
| eval worker | `evaluation.run` | `evaluation.metric.<name>` per metric |

Query previews appear **only** in bounded events (`query_preview` ≤ 80 chars,
synthetic/redacted), never in span names.

### 7.3 Runs — batch context, not online state

- **Suite-execution runs:** one run per test execution / regression-suite
  invocation / configuration version, per participating service.
  Run name `suite::<suite>::<config_version>::<service>`; tags are
  **low-cardinality only** (`service`, `env`, `suite`, `config_version`,
  `kind=suite-execution`). Per-turn metrics (`turn.*`, cost) are written with
  `step=turn_index` inside the suite run.
- **Evaluation runs:** created and **owned by the evaluation worker** (P4).
  The worker never reopens or mutates an online service run. Link tags on the
  evaluation run: `trace_id`, `message_id`, `session_id`,
  `evaluation_run_id`, `dataset_version`, `evaluator_version`,
  `rubric_version`; `eval.*` metrics live here with `step=turn_index`.
- **No `system::*` roll-up runs and no process-local counters** in the initial
  slice. Cross-service aggregates are deferred until a search-based or
  offline aggregation design exists.
- **Feedback** records as trace tags on the existing trace (C6-approved
  assessments replace tags only if P0 confirms support). Run-level like/dislike
  aggregates are deferred with the roll-ups.

---

## 8. Service contracts (Phase 1 — responsibility + correlation only)

Phase-1 HTTP contracts **model service responsibility and correlation** for
observability purposes. They make **no claim** of production WebSocket or
streaming compatibility and are labelled synthetic in code docstrings.

### 8.1 knowledge-base-service-mlflow-mock — `POST /retrieve` (8300)

```json
// request
{ "query": "…", "bubble": "HR", "top_k_candidates": 50, "top_k_final": 5,
  "correlation": { "session_id": "…", "turn_id": "…", "user_id": "…",
                   "root_trace_id": "…", "parent_trace_id": "…", "request_id": "…" } }
// response
{ "chunks": [ { "id": "…", "title": "…", "domain": "HR", "bm25_score": 0.81,
                "rerank_score": 0.9, "text": "…" } ],   // ≤ 5 entries
  "faq_hit": false, "faq_confidence": 0.0,
  "kb_trace_id": "…" }
```

### 8.2 guardrails-service-mlflow-mock — `POST /guardrails` (8200)

```json
// request
{ "direction": "input" | "output", "text": "…", "correlation": { … } }
// response
{ "allowed": true, "reasons": [], "scrubbed_text": "…", "guardrails_trace_id": "…" }
```

### 8.3 ai-orchestrator-service-mlflow-mock — `POST /chat`, `/feedback`, `/evaluate` (8100)

`POST /chat` response — **default (clean)**:

```json
{
  "session_id": "…", "message_id": "…", "turn_id": "…",
  "answer": "…",
  "sources": [ { "title": "…", "type": "MD|FAQ", "relevancy": "High", "score": 0.82 } ],
  "use_case": "generic_rag" | "text2sql" | "status_api" | "guardrailed",
  "tool_used": "kb" | "text2sql" | "status" | "guardrails",
  "mlflow_trace_id": "…", "mlflow_run_id": "…",
  "num_events": 14
}
```

With `OBSERVABILITY_DEBUG_PAYLOADS=true` (local/test config only), the
response additionally includes `events` (full envelope list) and
`child_traces` (per-service trace ids). **Default responses never return full
events or child-trace maps.**

`POST /feedback` — same contract as Vartalap: `session_id`, `message_id`,
`feedback` (`up|down|none`), optional `comment` (≤ 500 chars),
`mlflow_trace_id`. Tags the existing trace; no new trace, no new run.

`POST /evaluate` — fire-and-forget to the eval worker with the turn payload +
`mlflow_trace_id` + `turn_index`; the worker creates its own evaluation run.

### 8.4 evaluation-worker-mlflow-mock — `POST /evaluate` (8400)

Accepts `{turn_payload, mlflow_trace_id, turn_index}`; computes heuristic
`eval.*` metrics; writes them to a worker-owned evaluation run (with the 7
link tags from §7.3) and links back via trace tags. If P0 shows assessments
are supported, the worker writes post-hoc trace assessments instead of tags;
otherwise tags only.

### 8.5 mock-client (CLI)

`python -m mock_client.client --scenario leave-policy --feedback up` — prints
the answer, trace ids, and the stitch command. Scenarios are deterministic.

---

## 9. Synthetic data & retrieval (slice 1)

- **Docs:** ~8–12 tiny synthetic Markdown files across
  `HR / IT_HELPDESK / CR / DOWNLOAD / CONVERSATIONAL_BI / GENERAL`
  (2–4 short sections each).
- **FAQs:** ~20-row CSV (`id, question, answer, domain, product, role`).
- **Retrieval path (no embeddings in slice 1):**
  1. **FAQ-first deterministic match** — token-overlap similarity ≥ 0.85
     answers directly (no LLM call, zero tokens).
  2. **BM25 / token-overlap search** — score chunks, return top-50
     candidates.
  3. **Token-overlap rerank** — re-score candidates against the query +
     FAQ/domain priors, return top-5.
  4. Hash/vector embeddings are **deferred** until the first slice is stable.
- **Query scenarios** (`mock-client/scenarios.py`):

| Scenario | Expected path | Demonstrates |
| --- | --- | --- |
| `leave-policy` | KB RAG → LLM synthesis with `[S1]…` citations | RETRIEVER + LLM spans, tokens/cost |
| `faq-hit` | FAQ direct answer, no LLM | zero-token turn, FAQ-first policy |
| `blocked-input` | input guardrail blocks | guardrailed turn, no downstream calls |
| `pii-output` | output guardrail scrubs | scrub attributes |
| `analytic` | routed but stubbed (slice 1) | use-case routing metadata |
| `unknown` | retrieval finds nothing → refusal | refusal eval path |

---

## 10. Cardinality & payload rules

| Channel | Rule | Enforced by |
| --- | --- | --- |
| **Run tags** | Bounded **low-cardinality dimensions only**: `service`, `env`, `suite`, `config_version`, `kind`. No per-turn ids | sink |
| **Trace tags** | Per-trace metadata only: session/turn/message ids, correlation ids, feedback, `use_case`, `tool`, `bubble`, `model` — count ≤ 12, id values ≤ 64 chars, comment ≤ 500 chars | sink |
| **Span attributes** | Bounded metadata: counts, scores, booleans, small dicts — ≤ 30 keys, each ≤ 2000 chars when JSON-stringified | payload policy |
| **Span events** | Bounded diagnostics: `query_preview` ≤ 80 chars, content previews ≤ 280 chars, chunk/source lists ≤ 20 entries | payload policy |
| **Artifacts** | Large reports only (scenario reports, stitch reports) — the single unbounded channel | sink |
| **JSONL** | Local fallback, same envelope as events, same caps | emitter |
| **Prohibited everywhere** | Raw prompts, full documents, credentials, internal endpoints, personal data; AWS account IDs / ARNs / bucket paths in committed files | payload policy + report template |
| **Sanctioned exception** | `mlflow.chat.messages` carries **synthetic, bounded** message content (≤ 2000 chars each) because the GenAI dashboards require it | sink |

---

## 11. Environment variables (canonical list)

| Variable | Default | Meaning |
| --- | --- | --- |
| `MLFLOW_TRACKING_URI` | *(unset)* | Managed endpoint in CML (SigV4); unset → local `./mlruns` file store |
| `MLFLOW_EXPERIMENT` | `ADI` | Experiment name |
| `MLFLOW_TRACKING_AWS_SIGV4` | `false` | Set `true` when the URI is the managed endpoint; ignored locally |
| `MLFLOW_ENABLED` | `true` | Master switch for MLflow; `false` → JSONL-only mode |
| `MLFLOW_FAIL_OPEN` | `true` | `true`: observability errors are swallowed (product-first); `false`: surfaced (test/dev only) |
| `OBSERVABILITY_JSONL_ENABLED` | `true` | Local JSONL event fallback |
| `OBSERVABILITY_DEBUG_PAYLOADS` | `false` | Include full `events[]` / child-trace maps in responses (local/test only) |

Init order (pinned by a unit test in P1): set SigV4 env **before**
`set_tracking_uri`, then `set_experiment("ADI")` — exactly the verified CML
pattern.

**Never commit** the managed ARN, AWS account ID, or endpoint credentials —
they come from the runtime environment only.

---

## 12. Acceptance criteria (updated)

| # | Requirement | Demonstrated by | Verified by |
| --- | --- | --- | --- |
| 1 | Distributed service boundaries | 3 services, separate processes/ports | compose + ports table |
| 2 | Shared correlation ids | `x-adi-*` headers end-to-end | correlation unit tests + stitch output |
| 3 | MLflow tracing with **stable span names** | span names match §7.2 exactly; no query text in names | trace assertions |
| 4 | Cross-process correlation per the **post-P0 decision** | option A/B/C implemented per §6; `traceparent` validity rules honoured if B | integration test + P0 report cross-ref |
| 5 | Model & token metadata | `mlflow.chat.*` on `llm.generate` | trace assertions |
| 6 | Retrieval metadata | bm25/rerank scores, FAQ confidence, chunk count tags | KB trace assertions |
| 7 | Guardrail outcomes | block + scrub attributes on both hops | guardrails tests |
| 8 | Latency & errors | span durations; injected KB-down → error status on hop span, refusal answer | failure-injection test |
| 9 | Feedback linkage | tags on the existing trace (assessments only if C6) | no-new-trace assertion |
| 10 | Evaluation linkage | worker-owned eval run with the 7 link tags; `eval.*` metrics | eval test |
| 11 | Cost calculation | `turn.cost_usd` in suite-execution run | metrics assertions |
| 12 | JSONL fallback | per-service `logs/events-*.jsonl` | file assertions |
| 13 | Deterministic offline | full demo with no keys, no network | `demo.ps1` offline run |
| 14 | Synthetic data only | docs/FAQs fixtures; no Axis/PII strings | grep assertion in tests |
| 15 | Cardinality & payload rules hold | caps from §10 asserted on emitted traces/events | payload-policy tests |
| 16 | Debug fields off by default | default `/chat` response lacks `events`/`child_traces` | contract tests |
| 17 | No secrets in committed files | repo scan: no ARNs, account IDs, keys | CI grep check |

---

## 13. Error & edge-case matrix

| Case | Behaviour |
| --- | --- |
| KB service down | orchestrator marks error status on the hop span, returns a refusal; turn still traced |
| Guardrails block input | no downstream calls; `use_case=guardrailed`; minimal trace |
| LLM key absent | deterministic stub; `mlflow.chat.model = offline-stub`; cost = 0 |
| LLM key present but API fails | fallback to stub; error attribute on span |
| MLflow server unreachable | `MLFLOW_FAIL_OPEN=true`: answers continue, JSONL carries events; `=false` (tests): failure surfaced |
| FAQ high-confidence hit | KB answers directly; orchestrator skips LLM; 0 tokens logged |
| Feedback on unknown message_id | 400 + error event; no trace corruption |
| Invalid `traceparent` received (option B) | header dropped; correlation falls back to link tags; never propagated |

---

## 14. Validation plan

1. **P0 matrix** — §5.2 all 10 rows executed; redacted report committed.
2. **Unit tests (P1+)** — config resolution + SigV4 ordering, fail-open modes,
   JSONL toggle, payload caps, debug-flag behaviour, correlation context.
3. **Integration test (P3)** — one scripted offline turn: assert response
   payload, JSONL files, MLflow state via `MlflowClient` (traces, tags,
   chat attrs, suite-run metrics).
4. **Evaluation test (P4)** — worker owns its run; 7 link tags present; no
   mutation of the service run.
5. **Stitch test (P5)** — reconstruction tool works under the chosen §6
   option; if option C, filter on `adi.root_trace_id`.
6. **Failure injection (P5)** — stop KB mid-turn; assert graceful degradation.
7. **Remote validation (P5)** — same suite against the managed endpoint with
   SigV4; concurrency test re-run.
8. **No-regression on Vartalap** — mocks run with the Vartalap repo removed
   from `PYTHONPATH`; no reads/writes into it.

---

## 15. Updated directory structure (proposed)

```
adi-mlflow-mocks/                              # NEW sibling of the Vartalap repo
│
├── README.md                                  # run guide, diagram, ports table
├── ADI_MULTISERVICE_MOCK_DESIGN.md            # this document, copied at scaffold time (A6)
├── .env.example                               # env template per §11 (no secrets)
├── .gitignore                                 # .env, mlruns/, logs/, .venv/
│
├── compatibility/                             # P0 — managed SageMaker MLflow spike
│   ├── README.md                              # run instructions (env-only config)
│   ├── smoke_tests.py                         # C1–C9 checks, one flag per test
│   ├── concurrency_smoke.py                   # C9 parallel writes
│   ├── fail_open_smoke.py                     # C10 unavailable-server behaviour
│   └── compatibility_report.md                # redacted results + post-P0 decision
│
├── shared/
│   └── adi_observability_mock/                # the ONE observability package (P1)
│       ├── __init__.py
│       ├── config.py                          # env vars §11 + URI resolution + SigV4 order
│       ├── correlation.py                     # header names, context carrier, id generators
│       ├── schemas.py                         # event envelope (ADI message-schema fields)
│       ├── payload_policy.py                  # caps + prohibited-content rules (§10)
│       ├── emitter.py                         # EventEmitter API (span/emit/set_*)
│       ├── sink.py                            # traces-first sink: spans, chat attrs,
│       │                                      #   trace tags, suite-execution runs,
│       │                                      #   JSONL, fail-open, no roll-ups
│       ├── metrics.py                         # cost table + metric helpers (no counters)
│       └── client.py                          # httpx helper injecting correlation headers
│
├── mock-client/
│   ├── client.py                              # CLI: send turn, print answer + trace ids
│   ├── scenarios.py                           # deterministic scenarios (§9)
│   └── feedback.py                            # CLI feedback
│
├── ai-orchestrator-service-mlflow-mock/       # 8100 (env-configurable)
│   ├── app.py                                 # POST /chat /feedback /evaluate
│   ├── orchestrator.py                        # turn orchestration, root trace owner
│   ├── router.py                              # use-case routing (chat/rag | text2sql | api)
│   ├── llm.py                                 # offline stub + optional configured LLM
│   ├── requirements.txt
│   ├── Dockerfile
│   └── tests/
│       ├── test_orchestrator_offline.py
│       └── test_correlation_headers.py
│
├── guardrails-service-mlflow-mock/            # 8200
│   ├── app.py                                 # POST /guardrails {direction}
│   ├── filters.py                             # deterministic block / PII-scrub
│   ├── requirements.txt
│   ├── Dockerfile
│   └── tests/test_guardrails.py
│
├── knowledge-base-service-mlflow-mock/        # 8300
│   ├── app.py                                 # POST /retrieve
│   ├── retriever.py                           # FAQ-first + BM25/token-overlap
│   ├── bm25.py                                # token-overlap scorer (no embeddings)
│   ├── data/
│   │   ├── synthetic_docs/                    # 8–12 tiny MD docs
│   │   └── faqs.csv                           # ~20 synthetic FAQs
│   ├── requirements.txt
│   ├── Dockerfile
│   └── tests/test_retrieve.py
│
├── evaluation-worker-mlflow-mock/             # 8400
│   ├── app.py                                 # POST /evaluate — owns evaluation runs
│   ├── evaluator.py                           # heuristic eval.* metrics
│   ├── requirements.txt
│   ├── Dockerfile
│   └── tests/test_evaluation_run.py
│
├── run/
│   ├── start_all.ps1 / start_all.sh           # launch services on configured ports
│   ├── stop_all.ps1 / stop_all.sh
│   └── demo.ps1 / demo.sh                     # start → scenarios → print trace ids
│
└── docker-compose.yml                         # P5 — one image per service (A4)
```

Future services (same pattern, later phases): `api-invoker-service-mlflow-mock`
(8500), `db-connector-service-mlflow-mock` (8600, Text2SQL),
`content-parser-service-mlflow-mock` (8700).

---

## 16. Remaining blocking decisions (need your sign-off before P0)

1. **Managed endpoint availability for P0** — confirm the SageMaker MLflow
   URI is exposed in the CML environment at runtime (`MLFLOW_TRACKING_URI`
   env var, never committed). P0 cannot run without it.
2. **P0 decision gate** — approve the §6 selection rule (A → B → C baseline)
   so the post-P0 tracing decision does not require another review round.
3. **Assessment fallback** — if C6 reports assessments unsupported, confirm
   trace tags remain the accepted mechanism for feedback/eval linkage (this
   design assumes yes).
4. **Evaluation dataset/rubric versioning** — confirm the initial values for
   `dataset_version` / `evaluator_version` / `rubric_version`
   (proposed: `synthetic-v0.1` / `heuristic-v0.1` / `rubric-v0.1`).
5. **Docker availability for P5** — confirm Docker Desktop is available on
   the laptop; if not, P5's compose step degrades to process-based
   orchestration only.

---

## 17. Non-goals and guardrails (repeatable rules)

- ❌ No Lambda-stack components: no `app-layer-service`, no `llm-service`,
  no `prompt-builder-service`, no Lambda contracts on v2 mocks.
- ❌ No production-contract claims — Phase-1 contracts model responsibility
  and correlation only, explicitly synthetic.
- ❌ No real Azure/AWS service calls, no real LLM keys required, no PII.
- ❌ No reuse/modification of the existing OTel mocks or Vartalap.
- ❌ No single "everything" service — three real processes minimum.
- ❌ No committed secrets: no managed ARNs, AWS account IDs, credentials,
  artifact-bucket paths in any committed file.
- ✅ All folders end in `-mlflow-mock`; all data fixtures synthetic.
- ✅ Stable span names only; query previews only in bounded events.

---

## 18. Document map

- [VARTALAP_GUIDE.md](VARTALAP_GUIDE.md) §5 — MLflow patterns this design reuses
- [MLFLOW_INTEGRATION_GUIDE.md](MLFLOW_INTEGRATION_GUIDE.md) — per-service instrumentation recipe (P1/P3 playbook)
- [ADI_MLFLOW_INTEGRATION_GUIDE.md](ADI_MLFLOW_INTEGRATION_GUIDE.md) — the ADI rollout strategy this mock validates
