"""MLflow sink for observability events.

Model:
    - **One MLflow run per session.** Persisted in an in-memory session→run
      cache; first turn creates it, subsequent turns reopen it.
    - **One trace per chat turn.** `start_turn` opens a root span → creates
      a trace; every stage the supervisor wraps in `emitter.span(...)`
      becomes a child span with proper inputs/outputs/latency.
    - **User feedback lives on the trace itself** (not a new trace) via
      `MlflowClient.set_trace_tag(request_id, ...)`.
    - **Roll-up metrics** are also written to a shared `system::vartalaap`
      run — cross-session totals + rolling averages.

Enabled via `MLFLOW_ENABLED=true` (default). Safe no-op if mlflow is not
installed or the tracking URI is unreachable.
"""
from __future__ import annotations

import json
import os
import threading
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Iterator, Optional

from ..config import get_settings
from ..metrics import QualityMetrics, usd_cost


_LOCK = threading.Lock()
_INITED = False

_SESSION_RUNS: dict[str, str] = {}
_SESSION_TURNS: dict[str, int] = {}
_SESSION_UNIQUE_USERS: set[str] = set()
_SESSIONS_LOCK = threading.Lock()

_SYSTEM_RUN_ID: Optional[str] = None
_SYSTEM_LOCK = threading.Lock()
_SYSTEM_COUNTERS: dict[str, float] = {
    "turns": 0,
    "sessions": 0,
    "prompt_tokens": 0.0,
    "completion_tokens": 0.0,
    "total_tokens": 0.0,
    "cost_usd": 0.0,
    "likes": 0,
    "dislikes": 0,
    "no_feedback": 0,
    "guardrailed": 0,
    "reflexion_retries": 0,
    "num_sources": 0.0,
    # eval sums used for running averages
    "eval_context_relevance_sum": 0.0,
    "eval_faithfulness_sum": 0.0,
    "eval_answer_relevance_sum": 0.0,
    "eval_history_relevance_sum": 0.0,
    "eval_tone_sum": 0.0,
    "eval_toxicity_sum": 0.0,
    "eval_rag_score_sum": 0.0,
}


def _try_init() -> bool:
    global _INITED
    if _INITED:
        return True
    with _LOCK:
        if _INITED:
            return True
        settings = get_settings()
        if not settings.mlflow_enabled:
            _INITED = True
            return False
        try:
            import mlflow  # type: ignore
        except Exception:  # noqa: BLE001
            _INITED = True
            return False
        try:
            mlflow.set_tracking_uri(settings.mlflow_tracking_uri_resolved)
            mlflow.set_experiment(settings.mlflow_experiment)
            # System metrics: CPU / RAM samples per run (needs psutil).
            os.environ.setdefault("MLFLOW_ENABLE_SYSTEM_METRICS_LOGGING", "true")
            try:
                mlflow.enable_system_metrics_logging()
            except Exception:  # noqa: BLE001
                pass
        except Exception:  # noqa: BLE001
            _INITED = True
            return False
        _INITED = True
        return True


def _span_type_or(mlflow_mod, name: str, fallback: str = "CHAIN"):
    from mlflow.entities import SpanType  # type: ignore

    return getattr(SpanType, name, getattr(SpanType, fallback, "CHAIN"))


def _stringify(attributes: dict[str, Any]) -> dict[str, Any]:
    clean: dict[str, Any] = {}
    for key, value in attributes.items():
        if value is None:
            continue
        if isinstance(value, (str, int, float, bool)):
            clean[key] = value
        else:
            try:
                clean[key] = json.dumps(value, ensure_ascii=False, default=str)[:2000]
            except Exception:  # noqa: BLE001
                clean[key] = str(value)[:2000]
    return clean


# ---------------------------------------------------------------------------
def _get_or_create_session_run(
    mlflow_mod,
    *,
    session_id: str,
    user_id: str,
    bubble: Optional[str],
) -> Optional[str]:
    with _SESSIONS_LOCK:
        run_id = _SESSION_RUNS.get(session_id)
        if run_id:
            return run_id
    try:
        run = mlflow_mod.start_run(run_name=f"session::{session_id[:14]}")
        try:
            mlflow_mod.set_tags(
                {
                    "session_id": session_id,
                    "user_id": user_id or "anonymous",
                    "bubble": bubble or "All",
                    "app": "vartalaap",
                    "kind": "session",
                }
            )
            mlflow_mod.log_param("first_seen", datetime.now(timezone.utc).isoformat())
        finally:
            mlflow_mod.end_run()
        with _SESSIONS_LOCK:
            _SESSION_RUNS[session_id] = run.info.run_id
            _SYSTEM_COUNTERS["sessions"] += 1
            _SESSION_UNIQUE_USERS.add(user_id or "anonymous")
        return run.info.run_id
    except Exception:  # noqa: BLE001
        return None


def _bump_turn_counter(session_id: str) -> int:
    with _SESSIONS_LOCK:
        _SESSION_TURNS[session_id] = _SESSION_TURNS.get(session_id, 0) + 1
        return _SESSION_TURNS[session_id]


def _get_or_create_system_run(mlflow_mod) -> Optional[str]:
    global _SYSTEM_RUN_ID
    if _SYSTEM_RUN_ID:
        return _SYSTEM_RUN_ID
    with _SYSTEM_LOCK:
        if _SYSTEM_RUN_ID:
            return _SYSTEM_RUN_ID
        try:
            run = mlflow_mod.start_run(run_name="system::vartalaap")
            try:
                mlflow_mod.set_tags(
                    {"app": "vartalaap", "kind": "system"}
                )
                mlflow_mod.log_param(
                    "boot_at", datetime.now(timezone.utc).isoformat()
                )
            finally:
                mlflow_mod.end_run()
            _SYSTEM_RUN_ID = run.info.run_id
        except Exception:  # noqa: BLE001
            return None
        return _SYSTEM_RUN_ID


# ---------------------------------------------------------------------------
def _accumulate_tokens(totals: dict[str, int], token_info_json: Optional[str]) -> None:
    if not token_info_json:
        return
    try:
        info = json.loads(token_info_json)
    except Exception:  # noqa: BLE001
        return
    for key in ("prompt_tokens", "completion_tokens", "total_tokens"):
        value = int(info.get(key) or 0)
        if not value:
            continue
        if key == "total_tokens":
            totals["total_tokens"] += value
        else:
            totals[f"{key}_total"] += value


# ---------------------------------------------------------------------------
class MLflowSink:
    """Turn-scoped MLflow tracing sink."""

    def __init__(
        self,
        *,
        session_id: str,
        user_id: str,
        bubble: Optional[str],
    ) -> None:
        self.session_id = session_id
        self.user_id = user_id or "anonymous"
        self.bubble = bubble or "All"
        self.run_id: Optional[str] = None
        self.trace_id: Optional[str] = None
        self._enabled = False
        self._mlflow = None

        self._run_ctx = None
        self._root_span_ctx = None
        self._root_span = None
        self._span_stack: list[Any] = []
        self._turn_index = 0
        self._token_totals: dict[str, int] = {
            "prompt_tokens_total": 0,
            "completion_tokens_total": 0,
            "total_tokens": 0,
        }
        self._models_seen: set[str] = set()

        if not _try_init():
            return
        try:
            import mlflow  # type: ignore
        except Exception:  # noqa: BLE001
            return
        self._mlflow = mlflow
        self._enabled = True

    # ------------------------------------------------------------------
    @property
    def enabled(self) -> bool:
        return self._enabled and self._mlflow is not None

    # ------------------------------------------------------------------
    def start_turn(self, query: str) -> None:
        if not self.enabled:
            return
        mlflow = self._mlflow
        try:
            self.run_id = _get_or_create_session_run(
                mlflow,
                session_id=self.session_id,
                user_id=self.user_id,
                bubble=self.bubble,
            )
            if not self.run_id:
                self._enabled = False
                return
            self._turn_index = _bump_turn_counter(self.session_id)

            self._run_ctx = mlflow.start_run(run_id=self.run_id)
            self._run_ctx.__enter__()

            self._root_span_ctx = mlflow.start_span(
                name=f"turn.{self._turn_index:02d} :: {(query or '')[:60]}",
                span_type=_span_type_or(mlflow, "CHAIN"),
                attributes=_stringify(
                    {
                        "session_id": self.session_id,
                        "user_id": self.user_id,
                        "bubble": self.bubble,
                        "turn_index": self._turn_index,
                    }
                ),
            )
            self._root_span = self._root_span_ctx.__enter__()
            try:
                self._root_span.set_inputs(
                    {
                        "query": query,
                        "session_id": self.session_id,
                        "user_id": self.user_id,
                        "bubble": self.bubble,
                        "turn_index": self._turn_index,
                    }
                )
            except Exception:  # noqa: BLE001
                pass
            self.trace_id = getattr(self._root_span, "request_id", None) or getattr(
                self._root_span, "trace_id", None
            )
        except Exception as exc:  # noqa: BLE001
            import sys

            sys.stderr.write(f"[mlflow-sink] start_turn failed: {exc!r}\n")
            self._safe_close()
            self._enabled = False

    # ------------------------------------------------------------------
    @contextmanager
    def span(
        self,
        name: str,
        *,
        kind: str = "CHAIN",
        inputs: Optional[dict[str, Any]] = None,
        attributes: Optional[dict[str, Any]] = None,
    ) -> Iterator[Any]:
        if not self.enabled or self._root_span is None:
            yield None
            return
        mlflow = self._mlflow
        try:
            ctx = mlflow.start_span(
                name=name,
                span_type=_span_type_or(mlflow, kind),
                attributes=_stringify(attributes) if attributes else None,
            )
            span = ctx.__enter__()
            if inputs:
                try:
                    span.set_inputs(inputs)
                except Exception:  # noqa: BLE001
                    pass
        except Exception as exc:  # noqa: BLE001
            import sys

            sys.stderr.write(f"[mlflow-sink] span({name!r}) failed: {exc!r}\n")
            yield None
            return
        self._span_stack.append(span)
        try:
            yield span
        finally:
            self._span_stack.pop()
            try:
                ctx.__exit__(None, None, None)
            except Exception:  # noqa: BLE001
                pass

    def _current_span(self):
        if self._span_stack:
            return self._span_stack[-1]
        return self._root_span

    def set_current_outputs(self, outputs: dict[str, Any]) -> None:
        span = self._current_span()
        if span is None:
            return
        try:
            span.set_outputs(outputs)
        except Exception:  # noqa: BLE001
            pass

    def set_current_attributes(self, attributes: dict[str, Any]) -> None:
        span = self._current_span()
        if span is None:
            return
        try:
            span.set_attributes(_stringify(attributes))
        except Exception:  # noqa: BLE001
            pass

    def set_current_chat(
        self,
        *,
        messages: Optional[list[dict[str, Any]]] = None,
        input_tokens: Optional[int] = None,
        output_tokens: Optional[int] = None,
        model: Optional[str] = None,
    ) -> None:
        """Attach MLflow GenAI conventions to the current LLM span.

        MLflow's tracing UI aggregates `mlflow.chat.tokenUsage` (into the
        "Token Usage" / "Tokens per Trace" panels) and renders
        `mlflow.chat.messages` in the trace inspector. Setting these keys is
        what turns a plain span into a first-class LLM call in the dashboard.
        """
        span = self._current_span()
        if span is None:
            return
        try:
            if messages is not None:
                span.set_attribute("mlflow.chat.messages", messages)
            if input_tokens is not None or output_tokens is not None:
                total = int((input_tokens or 0) + (output_tokens or 0))
                span.set_attribute(
                    "mlflow.chat.tokenUsage",
                    {
                        "input_tokens": int(input_tokens or 0),
                        "output_tokens": int(output_tokens or 0),
                        "total_tokens": total,
                    },
                )
            if model:
                span.set_attribute("mlflow.chat.model", model)
        except Exception:  # noqa: BLE001
            pass

    def mark_current_error(self, message: str) -> None:
        span = self._current_span()
        if span is None:
            return
        try:
            from mlflow.entities import SpanStatusCode  # type: ignore

            span.set_status(SpanStatusCode.ERROR, description=message[:300])
        except Exception:  # noqa: BLE001
            try:
                span.set_attribute("error.message", message[:300])
            except Exception:  # noqa: BLE001
                pass

    # ------------------------------------------------------------------
    def log_event(self, envelope) -> None:
        if not self.enabled:
            return
        _accumulate_tokens(
            self._token_totals, getattr(envelope, "additionalinfotokeninfo", None)
        )
        model = getattr(envelope, "additionalinfomodel", None)
        if model:
            self._models_seen.add(model)
        span = self._current_span()
        if span is None:
            return
        try:
            span.add_event(
                name=envelope.messagetype or "event",
                attributes=_stringify(
                    {
                        "message_id": envelope.identifiermessageid,
                        "class": envelope.class_,
                        "api": envelope.apiname,
                        "content_preview": (envelope.content or "")[:280],
                    }
                ),
            )
        except Exception:  # noqa: BLE001
            pass

    # ------------------------------------------------------------------
    def finalize(
        self,
        *,
        response,
        events: list,
        quality: Optional[QualityMetrics] = None,
        retrieval_scores: Optional[list[float]] = None,
    ) -> None:
        if not self.enabled:
            return
        mlflow = self._mlflow
        prompt_tokens = self._token_totals["prompt_tokens_total"]
        completion_tokens = self._token_totals["completion_tokens_total"]
        total_tokens = self._token_totals["total_tokens"]
        primary_model = next(iter(self._models_seen), None) or "unknown"
        cost = usd_cost(primary_model, prompt_tokens, completion_tokens)

        try:
            if self._root_span is not None:
                attrs: dict[str, Any] = {
                    "message_id": response.message_id,
                    "tool_used": response.tool_used,
                    "use_case": response.use_case,
                    "reflexion_iterations": response.reflexion_iterations,
                    "num_events": len(events),
                    "num_sources": len(response.sources),
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": total_tokens,
                    "cost_usd": cost,
                    "model_primary": primary_model,
                    "models_used": ",".join(sorted(self._models_seen)) or "-",
                }
                if quality:
                    attrs.update(quality.to_metric_dict(prefix="eval."))
                self._root_span.set_attributes(_stringify(attrs))
                # GenAI conventions — these are what MLflow's tracing
                # dashboard reads for the "Token Usage" / "Tokens per Trace"
                # / "Requests" panels. Same values as the plain attrs above,
                # but under keys MLflow understands.
                try:
                    self._root_span.set_attribute(
                        "mlflow.chat.tokenUsage",
                        {
                            "input_tokens": int(prompt_tokens),
                            "output_tokens": int(completion_tokens),
                            "total_tokens": int(total_tokens),
                        },
                    )
                    self._root_span.set_attribute("mlflow.chat.model", primary_model)
                except Exception:  # noqa: BLE001
                    pass
                self._root_span.set_outputs(
                    {
                        "answer": response.answer,
                        "sources": [
                            {
                                "title": s.title,
                                "type": s.type,
                                "relevancy": s.relevancy,
                                "score": s.score,
                            }
                            for s in response.sources
                        ],
                        "message_id": response.message_id,
                    }
                )

            # Session-level per-turn metric time-series (step=turn_index)
            per_turn_metrics: dict[str, float] = {
                "turn.prompt_tokens": float(prompt_tokens),
                "turn.completion_tokens": float(completion_tokens),
                "turn.total_tokens": float(total_tokens),
                "turn.cost_usd": float(cost),
                "turn.num_sources": float(len(response.sources)),
                "turn.num_events": float(len(events)),
                "turn.reflexion_iterations": float(response.reflexion_iterations),
            }
            if quality:
                per_turn_metrics.update(quality.to_metric_dict(prefix="eval."))
            try:
                mlflow.log_metrics(per_turn_metrics, step=self._turn_index)
                mlflow.set_tag(
                    f"turn.{self._turn_index:02d}.tool", response.tool_used or "-"
                )
                mlflow.set_tag(
                    f"turn.{self._turn_index:02d}.use_case", response.use_case or "-"
                )
                mlflow.set_tag(
                    f"turn.{self._turn_index:02d}.model", primary_model
                )
            except Exception:  # noqa: BLE001
                pass

            # Copy the same eval + cost tags onto the TRACE row so the
            # trace table shows them in the Tags column.
            if self.trace_id:
                trace_tags = {
                    "tool": response.tool_used or "-",
                    "use_case": response.use_case or "-",
                    "user_id": self.user_id,
                    "bubble": self.bubble,
                    "model": primary_model,
                    "total_tokens": str(total_tokens),
                    "cost_usd": f"{cost:.6f}",
                }
                if quality:
                    trace_tags.update(
                        {
                            "eval.rag_score": f"{quality.rag_score:.3f}",
                            "eval.context_relevance": f"{quality.context_relevance:.3f}",
                            "eval.faithfulness": f"{quality.faithfulness:.3f}",
                            "eval.answer_relevance": f"{quality.answer_relevance:.3f}",
                            "eval.toxicity": f"{quality.toxicity:.3f}",
                        }
                    )
                self._set_trace_tags(trace_tags)
        finally:
            self._safe_close()

        _log_system_aggregates(
            mlflow_mod=mlflow,
            response=response,
            quality=quality,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            cost_usd=cost,
        )

    # ------------------------------------------------------------------
    def _set_trace_tags(self, tags: dict[str, str]) -> None:
        if not self.trace_id or not self.enabled:
            return
        try:
            from mlflow import MlflowClient  # type: ignore

            client = MlflowClient()
            for key, value in tags.items():
                try:
                    client.set_trace_tag(self.trace_id, key, str(value))
                except Exception:  # noqa: BLE001
                    continue
        except Exception:  # noqa: BLE001
            pass

    # ------------------------------------------------------------------
    def _safe_close(self) -> None:
        if self._root_span_ctx is not None:
            try:
                self._root_span_ctx.__exit__(None, None, None)
            except Exception:  # noqa: BLE001
                pass
        self._root_span_ctx = None
        self._root_span = None
        if self._run_ctx is not None:
            try:
                self._run_ctx.__exit__(None, None, None)
            except Exception:  # noqa: BLE001
                pass
        self._run_ctx = None


# ---------------------------------------------------------------------------
def _log_system_aggregates(
    *,
    mlflow_mod,
    response,
    quality: Optional[QualityMetrics],
    prompt_tokens: int,
    completion_tokens: int,
    total_tokens: int,
    cost_usd: float,
) -> None:
    """Update the shared `system::vartalaap` run with cross-session totals."""
    system_run_id = _get_or_create_system_run(mlflow_mod)
    if not system_run_id:
        return

    with _SYSTEM_LOCK:
        _SYSTEM_COUNTERS["turns"] += 1
        _SYSTEM_COUNTERS["prompt_tokens"] += prompt_tokens
        _SYSTEM_COUNTERS["completion_tokens"] += completion_tokens
        _SYSTEM_COUNTERS["total_tokens"] += total_tokens
        _SYSTEM_COUNTERS["cost_usd"] += cost_usd
        _SYSTEM_COUNTERS["num_sources"] += len(response.sources)
        if response.tool_used == "guardrails":
            _SYSTEM_COUNTERS["guardrailed"] += 1
        if response.reflexion_iterations > 1:
            _SYSTEM_COUNTERS["reflexion_retries"] += 1
        if quality:
            _SYSTEM_COUNTERS["eval_context_relevance_sum"] += quality.context_relevance
            _SYSTEM_COUNTERS["eval_faithfulness_sum"] += quality.faithfulness
            _SYSTEM_COUNTERS["eval_answer_relevance_sum"] += quality.answer_relevance
            _SYSTEM_COUNTERS["eval_history_relevance_sum"] += quality.chat_history_relevance
            _SYSTEM_COUNTERS["eval_tone_sum"] += quality.tone_appropriateness
            _SYSTEM_COUNTERS["eval_toxicity_sum"] += quality.toxicity
            _SYSTEM_COUNTERS["eval_rag_score_sum"] += quality.rag_score
        step = int(_SYSTEM_COUNTERS["turns"])
        turns = max(1, step)
        payload: dict[str, float] = {
            "system.total_turns": float(step),
            "system.total_sessions": float(_SYSTEM_COUNTERS["sessions"]),
            "system.unique_users": float(len(_SESSION_UNIQUE_USERS)),
            "system.total_prompt_tokens": float(_SYSTEM_COUNTERS["prompt_tokens"]),
            "system.total_completion_tokens": float(_SYSTEM_COUNTERS["completion_tokens"]),
            "system.total_tokens": float(_SYSTEM_COUNTERS["total_tokens"]),
            "system.total_cost_usd": float(_SYSTEM_COUNTERS["cost_usd"]),
            "system.avg_cost_per_turn_usd": float(_SYSTEM_COUNTERS["cost_usd"]) / turns,
            "system.avg_tokens_per_turn": float(_SYSTEM_COUNTERS["total_tokens"]) / turns,
            "system.avg_sources_per_turn": float(_SYSTEM_COUNTERS["num_sources"]) / turns,
            "system.likes": float(_SYSTEM_COUNTERS["likes"]),
            "system.dislikes": float(_SYSTEM_COUNTERS["dislikes"]),
            "system.no_feedback": float(_SYSTEM_COUNTERS["no_feedback"]),
            "system.guardrailed": float(_SYSTEM_COUNTERS["guardrailed"]),
            "system.reflexion_retries": float(_SYSTEM_COUNTERS["reflexion_retries"]),
            "system.eval.avg_context_relevance": float(
                _SYSTEM_COUNTERS["eval_context_relevance_sum"]
            )
            / turns,
            "system.eval.avg_faithfulness": float(
                _SYSTEM_COUNTERS["eval_faithfulness_sum"]
            )
            / turns,
            "system.eval.avg_answer_relevance": float(
                _SYSTEM_COUNTERS["eval_answer_relevance_sum"]
            )
            / turns,
            "system.eval.avg_history_relevance": float(
                _SYSTEM_COUNTERS["eval_history_relevance_sum"]
            )
            / turns,
            "system.eval.avg_tone": float(_SYSTEM_COUNTERS["eval_tone_sum"]) / turns,
            "system.eval.avg_toxicity": float(_SYSTEM_COUNTERS["eval_toxicity_sum"])
            / turns,
            "system.eval.avg_rag_score": float(
                _SYSTEM_COUNTERS["eval_rag_score_sum"]
            )
            / turns,
        }

    try:
        with mlflow_mod.start_run(run_id=system_run_id):
            mlflow_mod.log_metrics(payload, step=step)
    except Exception:  # noqa: BLE001
        pass


# ---------------------------------------------------------------------------
def log_feedback(
    *,
    session_id: str,
    user_id: Optional[str],
    message_id: str,
    feedback: str,
    comment: Optional[str],
    parent_run_id: Optional[str],
    trace_id: Optional[str],
) -> Optional[str]:
    """Attach feedback to the existing turn trace (not a new one).

    - Sets `feedback`, `feedback_score` and `feedback_comment` tags on the
      trace so each trace row shows its own feedback in the Tags column.
    - Bumps `feedback_score` metric on the session run and the shared
      `system::vartalaap` run.
    """
    if not _try_init():
        return None
    try:
        import mlflow  # type: ignore
        from mlflow import MlflowClient  # type: ignore
    except Exception:  # noqa: BLE001
        return None

    settings = get_settings()
    if not settings.mlflow_enabled:
        return None

    score = {"up": 1.0, "down": -1.0, "none": 0.0}.get(feedback, 0.0)

    with _SESSIONS_LOCK:
        session_run_id = _SESSION_RUNS.get(session_id) or parent_run_id

    # 1. Tag the trace itself.
    if trace_id:
        try:
            client = MlflowClient()
            client.set_trace_tag(trace_id, "feedback", feedback)
            client.set_trace_tag(trace_id, "feedback_score", f"{score:.2f}")
            if comment:
                client.set_trace_tag(trace_id, "feedback_comment", comment[:500])
        except Exception:  # noqa: BLE001
            pass

    # 2. Log a metric on the parent session run.
    if session_run_id:
        try:
            with mlflow.start_run(run_id=session_run_id):
                mlflow.set_tag(f"feedback.{message_id[:8]}", feedback)
                mlflow.log_metric("feedback_score_last", score)
        except Exception:  # noqa: BLE001
            pass

    # 3. Update running system totals.
    with _SYSTEM_LOCK:
        if feedback == "up":
            _SYSTEM_COUNTERS["likes"] += 1
        elif feedback == "down":
            _SYSTEM_COUNTERS["dislikes"] += 1
        else:
            _SYSTEM_COUNTERS["no_feedback"] += 1
        step = int(_SYSTEM_COUNTERS["turns"])
        payload = {
            "system.likes": float(_SYSTEM_COUNTERS["likes"]),
            "system.dislikes": float(_SYSTEM_COUNTERS["dislikes"]),
            "system.no_feedback": float(_SYSTEM_COUNTERS["no_feedback"]),
            "system.like_ratio": float(_SYSTEM_COUNTERS["likes"])
            / max(1.0, float(_SYSTEM_COUNTERS["likes"] + _SYSTEM_COUNTERS["dislikes"])),
        }
    sys_run_id = _get_or_create_system_run(mlflow)
    if sys_run_id:
        try:
            with mlflow.start_run(run_id=sys_run_id):
                mlflow.log_metrics(payload, step=step)
        except Exception:  # noqa: BLE001
            pass

    return session_run_id
