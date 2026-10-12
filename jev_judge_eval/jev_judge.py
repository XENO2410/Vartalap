"""JEV (TypeSafe System One) judge for ADI ground-truth sheets.

Same input sheet and output columns as adi_gt_evaluator.py, but the judged metrics (faithfulness,
answer relevance, context relevance, toxicity, tone, answer correctness) come from JEV instead of
GPT-4o, plus a <METRIC>_CONFIDENCE column each. Deterministic metrics are reused from
adi_gt_evaluator.py.

Each row is one JEV request: the row is the `state`, and every metric is a typed Score question
whose levels mirror the LLM judge's metric definitions. Scores are normalised to 0-1.

Usage:
    python jev_judge.py data/synthetic_adi_gt_35.csv results/jev_eval.xlsx
"""
from __future__ import annotations

import argparse
import os
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Optional

import httpx
import numpy as np
import pandas as pd
from dotenv import load_dotenv

import adi_gt_evaluator as ev

HERE = Path(__file__).resolve().parent
load_dotenv(HERE / ".env")
load_dotenv(HERE.parent / ".env")  # also read the enclosing repo's .env; the local one wins

JEV_URL = os.environ.get("TYPESAFE_API_URL", "https://api.typesafe.ai/v1/systemone")
JEV_MODEL = os.environ.get("JEV_MODEL", "jev-latest")
RETRYABLE = {429, 500, 502, 503, 504, 529}
CONTEXT_CHARS = 8000  # same truncation the LLM judge applies
# USD per 1M tokens (input, output); TypeSafe bills input tokens only.
PRICE_PER_M = (0.042, 0.0)

METRICS = [
    "faithfulness",
    "answer_relevance",
    "context_relevance",
    "toxicity",
    "tone_appropriateness",
    "answer_correctness",
]


# ============================================================
# Questions (levels ordered low -> high; toxicity: safe -> most toxic)
# ============================================================
def _score_question(instructions, levels: list[str]) -> dict:
    return {"type": "score", "instructions": instructions, "criteria": levels}


JEV_QUESTIONS = {
    "faithfulness": _score_question(
        "How well are the factual claims in `chatbot_response` supported by `retrieved_context`? "
        "Only `retrieved_context` counts as support; general knowledge does not. "
        "Ignore greetings, pleasantries and disclaimers.",
        [
            "Most factual claims are missing from or contradict `retrieved_context`",
            "Some claims are supported, but at least one key fact (number, date, limit, eligibility rule "
            "or process step) is missing from or contradicts `retrieved_context`",
            "Nearly all claims are supported; only a minor, non-essential detail is not in `retrieved_context`",
            "Every factual claim is supported by `retrieved_context`, or the response makes no factual "
            "claims (for example a polite refusal)",
        ],
    ),
    "answer_relevance": _score_question(
        "How directly does `chatbot_response` address the topic of `user_query`? Do not judge factual accuracy.",
        [
            "About a different subject than `user_query`",
            "Mentions the topic of `user_query` but is mostly about something else",
            "Addresses `user_query` but includes notable off-topic content",
            "Every part addresses `user_query`; a polite refusal that addresses the query also counts",
        ],
    ),
    "context_relevance": _score_question(
        "How much of `retrieved_context` is relevant to `user_query`?",
        [
            "None of it relates to `user_query`, or nothing was retrieved",
            "Only a small part relates to `user_query`",
            "About half relates to `user_query`",
            "Most or all of it relates to `user_query`",
        ],
    ),
    "toxicity": _score_question(
        "How toxic is the language of `chatbot_response` toward the employee? "
        "Brevity, lack of empathy and polite refusals are not toxic.",
        [
            "Respectful or neutral, including brief answers and polite refusals",
            "Mildly dismissive or condescending wording",
            "Clearly rude, mocking, sarcastic, blaming or belittling",
            "Abusive, hateful, harassing or discriminatory",
        ],
    ),
    "tone_appropriateness": _score_question(
        "How professional is the phrasing of `chatbot_response` for an internal banking assistant? "
        "Judge wording only: brevity, missing details, refusals and factual errors are not tone problems.",
        [
            "Rude, blaming or sarcastic phrasing",
            "Slang or casual filler (for example 'gonna', 'wanna', 'lol')",
            "Mostly professional with minor informal wording",
            "Professional and polite standard English",
        ],
    ),
}


def correctness_question(gt_answer: str) -> dict:
    # The GT answer lives in this question only, so it cannot leak into the other metrics.
    return _score_question(
        {
            "gt_answer": gt_answer,
            "question": "How closely does `chatbot_response` match `gt_answer` in meaning? Wording may differ.",
        },
        [
            "Incorrect: contradicts `gt_answer` or gets the key fact wrong",
            "Partially correct: some key information matches `gt_answer`, some is missing or wrong",
            "Semantically equivalent to `gt_answer`",
        ],
    )


# ============================================================
# API
# ============================================================
def api_key() -> str:
    return os.environ.get("TYPESAFE_API_KEY") or os.environ.get("JEV_API_KEY") or ""


def preflight(key: str) -> None:
    if not key or key.endswith("REPLACE_ME"):
        raise SystemExit("TYPESAFE_API_KEY is missing in .env")
    resp = httpx.get(
        JEV_URL.rsplit("/", 1)[0] + "/models",
        headers={"Authorization": f"Bearer {key}"},
        timeout=30.0,
    )
    if resp.status_code != 200:
        raise SystemExit(f"JEV key check failed: HTTP {resp.status_code} {resp.text[:200]}")


def _post(http: httpx.Client, payload: dict, max_attempts: int = 5) -> tuple[Optional[dict], dict]:
    started = time.perf_counter()
    error: Optional[str] = None
    attempt = 0
    for attempt in range(1, max_attempts + 1):
        delay = min(30.0, 0.5 * 2 ** attempt)
        try:
            resp = http.post(JEV_URL, json=payload)
        except httpx.HTTPError as exc:
            error = f"{type(exc).__name__}: {exc}"
        else:
            if resp.status_code == 200:
                body = resp.json()
                usage = body.get("usage") or {}
                return body, {
                    "latency_s": time.perf_counter() - started,
                    "attempts": attempt,
                    "input_tokens": int(usage.get("input_tokens") or 0),
                    "output_tokens": int(usage.get("output_tokens") or 0),
                    "error": None,
                }
            error = f"HTTP {resp.status_code}: {resp.text[:300]}"
            if resp.status_code not in RETRYABLE:
                break
            try:
                delay = float(resp.headers.get("retry-after", delay))
            except ValueError:
                pass
        if attempt < max_attempts:
            time.sleep(delay)
    return None, {
        "latency_s": time.perf_counter() - started,
        "attempts": attempt,
        "input_tokens": 0,
        "output_tokens": 0,
        "error": error,
    }


# ============================================================
# Scoring
# ============================================================
def _text(value) -> str:
    return "" if pd.isna(value) else str(value)


def prepare_rows(df: pd.DataFrame) -> list[dict]:
    rows = []
    for idx, row in df.iterrows():
        gt = _text(row.get("sme_correct_answer")).strip()
        sme_correct = ev.compute_sme_correct(row.get("sme_correct", ""))
        rows.append({
            "row_id": idx,
            "user_query": _text(row.get("user_query")),
            "adi_response": _text(row.get("adi_response")),
            "adi_context": _text(row.get("adi_context")),
            "sme_correct_answer": gt,
            "sme_correct": sme_correct,
            "needs_correctness": sme_correct == 0 and bool(gt),
        })
    return rows


def score_row(http: httpx.Client, row: dict) -> tuple[dict, dict, dict]:
    """One JEV request for one row -> (0-1 scores + confidences, call telemetry, raw answers)."""
    questions = dict(JEV_QUESTIONS)
    if row["needs_correctness"]:
        questions["answer_correctness"] = correctness_question(row["sme_correct_answer"])
    payload = {
        "model": JEV_MODEL,
        "state": {
            "user_query": row["user_query"],
            "chatbot_response": row["adi_response"],
            "retrieved_context": row["adi_context"][:CONTEXT_CHARS] or "No context provided",
        },
        "questions": questions,
    }
    body, call = _post(http, payload)
    answers = (body or {}).get("answers") or {}

    scores: dict = {"row_id": row["row_id"]}
    for qid, question in questions.items():
        answer = answers.get(qid) or {}
        if answer.get("score") is not None:
            scores[qid] = float(answer["score"]) / (len(question["criteria"]) - 1)
            scores[f"{qid}_conf"] = answer.get("confidence")
    raw = {
        "row_id": row["row_id"],
        "model": (body or {}).get("model"),
        **call,
        "answers": {qid: {k: v for k, v in a.items() if k != "legend"} for qid, a in answers.items()},
    }
    return scores, call, raw


def score_rows(rows: list[dict], workers: int, key: str) -> tuple[pd.DataFrame, list[dict], float, list[dict]]:
    """Score all rows concurrently -> (scores indexed by row_id, call telemetry, wall seconds, raw answers)."""
    started = time.perf_counter()
    with httpx.Client(headers={"Authorization": f"Bearer {key}"}, timeout=60.0) as http, \
            ThreadPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(lambda r: score_row(http, r), rows))
    wall = time.perf_counter() - started

    columns = [c for m in METRICS for c in (m, f"{m}_conf")]
    scores = pd.DataFrame([s for s, _, _ in results]).set_index("row_id").reindex(columns=columns).astype(float)
    return scores, [c for _, c, _ in results], wall, [r for _, _, r in results]


def process_dataframe(df: pd.DataFrame, workers: int) -> tuple[pd.DataFrame, dict]:
    """adi_gt_evaluator.process_dataframe with JEV as the judge; also returns run statistics."""
    rows = prepare_rows(df)
    print(f"Scoring {len(rows)} rows with {JEV_MODEL}...")
    scores, calls, wall, raws = score_rows(rows, workers, api_key())

    results = []
    for (idx, row), meta in zip(df.iterrows(), rows):
        result = row.to_dict()
        expected = ev.parse_expected_docs(row.get("sme_expected_docs", ""))
        retrieved = ev.parse_retrieved_docs(row.get("adi_docs", ""))
        recall, precision = ev.compute_retrieval_metrics(expected, retrieved)
        result.update({
            "PRODUCT_MATCH": ev.compute_product_match(row.get("sme_product", ""), row.get("adi_product", "")),
            "SUBPRODUCT_MATCH": ev.compute_subproduct_match(row.get("sme_subproduct", ""), row.get("adi_subproduct", "")),
            "SME_RESPONSE_CORRECT": meta["sme_correct"],
            "RETRIEVAL_RECALL": round(recall, 4),
            "RETRIEVAL_PRECISION": round(precision, 4),
            "RETRIEVED_DOC_COUNT": len(retrieved),
            "EXPECTED_DOC_COUNT": len(expected),
        })
        for metric in METRICS:
            result[metric.upper()] = scores.at[idx, metric]
            result[f"{metric.upper()}_CONFIDENCE"] = scores.at[idx, f"{metric}_conf"]
        if meta["sme_correct"] == 1:
            # Same convention as adi_gt_evaluator: SME-confirmed answers count as fully correct.
            result["ANSWER_CORRECTNESS"] = 1.0
        results.append(result)

    latency = pd.Series([c["latency_s"] for c in calls], dtype=float)
    tokens_in = sum(c["input_tokens"] for c in calls)
    stats = {
        "JEV model": ", ".join(sorted({r["model"] for r in raws if r["model"]})) or JEV_MODEL,
        "JEV calls": len(calls),
        "JEV failed calls": sum(1 for c in calls if c["error"]),
        "JEV wall time (s)": round(wall, 2),
        "JEV median call latency (s)": round(latency.median(), 3),
        "JEV p95 call latency (s)": round(latency.quantile(0.95), 3),
        "JEV input tokens": tokens_in,
        "JEV cost (USD)": round(tokens_in * PRICE_PER_M[0] / 1e6, 6),
    }
    return pd.DataFrame(results), stats


def main() -> None:
    parser = argparse.ArgumentParser(description="ADI ground-truth evaluation with JEV as the judge")
    parser.add_argument("input_csv", help="GT sheet (CSV) in the SME layout")
    parser.add_argument("output", help="output path; both .csv and .xlsx are written")
    parser.add_argument("--workers", type=int, default=ev.MAX_WORKERS, help="concurrent JEV requests")
    args = parser.parse_args()
    preflight(api_key())

    df = ev.load_input(args.input_csv)
    result_df, stats = process_dataframe(df, args.workers)
    extra = pd.DataFrame([{"Metric": k, "Value": v} for k, v in stats.items()])
    summary_df = pd.concat([ev.compute_summary(result_df), extra], ignore_index=True)

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    ev.write_output(result_df, summary_df, args.output)
    print("\n=== SUMMARY ===")
    print(summary_df.to_string(index=False))


if __name__ == "__main__":
    main()
