"""Reflexion AI Agent — reviews the draft answer and, if invalid, refines the
query for a follow-up iteration (doc §7.2, §7.3)."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Optional

from ..config import get_settings
from ..llm import LLMClient, LLMResponse, token_info
from ..observability import EventEmitter
from ..schemas import MessageClass, MessageTag


_REVIEW_SYSTEM = (
    "You are the Reflexion reviewer. Given a user question and a candidate "
    "answer, judge whether the answer is grounded, factual, non-refusing, "
    "and directly addresses the question. Respond ONLY with compact JSON of "
    'the form {"valid": true|false, "score": 0..1, "reason": "...", '
    '"refined_query": "..."} where refined_query is a rewritten query that '
    "should retrieve better context if valid is false."
)


@dataclass
class ReflexionVerdict:
    valid: bool
    score: float
    reason: str
    refined_query: Optional[str]
    model: str
    token_info_json: str


class ReflexionReviewer:
    def __init__(self, llm: Optional[LLMClient] = None) -> None:
        self.settings = get_settings()
        self.llm = llm or LLMClient()

    def review(
        self,
        *,
        question: str,
        answer: str,
        emitter: EventEmitter,
        iteration: int,
    ) -> ReflexionVerdict:
        payload = f"QUESTION:\n{question}\n\nCANDIDATE ANSWER:\n{answer}"
        emitter.emit(
            MessageTag.PROMPT_BUILDER_REFINE_QUERY_RESPONSE,
            content=payload,
            msg_class=MessageClass.SYSTEM,
            apiname="vartalaap.reflexion",
            extra={
                "additionalinfotags": json.dumps({"iteration": iteration}),
                "additionalinfomodel": self.settings.llm_model,
            },
        )
        # NOTE: we intentionally do NOT pass response_format={"type": "json_object"}
        # here — many OpenRouter models don't accept it. The system prompt asks
        # for compact JSON and `_parse_verdict` regex-extracts the object either way.
        resp: LLMResponse = self.llm.chat(
            system=_REVIEW_SYSTEM,
            user=payload,
            temperature=0.0,
            max_tokens=250,
        )
        emitter.emit(
            MessageTag.LLM_REFINE_QUERY_RESPONSE,
            content=resp.content,
            msg_class=MessageClass.RESPONSE,
            apiname="vartalaap.reflexion",
            extra={
                "additionalinfotokeninfo": token_info(resp),
                "additionalinfomodel": resp.model,
            },
        )
        # Feed the same chat trio to MLflow's LLM span so token / model
        # aggregates roll up correctly on the Reflexion iteration too.
        emitter.set_span_chat(
            messages=[
                {"role": "system", "content": _REVIEW_SYSTEM},
                {"role": "user", "content": payload},
                {"role": "assistant", "content": resp.content},
            ],
            input_tokens=resp.prompt_tokens,
            output_tokens=resp.completion_tokens,
            model=resp.model,
        )
        verdict = _parse_verdict(resp.content, fallback_query=question)
        return ReflexionVerdict(
            valid=verdict["valid"],
            score=verdict["score"],
            reason=verdict["reason"],
            refined_query=verdict["refined_query"],
            model=resp.model,
            token_info_json=token_info(resp),
        )


def _parse_verdict(text: str, *, fallback_query: str) -> dict:
    text = (text or "").strip()
    match = re.search(r"\{.*\}", text, re.DOTALL)
    raw = match.group(0) if match else "{}"
    try:
        data = json.loads(raw)
    except Exception:  # noqa: BLE001
        data = {}
    return {
        "valid": bool(data.get("valid", True)),
        "score": float(data.get("score", 0.8) or 0.0),
        "reason": str(data.get("reason", "")),
        "refined_query": str(data.get("refined_query") or fallback_query),
    }
