"""Metric contract for the ADI RAG evaluation framework.

This module owns score bands, binary compliance decisions, context chunk parsing,
and deterministic document-ID precision/recall. LLM-derived values are estimates;
these rules classify them but do not make them ground truth.
"""
from __future__ import annotations

import json
import math
import re
from typing import Optional

METRIC_THRESHOLDS: dict[str, dict[str, float]] = {
    "faithfulness": {"pass": 0.70, "review": 0.40},
    "answer_relevance": {"pass": 0.70, "review": 0.40},
    "answer_correctness": {"pass": 0.80, "review": 0.50},
    "context_relevance": {"pass": 0.70, "review": 0.40},
}
BINARY_SCORE_CUTOFF = 0.50
AGGREGATE_RATES: dict[str, dict[str, float]] = {
    "tone_appropriateness": {"pass": 0.95, "review": 0.90},
    "toxicity": {"pass": 1.00, "review": 0.95},
}
DECISION_POLICY = {
    "stage_1": "UAT/Pre-Production metric gates before deployment",
    "stage_2": "T-1 or near-real-time aggregate monitoring after deployment",
    "decision_levels": ["query", "sub-product", "product", "platform"],
    "approval": "Business, Data Science, IT, Risk and Application owners approve use-specific gates",
    "automation": "No automated production action is authorized by this evaluation policy alone",
}
DEFERRED_FRAMEWORK_METRICS = {
    "context_precision": "Requires ordered chunk-level relevance labels and a rank-aware calculation.",
    "context_recall": "Requires independently labelled reference contexts or complete reference-answer claims.",
    "document_deduplication": "Requires stable normalized document IDs per retrieved chunk.",
    "chunk_deduplication": "Requires stable chunk IDs or normalized document-and-excerpt pairs.",
    "ragas_composite": "Deferred until Context Precision and Context Recall have validated implementations and zero handling is approved.",
}


def framework_status(metric: str, value: object) -> str:
    """Return pass/review/fail using the framework's score bands.

    Tone is compliant when score >= the explicitly configurable binary cutoff.
    Toxicity is non-toxic when score < that cutoff. Aggregate rate bands are
    applied separately to the percentage of compliant/non-toxic rows.
    """
    try:
        score = float(value)
    except (TypeError, ValueError):
        return "not_evaluated"
    if not math.isfinite(score):
        return "not_evaluated"
    if metric == "tone_appropriateness":
        return "pass" if score >= BINARY_SCORE_CUTOFF else "fail"
    if metric == "toxicity":
        return "fail" if score >= BINARY_SCORE_CUTOFF else "pass"
    bands = METRIC_THRESHOLDS.get(metric)
    if bands is None:
        return "not_evaluated"
    if score >= bands["pass"]:
        return "pass"
    if score >= bands["review"]:
        return "review"
    return "fail"


def aggregate_rate_status(metric: str, rate: object) -> str:
    """Classify aggregate tone-compliance or non-toxicity rate."""
    try:
        value = float(rate)
    except (TypeError, ValueError):
        return "not_evaluated"
    if not math.isfinite(value):
        return "not_evaluated"
    bands = AGGREGATE_RATES.get(metric)
    if bands is None:
        return "not_evaluated"
    if value >= bands["pass"]:
        return "pass"
    if value >= bands["review"]:
        return "review"
    return "fail"


def combined_correctness(factual_correctness: object, semantic_similarity: object) -> float:
    """Framework Answer Correctness = 75% factual + 25% semantic similarity."""
    factual = float(factual_correctness)
    semantic = float(semantic_similarity)
    if not (math.isfinite(factual) and math.isfinite(semantic)):
        return float("nan")
    return 0.75 * min(1.0, max(0.0, factual)) + 0.25 * min(1.0, max(0.0, semantic))


def normalize_document_id(value: object) -> str:
    """Normalize an identifier for exact ID matching, not fuzzy semantic matching."""
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip().casefold()


def document_precision_recall(
    expected: list[str], retrieved: list[str]
) -> tuple[Optional[float], Optional[float]]:
    """Compute exact normalized document-ID precision and recall.

    Returns (None, None) when the query has no reference document labels;
    missing reference data is not treated as a perfect score.
    """
    expected_ids = {normalize_document_id(item) for item in expected if normalize_document_id(item)}
    retrieved_ids = [normalize_document_id(item) for item in retrieved if normalize_document_id(item)]
    if not expected_ids:
        return None, None
    if not retrieved_ids:
        return 0.0, 0.0
    retrieved_set = set(retrieved_ids)
    relevant_retrieved = sum(item in expected_ids for item in retrieved_ids)
    relevant_expected_retrieved = len(expected_ids & retrieved_set)
    return relevant_retrieved / len(retrieved_ids), relevant_expected_retrieved / len(expected_ids)


def parse_prior_conversation(value: object) -> list[dict]:
    """Parse serialized prior turns into [{role, content}, ...]; empty when absent.

    Malformed or placeholder values return [] rather than raising, so a broken
    history cell cannot take down a whole benchmark run.
    """
    if value is None:
        return []
    text = str(value).strip()
    if not text or text.casefold() in {"nan", "none", "null", "[]", "no history"}:
        return []
    try:
        parsed = json.loads(text)
    except (TypeError, ValueError, json.JSONDecodeError):
        return []
    if not isinstance(parsed, list):
        return []
    turns = []
    for item in parsed:
        if isinstance(item, dict) and item.get("content"):
            turns.append(
                {"role": str(item.get("role") or "user"), "content": str(item["content"])}
            )
    return turns


def parse_context_chunks(explicit_json: object, combined_context: object) -> list[str]:
    """Get retrieved chunks from an explicit JSON list or a marked/paragraph text field.

    If the source data does not preserve chunk boundaries, paragraph splitting is
    a documented approximation and should not be presented as exact chunk-level truth.
    """
    if explicit_json is not None:
        try:
            parsed = json.loads(str(explicit_json))
            if isinstance(parsed, list):
                chunks = [str(item).strip() for item in parsed if str(item).strip()]
                if chunks:
                    return chunks
        except (TypeError, ValueError, json.JSONDecodeError):
            pass
    text = "" if combined_context is None else str(combined_context).strip()
    if not text or text.casefold() in {"nan", "none", "null", "no context provided"}:
        return []
    marked = re.split(r"(?=\[(?:Doc|API|Text2SQL|FAQ):)", text)
    if len(marked) > 1:
        return [item.strip() for item in marked if item.strip()]
    return [item.strip() for item in re.split(r"\n\s*\n", text) if item.strip()]
