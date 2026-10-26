"""Additional evaluation arms for controlled comparisons.

- Matched-rubric GPT: GPT selects a discrete rubric level for each JEV question.
- Hybrid: GPT extracts claims/statements; JEV classifies extracted items and scores the remaining metrics.

These arms use the same synthetic or SME reference inputs as the comparison harness. They do not
make decisions in production. No credentials are printed.
"""
from __future__ import annotations

import json
import math
import time
from concurrent.futures import ThreadPoolExecutor

import httpx
import numpy as np
import pandas as pd

import adi_gt_evaluator as ev
import jev_judge as jj
from evaluation_policy import combined_correctness


MATCHED_SYSTEM = """You are an evaluation judge. The input contains a test case and typed rubric questions. Each score question has ordered rubric levels indexed from 0. For each question independently, return a probability for every level, keyed by its zero-based index; probabilities must be between 0 and 1 and sum to 1. Use the provided state only. Return JSON: {\"answers\": {\"question_id\": {\"probabilities\": {\"0\": 0.2, \"1\": 0.8}}}}. Do not omit a level. Do not return a single selected label."""
EXTRACT_SYSTEM = """Extract evaluation units from the supplied response only. Return JSON with:
- claims: atomic factual claims, one independently verifiable fact per item; omit greetings and opinions
- answer_statements: atomic statements, one idea per item, including non-factual advice/refusals
Do not judge truth or relevance. Do not use outside knowledge. If none, return an empty list."""

_TONE_LEVELS = jj.JEV_QUESTIONS["tone_appropriateness"]["criteria"]
_TOXICITY_LEVELS = jj.JEV_QUESTIONS["toxicity"]["criteria"]
_SEMANTIC_LEVELS = jj.correctness_questions("gt_answer")["semantic_similarity"]["criteria"]
RAGAS_SYSTEM = (
    "You are a RAG evaluation judge following the ADI framework definitions. "
    "DECOMPOSE first, then judge each unit — never score the whole response in one step.\n"
    "Tone levels (0..3, same rubric as the reference judge): " + json.dumps(_TONE_LEVELS) + "\n"
    "Toxicity levels (0..3, same rubric as the reference judge): " + json.dumps(_TOXICITY_LEVELS) + "\n"
    "Semantic similarity vs the reference answer (0..3): " + json.dumps(_SEMANTIC_LEVELS) + "\n"
    'Return JSON with exactly: claims: [{"text": str, "supported_by_context": bool, '
    '"supported_by_reference": bool}], reference_claims: [{"text": str, "covered_by_response": bool}], '
    'answer_statements: [{"text": str, "relevant_to_query": bool}], '
    'chunk_verdicts: [{"index": int, "relevant_to_query": bool}], tone_level: int, '
    "toxicity_level: int, semantic_level: int. "
    "Judge claim support against retrieved_context only (no outside knowledge) and against the "
    "reference answer where one is provided. If no reference answer is provided, return "
    "reference_claims as [] and set every supported_by_reference to false."
)

METRICS = [
    "faithfulness", "answer_relevance", "context_relevance", "toxicity", "tone_appropriateness",
    "factual_precision", "factual_recall", "factual_correctness", "semantic_similarity", "answer_correctness",
]


def _questions_for_row(row: dict) -> dict[str, dict]:
    questions = dict(jj.JEV_QUESTIONS)
    if row.get("reference_answer"):
        questions.update(jj.correctness_questions(row["reference_answer"]))
    return questions


def _state_for_row(row: dict) -> dict:
    """Judge-visible state for one row: full fields, no truncation, with history."""
    return {
        "user_query": row["user_query"],
        "chatbot_response": row["adi_response"],
        "retrieved_context": row["adi_context"] or "No context provided",
        "retrieved_context_chunks": row.get("adi_chunks") or [],
        "prior_conversation": row.get("prior_conversation") or [],
    }


def _model_for_row(row: dict, model: str) -> tuple[dict, list[dict], dict]:
    client = ev._client()
    questions = _questions_for_row(row)
    state = _state_for_row(row)
    started = time.perf_counter()
    error = None
    response = None
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": MATCHED_SYSTEM},
                {"role": "user", "content": json.dumps({"state": state, "questions": questions}, ensure_ascii=False)},
            ],
            temperature=0,
            max_tokens=900,
            response_format={"type": "json_object"},
        )
        parsed = ev.parse_llm_response(response.choices[0].message.content or "")
    except Exception as exc:  # SDK retry policy applies; failure is retained as missing.
        parsed = {}
        error = f"{type(exc).__name__}: {str(exc)[:200]}"
    usage = getattr(response, "usage", None)
    call = {
        "latency_s": time.perf_counter() - started,
        "attempts": 1,
        "input_tokens": getattr(usage, "prompt_tokens", 0) or 0,
        "output_tokens": getattr(usage, "completion_tokens", 0) or 0,
        "error": error,
        "batch_rows": 1,
        "model": model,
    }
    scores = {"row_id": row["row_id"]}
    out_of_range = 0
    answers = parsed.get("answers") or {}
    for qid, question in questions.items():
        answer = answers.get(qid) or {}
        probabilities = answer.get("probabilities")
        try:
            if isinstance(probabilities, dict):
                distribution = [float(probabilities[str(i)]) for i in range(len(question["criteria"]))]
            elif isinstance(probabilities, list):
                distribution = [float(value) for value in probabilities]
            else:
                continue
        except (TypeError, ValueError, KeyError):
            continue
        top = len(question["criteria"]) - 1
        if len(distribution) != top + 1 or any(value < 0 or value > 1 for value in distribution):
            out_of_range += 1
            continue
        total = sum(distribution)
        if total <= 0 or abs(total - 1) > 0.05:
            out_of_range += 1
            continue
        distribution = [value / total for value in distribution]
        scores[qid] = sum(index * value for index, value in enumerate(distribution)) / top
    _derive_correctness(scores)
    raw = {"row_id": row["row_id"], "model": model, "out_of_range_scores": out_of_range, **call, "answers": answers}
    return scores, [call], raw


def _derive_correctness(scores: dict) -> None:
    precision = scores.get("factual_precision", np.nan)
    recall = scores.get("factual_recall", np.nan)
    semantic = scores.get("semantic_similarity", np.nan)
    if np.isfinite(precision) and np.isfinite(recall):
        factual = 0.0 if precision + recall == 0 else 2 * precision * recall / (precision + recall)
        scores["factual_correctness"] = factual
        if np.isfinite(semantic):
            scores["answer_correctness"] = combined_correctness(factual, semantic)


def run_matched_gpt(rows: list[dict], workers: int, model: str) -> tuple[pd.DataFrame, list[dict], float, list[dict], int]:
    started = time.perf_counter()
    with ThreadPoolExecutor(max_workers=workers) as pool:
        scored = list(pool.map(lambda row: _model_for_row(row, model), rows))
    wall = time.perf_counter() - started
    frame = pd.DataFrame([item[0] for item in scored]).set_index("row_id")
    calls = [call for _, calls, _ in scored for call in calls]
    raw = [result for _, _, result in scored]
    columns = [column for metric in METRICS for column in (metric, f"{metric}_conf")]
    return frame.reindex(columns=columns).astype(float), calls, wall, raw, sum(item.get("out_of_range_scores", 0) for item in raw)


# ============================================================
# RAGAS-style arm: our framework info, RAGAS-inspired decomposition
# ============================================================
def _ragas_user_prompt(row: dict) -> str:
    return json.dumps(
        {
            "state": _state_for_row(row),
            "reference_answer": row.get("reference_answer") or "",
        },
        ensure_ascii=False,
    )


def _flag_ratio(units: list[dict], flag: str) -> float:
    if not units:
        return float("nan")
    return sum(1 for unit in units if bool(unit.get(flag))) / len(units)


def _normalize_level(value: object, top: int = 3) -> tuple[float, bool]:
    """Normalize a rubric level to 0-1; second element flags out-of-range input."""
    try:
        level = int(value)
    except (TypeError, ValueError):
        return float("nan"), True
    if level < 0 or level > top:
        return float("nan"), True
    return level / top, False


def _ragas_scores_from(parsed: dict, row: dict) -> tuple[dict, int]:
    """Framework scores from the RAGAS-style decomposition output (pure, testable)."""
    claims = [
        c for c in parsed.get("claims") or []
        if isinstance(c, dict) and str(c.get("text", "")).strip()
    ]
    ref_claims = [
        c for c in parsed.get("reference_claims") or []
        if isinstance(c, dict) and str(c.get("text", "")).strip()
    ]
    statements = [
        s for s in parsed.get("answer_statements") or []
        if isinstance(s, dict) and str(s.get("text", "")).strip()
    ]
    chunk_verdicts = parsed.get("chunk_verdicts") or []
    chunks = row.get("adi_chunks") or []
    out_of_range = 0

    scores: dict = {"row_id": row["row_id"]}
    # Generation metrics: unit ratios, same 0-1 scale as the other arms.
    scores["faithfulness"] = _flag_ratio(claims, "supported_by_context")
    if not claims:
        scores["faithfulness"] = 1.0  # no factual claims = fully grounded (JEV convention)
    scores["answer_relevance"] = _flag_ratio(statements, "relevant_to_query")
    if not statements:
        scores["answer_relevance"] = 0.0
    relevant_chunks = set()
    for verdict in chunk_verdicts:
        if not isinstance(verdict, dict) or not bool(verdict.get("relevant_to_query")):
            continue
        try:
            relevant_chunks.add(int(verdict["index"]))
        except (TypeError, ValueError):
            out_of_range += 1
    scores["context_relevance"] = len(relevant_chunks) / len(chunks) if chunks else 0.0
    # Correctness components: claim-level overlap with the reference + graded semantics.
    scores["factual_precision"] = _flag_ratio(claims, "supported_by_reference")
    if not claims:
        scores["factual_precision"] = 0.0
    scores["factual_recall"] = _flag_ratio(ref_claims, "covered_by_response")  # NaN without reference
    precision = scores["factual_precision"]
    recall = scores["factual_recall"]
    if np.isfinite(precision) and np.isfinite(recall):
        scores["factual_correctness"] = (
            0.0 if precision + recall == 0
            else 2 * precision * recall / (precision + recall)
        )
    else:
        scores["factual_correctness"] = np.nan
    semantic, bad = _normalize_level(parsed.get("semantic_level"))
    out_of_range += int(bad)
    scores["semantic_similarity"] = semantic
    if np.isfinite(scores["factual_correctness"]) and np.isfinite(semantic):
        scores["answer_correctness"] = combined_correctness(scores["factual_correctness"], semantic)
    else:
        scores["answer_correctness"] = np.nan
    tone, bad = _normalize_level(parsed.get("tone_level"))
    out_of_range += int(bad)
    toxicity, bad = _normalize_level(parsed.get("toxicity_level"))
    out_of_range += int(bad)
    scores["tone_appropriateness"] = tone
    scores["toxicity"] = toxicity
    for metric in METRICS:
        scores.setdefault(metric, np.nan)
        scores.setdefault(f"{metric}_conf", np.nan)
    return scores, out_of_range


def _ragas_row(row: dict, model: str) -> tuple[dict, list[dict], dict]:
    client = ev._client()
    started = time.perf_counter()
    error = None
    response = None
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": RAGAS_SYSTEM},
                {"role": "user", "content": _ragas_user_prompt(row)},
            ],
            temperature=0,
            max_tokens=1200,
            response_format={"type": "json_object"},
        )
        parsed = ev.parse_llm_response(response.choices[0].message.content or "")
    except Exception as exc:  # SDK retry policy applies; failure is retained as missing.
        parsed = {}
        error = f"{type(exc).__name__}: {str(exc)[:200]}"
    usage = getattr(response, "usage", None)
    call = {
        "latency_s": time.perf_counter() - started,
        "attempts": 1,
        "input_tokens": getattr(usage, "prompt_tokens", 0) or 0,
        "output_tokens": getattr(usage, "completion_tokens", 0) or 0,
        "error": error,
        "batch_rows": 1,
        "model": model,
    }
    if parsed:
        scores, out_of_range = _ragas_scores_from(parsed, row)
    else:
        scores, out_of_range = {"row_id": row["row_id"]}, 0
    raw = {"row_id": row["row_id"], "model": model, "out_of_range_scores": out_of_range, **call, "answers": parsed}
    return scores, [call], raw


def run_ragas_gpt(rows: list[dict], workers: int, model: str) -> tuple[pd.DataFrame, list[dict], float, list[dict], int]:
    started = time.perf_counter()
    with ThreadPoolExecutor(max_workers=workers) as pool:
        scored = list(pool.map(lambda row: _ragas_row(row, model), rows))
    wall = time.perf_counter() - started
    frame = pd.DataFrame([item[0] for item in scored]).set_index("row_id")
    calls = [call for _, calls, _ in scored for call in calls]
    raw = [result for _, _, result in scored]
    columns = [column for metric in METRICS for column in (metric, f"{metric}_conf")]
    return frame.reindex(columns=columns).astype(float), calls, wall, raw, sum(item.get("out_of_range_scores", 0) for item in raw)


def _extract_items(row: dict) -> tuple[dict, dict]:
    client = ev._client()
    started = time.perf_counter()
    error = None
    response = None
    try:
        response = client.chat.completions.create(
            model=ev.JUDGE_MODEL,
            messages=[
                {"role": "system", "content": EXTRACT_SYSTEM},
                {"role": "user", "content": json.dumps({"user_query": row["user_query"], "response": row["adi_response"]}, ensure_ascii=False)},
            ],
            temperature=0,
            max_tokens=700,
            response_format={"type": "json_object"},
        )
        parsed = ev.parse_llm_response(response.choices[0].message.content or "")
    except Exception as exc:
        parsed = {}
        error = f"{type(exc).__name__}: {str(exc)[:200]}"
    usage = getattr(response, "usage", None)
    call = {
        "latency_s": time.perf_counter() - started,
        "attempts": 1,
        "input_tokens": getattr(usage, "prompt_tokens", 0) or 0,
        "output_tokens": getattr(usage, "completion_tokens", 0) or 0,
        "error": error,
        "batch_rows": 1,
        "stage": "extract",
        "model": ev.JUDGE_MODEL,
    }
    return parsed, call


def _hybrid_row(http: httpx.Client, row: dict) -> tuple[dict, list[dict], dict]:
    extracted, extract_call = _extract_items(row)
    claims = extracted.get("claims") or []
    statements = extracted.get("answer_statements") or []
    chunks = row.get("adi_chunks") or []
    questions: dict[str, dict] = {}
    for index, claim in enumerate(claims):
        questions[f"claim_{index}"] = {
            "type": "noul",
            "instructions": {"claim": str(claim), "question": "Is this claim supported by retrieved_context?"},
            "criteria": {"true": "Directly supported or entailed by retrieved_context", "false": "Absent from or contradictory to retrieved_context"},
        }
    for index, statement in enumerate(statements):
        questions[f"statement_{index}"] = {
            "type": "noul",
            "instructions": {"statement": str(statement), "question": "Does this statement directly address user_query? Ignore factual correctness."},
            "criteria": {"true": "Directly on the query topic", "false": "Off topic or tangent"},
        }
    for index, chunk in enumerate(chunks):
        questions[f"chunk_{index}"] = {
            "type": "noul",
            "instructions": {"chunk": str(chunk), "question": "Is this retrieved chunk useful for answering user_query?"},
            "criteria": {"true": "Relevant information useful to answer the query", "false": "Irrelevant or noise"},
        }
    questions.update({"toxicity": jj.JEV_QUESTIONS["toxicity"], "tone_appropriateness": jj.JEV_QUESTIONS["tone_appropriateness"]})
    if row.get("reference_answer"):
        questions.update(jj.correctness_questions(row["reference_answer"]))
    payload = {
        "model": jj.JEV_MODEL,
        "state": _state_for_row(row),
        "questions": questions,
    }
    body, decision_call = jj._post(http, payload)
    decision_call["model"] = jj.JEV_MODEL
    answers = (body or {}).get("answers") or {}
    supported = [answers.get(f"claim_{i}", {}).get("noul") for i in range(len(claims))]
    relevant = [answers.get(f"statement_{i}", {}).get("noul") for i in range(len(statements))]
    context_relevant = [answers.get(f"chunk_{i}", {}).get("noul") for i in range(len(chunks))]
    scores = {"row_id": row["row_id"]}
    scores["faithfulness"] = float(np.mean(supported)) if supported and all(x is not None for x in supported) else (1.0 if not claims else np.nan)
    scores["answer_relevance"] = float(np.mean(relevant)) if relevant and all(x is not None for x in relevant) else (0.0 if not statements else np.nan)
    scores["context_relevance"] = float(np.mean(context_relevant)) if context_relevant and all(x is not None for x in context_relevant) else (0.0 if not chunks else np.nan)
    for metric in ("toxicity", "tone_appropriateness", "factual_precision", "factual_recall", "semantic_similarity"):
        question = questions.get(metric)
        answer = answers.get(metric) or {}
        if question and answer.get("score") is not None:
            scores[metric] = float(answer["score"]) / (len(question["criteria"]) - 1)
            scores[f"{metric}_conf"] = answer.get("confidence")
    _derive_correctness(scores)
    raw = {
        "row_id": row["row_id"], "model": (body or {}).get("model"),
        "claims": claims, "answer_statements": statements,
        "answers": {key: {k: v for k, v in value.items() if k != "legend"} for key, value in answers.items()},
    }
    return scores, [extract_call, decision_call], raw


def run_hybrid(rows: list[dict], workers: int, api_key: str) -> tuple[pd.DataFrame, list[dict], float, list[dict], int]:
    started = time.perf_counter()
    with httpx.Client(headers={"Authorization": f"Bearer {api_key}"}, timeout=60.0) as http, \
            ThreadPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(lambda row: _hybrid_row(http, row), rows))
    wall = time.perf_counter() - started
    scores = pd.DataFrame([score for score, _, _ in results]).set_index("row_id")
    calls = [call for _, row_calls, _ in results for call in row_calls]
    raw = [item for _, _, item in results]
    columns = [column for metric in METRICS for column in (metric, f"{metric}_conf")]
    return scores.reindex(columns=columns).astype(float), calls, wall, raw, 0
