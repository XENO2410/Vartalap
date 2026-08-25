"""Cheap heuristic evaluators for RAG quality metrics.

These are best-effort proxies suitable for demo observability — mirrors the
metric tiles shown on the ADI dashboard (context relevance, faithfulness,
answer relevance, tone appropriateness, toxicity, chat history relevance,
composite RAG score). Ground-truth-free by design so they can be computed
inline for every turn.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable


_CITATION_RE = re.compile(r"\[S\d+\]")
_REFUSAL_PATTERNS = [
    "i don't have enough information",
    "i cannot help",
    "i can't help",
    "sorry, i can't",
    "unable to find",
    "contact the relevant helpdesk",
    "contact the appropriate helpdesk",
]
_TOXIC_WORDS = {
    "hate", "kill", "stupid", "idiot", "damn", "hell",
    "shut up", "moron", "worthless",
}
_POLITE_MARKERS = {
    "please", "thank", "kindly", "certainly",
    "here is", "here are", "you can", "you may",
}
_STOP = {
    "the", "a", "an", "is", "of", "and", "or", "in", "on", "to", "for",
    "with", "by", "at", "be", "as", "are", "was", "were", "this", "that",
    "it", "what", "how", "who", "why", "when", "which", "do", "does",
    "did", "i", "you", "we", "they", "he", "she", "not", "no", "yes",
}


@dataclass
class QualityMetrics:
    context_relevance: float
    faithfulness: float
    answer_relevance: float
    chat_history_relevance: float
    tone_appropriateness: float
    toxicity: float
    rag_score: float

    def to_metric_dict(self, prefix: str = "eval.") -> dict[str, float]:
        return {
            f"{prefix}context_relevance": self.context_relevance,
            f"{prefix}faithfulness": self.faithfulness,
            f"{prefix}answer_relevance": self.answer_relevance,
            f"{prefix}chat_history_relevance": self.chat_history_relevance,
            f"{prefix}tone_appropriateness": self.tone_appropriateness,
            f"{prefix}toxicity": self.toxicity,
            f"{prefix}rag_score": self.rag_score,
        }


def evaluate(
    *,
    query: str,
    answer: str,
    retrieval_scores: list[float],
    history_used: bool,
    tool_used: str,
) -> QualityMetrics:
    context_relevance = _context_relevance(retrieval_scores)
    faithfulness = _faithfulness(answer, tool_used)
    answer_relevance = _answer_relevance(query, answer)
    chat_history_relevance = _history_relevance(history_used, answer)
    tone_appropriateness = _tone(answer)
    toxicity = _toxicity(answer)
    rag_score = _composite(
        context_relevance=context_relevance,
        faithfulness=faithfulness,
        answer_relevance=answer_relevance,
        tone_appropriateness=tone_appropriateness,
        toxicity=toxicity,
    )
    return QualityMetrics(
        context_relevance=context_relevance,
        faithfulness=faithfulness,
        answer_relevance=answer_relevance,
        chat_history_relevance=chat_history_relevance,
        tone_appropriateness=tone_appropriateness,
        toxicity=toxicity,
        rag_score=rag_score,
    )


# ---------------------------------------------------------------------------
def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def _context_relevance(scores: Iterable[float]) -> float:
    values = [max(0.0, float(s)) for s in scores if s is not None]
    if not values:
        return 0.0
    top = values[: min(5, len(values))]
    return round(_clamp(sum(top) / len(top)), 4)


def _faithfulness(answer: str, tool_used: str) -> float:
    if tool_used == "guardrails":
        return 1.0
    if not answer:
        return 0.0
    text = answer.lower()
    if any(p in text for p in _REFUSAL_PATTERNS):
        return 0.7
    citations = len(_CITATION_RE.findall(answer))
    if citations:
        return round(_clamp(0.55 + 0.1 * citations), 4)
    return 0.4 if tool_used == "kb" else 0.75


def _answer_relevance(query: str, answer: str) -> float:
    if not answer or not query:
        return 0.0
    q_words = _tokens(query)
    a_words = _tokens(answer)
    if not q_words:
        return 0.5
    overlap = len(q_words & a_words) / len(q_words)
    return round(_clamp(0.5 + 0.5 * overlap), 4)


def _history_relevance(history_used: bool, answer: str) -> float:
    if not history_used:
        return 0.0
    text = (answer or "").lower()
    if "as mentioned" in text or "as we discussed" in text or "as noted" in text:
        return 0.9
    return 0.6


def _tone(answer: str) -> float:
    if not answer:
        return 0.5
    text = answer.lower()
    hits = sum(1 for m in _POLITE_MARKERS if m in text)
    return round(_clamp(0.7 + 0.08 * hits), 4)


def _toxicity(answer: str) -> float:
    if not answer:
        return 0.0
    text = answer.lower()
    hits = sum(1 for w in _TOXIC_WORDS if w in text)
    return round(_clamp(hits * 0.25), 4)


def _composite(
    *,
    context_relevance: float,
    faithfulness: float,
    answer_relevance: float,
    tone_appropriateness: float,
    toxicity: float,
) -> float:
    base = (
        context_relevance * 0.25
        + faithfulness * 0.30
        + answer_relevance * 0.25
        + tone_appropriateness * 0.20
    )
    return round(_clamp(base * (1.0 - toxicity)), 4)


def _tokens(text: str) -> set[str]:
    words = re.findall(r"\w+", text.lower())
    return {w for w in words if len(w) > 2 and w not in _STOP}
