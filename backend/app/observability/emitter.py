"""Central event emitter.

Every stage of the runtime funnels through `EventEmitter.emit(...)`. Today it
writes JSONL to a per-day file, optionally mirrors to stdout, and (when
`MLFLOW_ENABLED=true`) tees each event to the current MLflow span while the
supervisor wraps each pipeline stage in `emitter.span(...)`. The Kytee SDK
can be plugged in inside this single module without touching any call-sites.
"""
from __future__ import annotations

import json
import sys
import threading
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator, Optional

from ..config import get_settings
from ..schemas import MessageClass, MessageEnvelope, MessageTag
from .mlflow_sink import MLflowSink


_SETTINGS = get_settings()
_LOCK = threading.Lock()


def _today_partition() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


class EventEmitter:
    """Session-scoped emitter. One instance per request/turn."""

    def __init__(
        self,
        *,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        bubble: Optional[str] = None,
    ) -> None:
        self.session_id = session_id or f"sess_{uuid.uuid4().hex[:12]}"
        self.user_id = user_id or "anonymous"
        self.bubble = bubble
        self.events: list[MessageEnvelope] = []
        self._log_dir: Path = _SETTINGS.log_abs_dir
        self._log_dir.mkdir(parents=True, exist_ok=True)
        self.mlflow = MLflowSink(
            session_id=self.session_id,
            user_id=self.user_id,
            bubble=bubble,
        )

    # ------------------------------------------------------------------
    def start_turn(self, query: str) -> None:
        """Open the MLflow run for this turn (no-op if MLflow disabled)."""
        self.mlflow.start_turn(query=query)

    @property
    def mlflow_run_id(self) -> Optional[str]:
        return self.mlflow.run_id

    @property
    def mlflow_trace_id(self) -> Optional[str]:
        return self.mlflow.trace_id

    def finalize(self, response, *, quality=None, retrieval_scores=None) -> None:
        """Log rollup metrics + artifacts and close the MLflow run."""
        self.mlflow.finalize(
            response=response,
            events=self.events,
            quality=quality,
            retrieval_scores=retrieval_scores,
        )

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
        """Wrap a pipeline stage in an MLflow span."""
        with self.mlflow.span(
            name=name, kind=kind, inputs=inputs, attributes=attributes
        ) as span:
            yield span

    def set_span_outputs(self, outputs: dict[str, Any]) -> None:
        self.mlflow.set_current_outputs(outputs)

    def set_span_attributes(self, **attributes: Any) -> None:
        self.mlflow.set_current_attributes(attributes)

    def set_span_chat(
        self,
        *,
        messages: Optional[list[dict[str, Any]]] = None,
        input_tokens: Optional[int] = None,
        output_tokens: Optional[int] = None,
        model: Optional[str] = None,
    ) -> None:
        """Attach MLflow GenAI conventions to the currently active LLM span."""
        self.mlflow.set_current_chat(
            messages=messages,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            model=model,
        )

    def mark_span_error(self, message: str) -> None:
        self.mlflow.mark_current_error(message)

    # ------------------------------------------------------------------
    def emit(
        self,
        tag: MessageTag | str,
        *,
        content: Optional[str] = None,
        msg_class: MessageClass | str = MessageClass.SYSTEM,
        apiname: Optional[str] = None,
        use_case: Optional[str] = None,
        extra: Optional[dict[str, Any]] = None,
    ) -> MessageEnvelope:
        """Emit a single event conforming to the ADI message schema."""
        tag_value = tag.value if isinstance(tag, MessageTag) else str(tag)
        class_value = msg_class.value if isinstance(msg_class, MessageClass) else str(msg_class)

        envelope = MessageEnvelope(
            identifiersessionid=self.session_id,
            identifieruserid=self.user_id,
            messagetype=tag_value,
            apiname=apiname or "vartalaap.chat",
            content=content,
            msgcontent=content,
            additionalinfousecase=use_case,
            **{"class": class_value},
        )
        if extra:
            for key, value in extra.items():
                if value is None:
                    continue
                if not isinstance(value, str):
                    value = json.dumps(value, ensure_ascii=False, default=str)
                setattr(envelope, key, value)

        self.events.append(envelope)
        self._sink(envelope)
        self.mlflow.log_event(envelope)
        return envelope

    # ------------------------------------------------------------------
    def _sink(self, envelope: MessageEnvelope) -> None:
        payload = envelope.model_dump(by_alias=True, exclude_none=False)
        line = json.dumps(payload, ensure_ascii=False, default=str)
        log_path = self._log_dir / f"events-{_today_partition()}.jsonl"
        with _LOCK:
            with log_path.open("a", encoding="utf-8") as fh:
                fh.write(line + "\n")
            if _SETTINGS.observability_stdout:
                sys.stdout.write(f"[event] {envelope.messagetype} :: {envelope.identifiersessionid}\n")
                sys.stdout.flush()

    # ------------------------------------------------------------------
    def snapshot(self) -> list[MessageEnvelope]:
        return list(self.events)
