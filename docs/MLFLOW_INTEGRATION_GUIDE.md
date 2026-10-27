# MLflow Integration Guide — how to add MLflow observability to any system

> **Audience:** engineers who want to instrument a service (LLM app, RAG
> pipeline, chatbot, batch job) with MLflow tracing/metrics, and AI assistants
> asked to implement it.
>
> **Reference implementation:** this repository's [वार्तालाप (Vartalap)](../README.md)
> backend — every pattern below exists as working code here, mostly in
> [`backend/app/observability/mlflow_sink.py`](../backend/app/observability/mlflow_sink.py)
> and [`backend/app/observability/emitter.py`](../backend/app/observability/emitter.py).
>
> **Companion documents:**
> - [docs/ADI_MLFLOW_INTEGRATION_GUIDE.md](ADI_MLFLOW_INTEGRATION_GUIDE.md) —
>   rolling this out across **ADI's ~52 microservice repos** (banking controls,
>   cross-service tracing, phased plan) — this generic recipe is its §6.2 playbook.
> - [docs/VARTALAP_GUIDE.md](VARTALAP_GUIDE.md) — full project context; §5 is
>   the MLflow reference.

---

## 1. MLflow in 60 seconds

MLflow is an open-source observability platform for ML and GenAI workloads.
The pieces you will use:

| Concept | What it is | Vartalap example |
| --- | --- | --- |
| **Tracking server** | Where everything is written/read | local `file://backend/mlruns` or a hosted server |
| **Experiment** | A named grouping of runs | `vartalaap` |
| **Run** | One tracked unit of work, owns metrics/tags/params/artifacts | one run per chat **session** |
| **Trace** | A tree of spans for one invocation (MLflow ≥ 2.13) | one trace per chat **turn** |
| **Span** | A node in the trace: `LLM`, `CHAIN`, `RETRIEVER`, `TOOL`, `AGENT`, … | one span per pipeline stage |
| **Span event** | A timestamped note attached to a span | each `MessageEnvelope` event |
| **Metric** | Numeric, optionally step-indexed | `turn.cost_usd`, `eval.rag_score` |
| **Tag / param** | Key-value strings on runs or traces | `session_id`, `bubble`, `tool` |
| **GenAI conventions** | Reserved `mlflow.chat.*` span attributes | `mlflow.chat.tokenUsage` |

**Why manual instrumentation instead of `autolog`?** `mlflow.<framework>.autolog`
is great for training runs, but GenAI pipelines need *your* boundaries
(session, turn, stage) and *your* metrics. The manual pattern below — the one
Vartalap uses — gives you that control and is ~200 lines total.

---

## 2. Step 0 — choose your topology

Pick one of three setups (Vartalap supports all of them, see
[VARTALAP_GUIDE.md](VARTALAP_GUIDE.md) §5.9):

| Topology | Tracking URI | When to use |
| --- | --- | --- |
| **A. Local file store** | `./mlruns` (auto-resolved to `file://…`) | development, single box, Docker Compose |
| **B. Hosted tracking server + Postgres** | `https://mlflow.example.com` | production, multi-service, shared dashboard |
| **C. Disabled** | env `MLFLOW_ENABLED=false` | CI, environments without the server |

- A needs nothing but the `mlflow` package (data is a local directory).
- B is exactly the repo's [`mlflow_server/`](../mlflow_server/) service:
  `mlflow server --backend-store-uri postgresql://… --serve-artifacts` behind
  HTTPS (see [mlflow_server/README.md](../mlflow_server/README.md) and
  [docs/DEPLOY.md](DEPLOY.md) §3). Runs/traces/metrics/tags live in Postgres;
  artifacts are files on the server's disk.
- C keeps your event log (JSONL, stdout, or your own sink) running while
  MLflow is off.

---

## 3. Step 1 — add the dependency and config

**Dependency** (pin to the 2.17+ line so you get tracing + the GenAI
dashboards):

```txt
mlflow>=2.17,<4.0
```

**Config** — three env vars is all the runtime needs. Vartalap's version is
[`backend/app/config.py`](../backend/app/config.py):

```python
mlflow_enabled: bool = True                          # MLFLOW_ENABLED
mlflow_tracking_uri: str = "./mlruns"                # MLFLOW_TRACKING_URI
mlflow_experiment: str = "vartalaap"                 # MLFLOW_EXPERIMENT
```

The one piece of logic worth copying is **URI resolution** — pass
`http(s)://`, `file:`, `sqlite:`, `databricks:` through unchanged; turn any
bare path into an absolute `file://` URI so the store always lands where you
expect:

```python
@property
def mlflow_tracking_uri_resolved(self) -> str:
    uri = self.mlflow_tracking_uri
    if uri.startswith(("http://", "https://", "file:", "sqlite:", "databricks:")):
        return uri
    p = Path(uri)
    if not p.is_absolute():
        p = BACKEND_ROOT / p
    p.mkdir(parents=True, exist_ok=True)
    return p.absolute().as_uri()
```

---

## 4. Step 2 — initialize once, and **never crash on failure**

Observability must be a **best-effort sidecar**: if the tracking server is
down, your product must still work. Vartalap's `_try_init()` pattern
(module-level, called lazily) does exactly this:

1. Bail out if `MLFLOW_ENABLED` is false.
2. `import mlflow` inside a try/except (so MLflow is optional at import time).
3. `mlflow.set_tracking_uri(resolved)` and `mlflow.set_experiment(name)`
   (auto-creates the experiment).
4. Optionally enable **system metrics** (CPU/RAM per run):

```python
os.environ.setdefault("MLFLOW_ENABLE_SYSTEM_METRICS_LOGGING", "true")
mlflow.enable_system_metrics_logging()   # needs psutil; wrap in try/except
```

5. Every later MLflow call is individually wrapped in try/except and
   degrades to a no-op. Rule of thumb: **an observability error must never
   become a user-facing error.**

---

## 5. Step 3 — decide your run model (the most important design decision)

Before writing any span code, answer: *what does one MLflow run represent?*

Vartalap's answer (and a good default for any conversational/agent system):

| Unit | MLflow object | Name / id |
| --- | --- | --- |
| One user **session** | one **run** | `run_name="session::<id[:14]>"`, tags `session_id`, `user_id`, `kind=session` |
| One **turn/request** | one **trace** (root span) | `turn.NN :: <query[:60]>` |
| One pipeline **stage** | one **span** | `preprocess.translate`, `route`, `tool.kb`, `reflexion.review`, … |
| Whole deployment | one **roll-up run** | `system::vartalaap`, tags `kind=system` |

Key mechanics (from `mlflow_sink.py`):

- **Create-or-reopen**: keep an in-memory `{session_id: run_id}` cache;
  first turn creates the run (`start_run` + tags + params, then `end_run`),
  later turns reopen it with `mlflow.start_run(run_id=run_id)`.
- **Reopen safely**: wrap the reopened run in a context manager and exit it
  when the turn ends — never leave a run context open across requests.
- **Roll-up run**: a second, lazily-created run where you append
  cross-session aggregates with `step=<total_turns>` — this single run powers
  "how is the system doing overall" charts without querying many runs.

For non-conversational systems the same pattern applies: run = job/batch,
trace = item, spans = steps, roll-up run = deployment totals.

---

## 6. Step 4 — open a root span per unit of work (the trace)

```python
self._run_ctx = mlflow.start_run(run_id=self.run_id)
self._run_ctx.__enter__()                      # reopen the session run

self._root_span_ctx = mlflow.start_span(
    name=f"turn.{n:02d} :: {query[:60]}",
    span_type=SpanType.CHAIN,                  # LLM | CHAIN | RETRIEVER | TOOL | AGENT
    attributes={"session_id": …, "turn_index": n},
)
span = self._root_span_ctx.__enter__()
span.set_inputs({"query": query, "session_id": …})

trace_id = span.request_id                    # MLflow's trace identifier
```

Rules that make the trace table useful:

- The root span **name should be human-readable** (Vartalap: turn number +
  query snippet), because it is the row label in the trace table.
- Always `set_inputs(...)` on the root span; always `set_outputs(...)` at
  the end (Vartalap's root output: `{answer, sources, message_id}`).
- Save `trace_id` (`request_id`) in the API response so clients can attach
  feedback later (Vartalap returns `mlflow_trace_id` from `/chat`).
- Close spans/runs in `finally` so a crashed turn still produces a trace.

---

## 7. Step 5 — wrap every stage in a child span

The ergonomic pattern is a context manager (Vartalap:
`EventEmitter.span()` → `MLflowSink.span()`):

```python
with emitter.span("tool.kb", kind="RETRIEVER", inputs={"query": q}):
    result = kb_tool.run(q)
    emitter.set_span_attributes(faq_direct=result.faq_direct, num_returned=5)
    emitter.set_span_outputs({"chunks": […], "answer": result.answer})
```

- Map each span to the right **span type** (`SpanType.LLM`, `CHAIN`,
  `RETRIEVER`, `TOOL`, `AGENT`, …) — the UI colors and groups by it.
- Nested `with` blocks produce the nested trace tree automatically.
- Track the current span on a small stack (`_span_stack`) so helper
  functions can say "write outputs to the span I'm inside".
- Put **latency-sensitive names** in span names and queries/answers in
  inputs/outputs — MLflow records duration per span automatically.

---

## 8. Step 6 — record schema events as span events

If your system already produces domain events (audit rows, message schema),
tee them into the trace:

```python
span.add_event(
    name=envelope.messagetype,               # e.g. "LLM_QA_RESPONSE"
    attributes={
        "message_id": envelope.id,
        "class": "response",
        "api": "vartalaap.kb",
        "content_preview": text[:280],       # truncate! traces are not logs
    },
)
```

Vartalap keeps the **full** payload in a separate JSONL event log
([`backend/logs/events-*.jsonl`](../backend/logs/)) and only a preview on the
span — good practice: traces for navigation, the event log for replay.

---

## 9. Step 7 — attach MLflow GenAI conventions to LLM spans (the money step)

MLflow ≥ 2.17 renders the GenAI dashboard panels — **Requests, Latency,
Token Usage, Tokens per Trace** — only when spans carry the reserved
`mlflow.chat.*` attributes. On every span that makes an LLM call, set:

```python
span.set_attribute("mlflow.chat.messages", [
    {"role": "system", "content": sys},
    {"role": "user",   "content": usr},
    {"role": "assistant", "content": ans},
])
span.set_attribute("mlflow.chat.tokenUsage", {
    "input_tokens": 512, "output_tokens": 96, "total_tokens": 608,
})
span.set_attribute("mlflow.chat.model", "openai/gpt-4o-mini")
```

Vartalap does this in four places — wherever an LLM call happens:
[`supervisor.py`](../backend/app/agents/supervisor.py) (translation),
[`agents/reflexion.py`](../backend/app/agents/reflexion.py),
[`tools/kb_function.py`](../backend/app/tools/kb_function.py),
[`tools/text2sql.py`](../backend/app/tools/text2sql.py) — via
`emitter.set_span_chat(...)` → [`mlflow_sink.py`](../backend/app/observability/mlflow_sink.py) `set_current_chat()`.

Additionally, set `mlflow.chat.tokenUsage` + `mlflow.chat.model` on the
**root span** with the turn's totals (`finalize()`), so even turns that made
no LLM call (e.g. FAQ-direct answers) appear correctly in the dashboards.

---

## 10. Step 8 — log metrics and tags on the run (per-turn time series)

At the end of each turn, write step-indexed metrics on the session run
(`step = turn index`) so you get per-session time series:

```python
mlflow.log_metrics({
    "turn.prompt_tokens": float(pt), "turn.completion_tokens": float(ct),
    "turn.total_tokens": float(tt),  "turn.cost_usd": cost,
    "turn.num_sources": float(n),    "turn.reflexion_iterations": float(it),
    "eval.rag_score": 0.82,          "eval.faithfulness": 0.9,
    …
}, step=turn_index)

mlflow.set_tag(f"turn.{turn_index:02d}.tool", "kb")       # per-turn tags
mlflow.set_tag(f"turn.{turn_index:02d}.use_case", "generic_rag")
```

- Prefix by unit (`turn.`, `eval.`, `system.`) — flat metric namespaces are
  easy to chart and cheap to rename later.
- **Cost tracking**: keep a per-model USD/1M-token table
  ([`metrics/costs.py`](../backend/app/metrics/costs.py)) and log
  `cost_usd` — the single most valuable metric for LLM products.
- Heuristic eval metrics are fine to start; swap in an LLM judge later
  (this repo's [`jev_judge_eval/`](../jev_judge_eval/) benchmarks exactly that).

---

## 11. Step 9 — surface per-trace tags (what the trace table shows)

Metrics belong to runs; **tags belong to traces**. Use
`MlflowClient.set_trace_tag` so each trace row in the UI shows its metadata:

```python
from mlflow import MlflowClient
client = MlflowClient()
client.set_trace_tag(trace_id, "tool", "kb")
client.set_trace_tag(trace_id, "cost_usd", f"{cost:.6f}")
client.set_trace_tag(trace_id, "eval.rag_score", f"{quality.rag_score:.3f}")
```

Vartalap tags every trace with `tool`, `use_case`, `user_id`, `bubble`,
`model`, `total_tokens`, `cost_usd`, and `eval.*` scores.

---

## 12. Step 10 — feedback attaches to the **existing** trace

Never spawn a new trace for user feedback. Attach it to the trace that
produced the answer:

```python
client.set_trace_tag(trace_id, "feedback", "up")          # up | down | none
client.set_trace_tag(trace_id, "feedback_score", "1.00")  # 1 / -1 / 0
client.set_trace_tag(trace_id, "feedback_comment", comment[:500])
```

Then update the session run (`mlflow.log_metric("feedback_score_last", 1.0)`)
and the roll-up run (`system.likes`, `system.dislikes`,
`system.like_ratio`). This is `log_feedback()` in
[`mlflow_sink.py`](../backend/app/observability/mlflow_sink.py), called from
`POST /feedback`.

Requirements for this to work end-to-end:

1. `/chat` returns `mlflow_run_id` + `mlflow_trace_id`.
2. The client echoes them back with the feedback call.
3. The server looks up the trace by id and tags it.

---

## 13. Step 11 — cross-session roll-ups (the `system::…` run)

Create one shared run per deployment (`run_name="system::vartalaap"`,
tags `app=…, kind=system`) and append aggregates on every turn with
`step = total_turns`:

```python
with mlflow.start_run(run_id=system_run_id):
    mlflow.log_metrics({
        "system.total_turns": float(turns),
        "system.total_cost_usd": float(cost_sum),
        "system.avg_cost_per_turn_usd": cost_sum / turns,
        "system.eval.avg_rag_score": rag_sum / turns,
        "system.like_ratio": likes / max(1, likes + dislikes),
    }, step=turns)
```

This is the cheapest way to get a system-level dashboard: one run, one line
per turn, no aggregation queries. (Caveat, same as Vartalap's: counters are
in-memory per process — use Postgres or a proper store if you run multiple
workers.)

---

## 14. Step 12 — expose the UI

- **Docker Compose** (local dev): a third service that reuses the same
  volume as the writer — exactly
  [`docker-compose.yml`](../docker-compose.yml)'s `mlflow-ui` service:

  ```yaml
  mlflow-ui:
    image: vartalaap-backend:latest
    command: ["mlflow", "ui", "--backend-store-uri", "/app/mlruns",
              "--host", "0.0.0.0", "--port", "5000"]
    volumes: [ "mlruns:/app/mlruns" ]
    ports: [ "5000:5000" ]
  ```

- **Production**: a hosted `mlflow server` with a Postgres backend store
  (repo folder [`mlflow_server/`](../mlflow_server/)):

  ```bash
  mlflow server \
    --backend-store-uri "$MLFLOW_BACKEND_STORE_URI" \   # postgresql://…
    --artifacts-destination /tmp/mlflow-artifacts \
    --serve-artifacts \
    --host 0.0.0.0 --port $PORT
  ```

  Then point the app at it with `MLFLOW_TRACKING_URI=https://<host>` — the
  URI passthrough logic from §3 means zero code changes. Add a
  `NEXT_PUBLIC_MLFLOW_URL` link in your UI header (Vartalap does).

---

## 15. Step 13 — kill switch and diagnostics

- `MLFLOW_ENABLED=false` must turn **everything** MLflow-related into a
  no-op while your own event log keeps working (Vartalap's JSONL sink is
  independent of the MLflow sink).
- Expose config in `/health`: Vartalap reports `mlflow_enabled`,
  `mlflow_tracking_uri`, `mlflow_experiment` — make your healthcheck do the
  same so a misconfigured URI is visible before users hit it.
- Log MLflow failures to stderr with a clear prefix
  (`[mlflow-sink] start_turn failed: …`) and move on.

---

## 16. Integration checklist (verifying it worked)

Send one request through your pipeline, then confirm in the MLflow UI:

- [ ] Experiment exists with the configured name.
- [ ] One **run** per session; one **trace** per turn, named readably.
- [ ] Trace tree shows every stage as a span with correct type, inputs,
      outputs, and latency.
- [ ] LLM spans carry `mlflow.chat.messages` / `mlflow.chat.tokenUsage` /
      `mlflow.chat.model`; the GenAI dashboards show Requests / Latency /
      Token Usage / Tokens per Trace.
- [ ] Session run shows `turn.*` and `eval.*` step charts.
- [ ] Trace row tags show `tool`, `use_case`, `model`, `cost_usd`, `eval.*`.
- [ ] Feedback tags land on the existing trace (no new trace).
- [ ] `system::…` run accumulates totals and averages.
- [ ] Kill the tracking server → your app keeps serving (no-op sink).

---

## 17. Where each pattern lives in Vartalap (copy-from map)

| Guide section | Vartalap code |
| --- | --- |
| §3 Config + URI resolution | [`backend/app/config.py`](../backend/app/config.py) |
| §4 Safe init / no-op | [`mlflow_sink.py`](../backend/app/observability/mlflow_sink.py) `_try_init()` |
| §5 Run model | `mlflow_sink.py` `_get_or_create_session_run()`, `_get_or_create_system_run()` |
| §6 Root span / trace | `mlflow_sink.py` `MLflowSink.start_turn()` |
| §7 Child spans | `mlflow_sink.py` `MLflowSink.span()`, [`emitter.py`](../backend/app/observability/emitter.py) |
| §8 Span events | `mlflow_sink.py` `MLflowSink.log_event()` |
| §9 GenAI conventions | `mlflow_sink.py` `MLflowSink.set_current_chat()` + `finalize()` |
| §10 Run metrics | `mlflow_sink.py` `MLflowSink.finalize()` |
| §11 Trace tags | `mlflow_sink.py` `_set_trace_tags()` |
| §12 Feedback | `mlflow_sink.py` `log_feedback()` |
| §13 Roll-ups | `mlflow_sink.py` `_log_system_aggregates()` |
| §14 UI / server | [`docker-compose.yml`](../docker-compose.yml), [`mlflow_server/`](../mlflow_server/) |
| §15 Kill switch | [`backend/app/main.py`](../backend/app/main.py) `/health`, `config.py` |

---

## 18. Common pitfalls

1. **Crashes when the server is unreachable** — every MLflow call must be
   guarded; observability is best-effort (§4).
2. **No GenAI panels in the UI** — you forgot the `mlflow.chat.*` attributes
   or you're on MLflow < 2.17 (§9).
3. **One run per request instead of per session** — step metrics become
   useless time series (§5).
4. **Feedback creates new traces** — attach to the existing trace via
   `set_trace_tag` (§12).
5. **Counters reset on restart / diverge across workers** — keep a single
   writer or persist counters (§13).
6. **Giant span attributes** — truncate content previews and stringify dicts
   (Vartalap caps at 280 / 2000 chars, §8).
7. **Artifacts lost on ephemeral disks** — runs/metrics/traces belong in
   Postgres; only artifacts need a bucket (Cloudflare R2 works, see
   [mlflow_server/README.md](../mlflow_server/README.md)).

---

## 19. Further reading

- [docs/VARTALAP_GUIDE.md](VARTALAP_GUIDE.md) §5 — MLflow details specific to this repo
- [mlflow_server/README.md](../mlflow_server/README.md) — hosted tracking server
- [docs/DEPLOY.md](DEPLOY.md) §3 — Render + Neon Postgres walkthrough
- [MLflow tracing docs](https://mlflow.org/docs/latest/llms/tracing/index.html)
- [MLflow GenAI conventions](https://mlflow.org/docs/latest/llms/tracing/index.html#genai-tracing-conventions)
