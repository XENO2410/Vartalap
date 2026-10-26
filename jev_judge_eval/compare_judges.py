"""JEV (TypeSafe System One) vs the GPT-4o LLM-as-a-judge in adi_gt_evaluator.py.

Both judges score the same rows on the same metrics. The LLM judge is adi_gt_evaluator's own
pipeline, unchanged (5 rows per GPT-4o call). JEV (jev_judge.py) gets one request per row with one
typed Score question per metric, written to mirror the LLM judge's metric definitions. Both run at
the same concurrency.

Compared: accuracy vs designer gold labels and vs SME Yes/No, judge-vs-judge agreement, latency,
throughput, tokens, cost, reliability, run-to-run consistency and JEV confidence.

Usage:
    python compare_judges.py
    python compare_judges.py --input real_gt.csv --gold none --repeats 1
"""
from __future__ import annotations

import argparse
import importlib.util
import itertools
import json
import time
import warnings
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr
from sklearn.metrics import (
    accuracy_score,
    brier_score_loss,
    cohen_kappa_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

import adi_gt_evaluator as ev
import jev_judge as jj
import judge_arms as arms
import hhem_judge as hhem
from evaluation_policy import (
    AGGREGATE_RATES,
    DEFERRED_FRAMEWORK_METRICS,
    DECISION_POLICY,
    METRIC_THRESHOLDS,
    aggregate_rate_status,
    framework_status,
)

HERE = Path(__file__).resolve().parent
DEFAULT_INPUT = HERE / "data" / "synthetic_adi_gt_100_sessions_250_queries.csv"
DEFAULT_GOLD = HERE / "data" / "synthetic_adi_gt_100_sessions_250_queries_gold.csv"
DEFAULT_OUT = HERE / "results" / "framework_session_benchmark"

LLM, JEV = "LLM judge", "JEV"
CURRENT_GPT = "Current GPT-4o"
MATCHED_GPT = "Matched-rubric GPT-4o"
GPT_MINI = "Matched-rubric GPT-4o-mini"
RAGAS_GPT = "RAGAS-style GPT-4o"
HYBRID = "Hybrid GPT extraction + JEV decision"
HHEM = "HHEM faithfulness"
# USD per 1M tokens (input, output), OpenRouter list prices.
LLM_PRICES = {"openai/gpt-4o": (2.50, 10.00), "openai/gpt-4o-mini": (0.15, 0.60)}
ARM_MODELS = {
    CURRENT_GPT: ev.JUDGE_MODEL,
    MATCHED_GPT: "openai/gpt-4o",
    GPT_MINI: "openai/gpt-4o-mini",
    RAGAS_GPT: ev.JUDGE_MODEL,
    HYBRID: f"{ev.JUDGE_MODEL} + {jj.JEV_MODEL}",
    HHEM: hhem.MODEL_ID,
}
ARM_CHOICES = ["llm", "jev", "matched-gpt", "gpt-mini", "ragas-gpt", "hybrid", "hhem"]

BINARY_METRICS = ["faithfulness", "answer_relevance", "context_relevance", "toxicity", "tone_appropriateness"]
COMPONENT_METRICS = ["factual_precision", "factual_recall", "factual_correctness", "semantic_similarity"]
FRAMEWORK_METRICS = BINARY_METRICS + ["answer_correctness"]
ALL_METRICS = BINARY_METRICS + COMPONENT_METRICS + ["answer_correctness"]
SME_METRICS = FRAMEWORK_METRICS
ARM_METRICS = {
    LLM: FRAMEWORK_METRICS + COMPONENT_METRICS,
    JEV: FRAMEWORK_METRICS + COMPONENT_METRICS,
    CURRENT_GPT: FRAMEWORK_METRICS + COMPONENT_METRICS,
    MATCHED_GPT: FRAMEWORK_METRICS + COMPONENT_METRICS,
    GPT_MINI: FRAMEWORK_METRICS + COMPONENT_METRICS,
    RAGAS_GPT: FRAMEWORK_METRICS + COMPONENT_METRICS,
    HYBRID: FRAMEWORK_METRICS + COMPONENT_METRICS,
    HHEM: ["faithfulness"],
}
GOLD_COL = {
    "faithfulness": "gold_faithful",
    "answer_relevance": "gold_answer_relevant",
    "context_relevance": "gold_context_relevant",
    "toxicity": "gold_toxic",
    "tone_appropriateness": "gold_tone_professional",
    "factual_precision": "gold_factual_precision",
    "factual_recall": "gold_factual_recall",
    "factual_correctness": "gold_factual_correctness",
    "semantic_similarity": "gold_semantic_similarity",
    "answer_correctness": "gold_answer_correctness",
}


# ============================================================
# Runs
# ============================================================
@dataclass
class JudgeRun:
    judge: str
    run: int
    scores: pd.DataFrame  # index row_id; one column per metric on a 0-1 scale
    calls: list[dict]     # latency_s, attempts, input_tokens, output_tokens, error
    wall_s: float
    out_of_range: int = 0
    models: set[str] = field(default_factory=set)


def run_llm(df: pd.DataFrame, meta: pd.DataFrame, run: int) -> tuple[JudgeRun, pd.DataFrame]:
    ev.CALL_LOG.clear()
    started = time.perf_counter()
    out = ev.process_dataframe(df.copy())
    wall = time.perf_counter() - started

    scores = pd.DataFrame(index=out.index)
    out_of_range = 0
    for metric in ALL_METRICS:
        col = metric.upper()
        reasons = out[f"{col}_REASON"].astype(str)
        # The evaluator writes 0.0 / "Not evaluated" for rows the LLM skipped; treat those as missing.
        values = pd.to_numeric(out[col], errors="coerce").where(reasons != "Not evaluated")
        out_of_range += int(((values < 0) | (values > 1)).sum())
        scores[metric] = values.clip(0, 1)
        scores[f"{metric}_reason"] = reasons
    judged = meta["needs_correctness"] & (scores["answer_correctness_reason"] != "Not evaluated")
    scores.loc[~judged, ["answer_correctness", *COMPONENT_METRICS]] = np.nan

    calls = [
        {
            "latency_s": c["latency_s"],
            "attempts": c["attempts"],
            "input_tokens": c["prompt_tokens"],
            "output_tokens": c["completion_tokens"],
            "error": c["error"],
            "model": ev.JUDGE_MODEL,
        }
        for c in ev.CALL_LOG
    ]
    return JudgeRun(LLM, run, scores, calls, wall, out_of_range, {ev.JUDGE_MODEL}), out


def run_jev(rows: list[dict], workers: int, api_key: str, run: int) -> tuple[JudgeRun, list[dict]]:
    scores, calls, wall, raws = jj.score_rows(rows, workers, api_key)
    models = {r["model"] for r in raws if r["model"]}
    out_of_range = sum(r.get("out_of_range_scores", 0) for r in raws)
    calls = [dict(call, model=jj.JEV_MODEL) for call in calls]
    return JudgeRun(JEV, run, scores, calls, wall, out_of_range, models), raws


def run_gpt_arm(
    rows: list[dict], workers: int, model: str, label: str, run: int
) -> tuple[JudgeRun, list[dict]]:
    scores, calls, wall, raws, out_of_range = arms.run_matched_gpt(rows, workers, model)
    return JudgeRun(label, run, scores, calls, wall, out_of_range, {model}), raws


def run_hybrid_arm(
    rows: list[dict], workers: int, api_key: str, run: int
) -> tuple[JudgeRun, list[dict]]:
    scores, calls, wall, raws, out_of_range = arms.run_hybrid(rows, workers, api_key)
    return JudgeRun(HYBRID, run, scores, calls, wall, out_of_range, {ev.JUDGE_MODEL, jj.JEV_MODEL}), raws


def run_hhem_arm(rows: list[dict], run: int) -> tuple[JudgeRun, list[dict]]:
    score_series, calls, wall, raws = hhem.score_rows(rows)
    scores = pd.DataFrame(index=score_series.index)
    scores["faithfulness"] = score_series
    scores["faithfulness_conf"] = np.nan
    calls = [dict(call, model=hhem.MODEL_ID) for call in calls]
    return JudgeRun(HHEM, run, scores, calls, wall, 0, {hhem.MODEL_ID}), raws


def run_ragas_arm(rows: list[dict], workers: int, run: int) -> tuple[JudgeRun, list[dict]]:
    scores, calls, wall, raws, out_of_range = arms.run_ragas_gpt(rows, workers, ev.JUDGE_MODEL)
    return JudgeRun(RAGAS_GPT, run, scores, calls, wall, out_of_range, {ev.JUDGE_MODEL}), raws


# ============================================================
# Analysis
# ============================================================
def _framework_failure(metric: str, score: float) -> bool:
    if metric == "toxicity":
        return framework_status(metric, score) == "fail"
    return framework_status(metric, score) != "pass"


def _failure_true(metric: str, gold: pd.Series) -> pd.Series:
    return gold.map(lambda value: _framework_failure(metric, float(value)))


def _failure_prob(metric: str, score: pd.Series) -> pd.Series:
    return score if metric == "toxicity" else 1 - score


def _failure_pred(metric: str, score: pd.Series, threshold: Optional[float] = None) -> pd.Series:
    if threshold is not None:
        return (score >= threshold) if metric == "toxicity" else (score < threshold)
    return score.map(lambda value: _framework_failure(metric, float(value)))


def _verdict(
    metric: str,
    values: pd.Series,
    threshold: Optional[float] = None,
    gold: bool = False,
) -> pd.Series:
    if gold and metric in BINARY_METRICS:
        failure = _failure_true(metric, values)
        verdict = failure.map({True: "fail", False: "pass"})
    elif threshold is not None and metric in BINARY_METRICS:
        failure = _failure_pred(metric, values, threshold)
        verdict = failure.map({True: "fail", False: "pass"})
    elif metric in ALL_METRICS:
        verdict = values.map(lambda value: framework_status(metric, value))
    else:
        verdict = values.map(lambda value: "not_evaluated")
    return verdict.where(values.notna())


def _quiet(fn: Callable, *args) -> float:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        try:
            return float(fn(*args))
        except ValueError:
            return float("nan")


def _corr(fn: Callable, a: pd.Series, b: pd.Series) -> float:
    if len(a) < 3 or a.nunique() < 2 or b.nunique() < 2:
        return float("nan")
    return float(fn(a, b)[0])


def _mean_over_runs(frames: list[pd.DataFrame], keys: list[str]) -> pd.DataFrame:
    frames = [f for f in frames if f is not None and not f.empty]
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames).groupby(keys, sort=False).mean(numeric_only=True).reset_index()


def accuracy_vs_gold(
    runs: dict[str, JudgeRun], gold: pd.DataFrame,
    thresholds: Optional[dict[str, float]] = None,
) -> pd.DataFrame:
    thresholds = thresholds or {}
    records = []
    for metric in ALL_METRICS:
        for judge, jr in runs.items():
            if metric not in jr.scores:
                continue
            pair = pd.DataFrame({"s": jr.scores[metric], "g": gold[GOLD_COL[metric]]}).dropna()
            if pair.empty:
                continue
            rec = {"metric": metric, "judge": judge, "n": len(pair), "mae_vs_gold": (pair.s - pair.g).abs().mean()}
            if metric in BINARY_METRICS:
                y = _failure_true(metric, pair.g).astype(int)
                p = _failure_prob(metric, pair.s)
                yhat = _failure_pred(metric, pair.s, thresholds.get(metric)).astype(int)
                rec.update(
                    gold_failures=int(y.sum()),
                    flagged=int(yhat.sum()),
                    accuracy=accuracy_score(y, yhat),
                    precision=precision_score(y, yhat, zero_division=0),
                    recall=recall_score(y, yhat, zero_division=0),
                    f1=f1_score(y, yhat, zero_division=0),
                    kappa=_quiet(cohen_kappa_score, y, yhat),
                    auc=_quiet(roc_auc_score, y, p),
                    brier=brier_score_loss(y, p),
                )
            elif metric == "answer_correctness":
                actual_status = pair.s.map(lambda score: framework_status(metric, score))
                gold_status = pair.g.map(lambda score: framework_status(metric, score))
                rec["accuracy"] = (actual_status == gold_status).mean()
                rec["framework_status_agreement"] = rec["accuracy"]
                rec["mae"] = (pair.s - pair.g).abs().mean()
                rec["quadratic_weighted_kappa"] = _quiet(
                    lambda actual, predicted: cohen_kappa_score(actual, predicted, weights="quadratic"),
                    np.digitize(pair.g, [0.5, 0.8]),
                    np.digitize(pair.s, [0.5, 0.8]),
                )
            elif metric in COMPONENT_METRICS:
                rec["mae"] = (pair.s - pair.g).abs().mean()
                rec["spearman"] = _corr(spearmanr, pair.s, pair.g)
            else:
                rec["mae"] = (pair.s - pair.g).abs().mean()
                rec["spearman"] = _corr(spearmanr, pair.s, pair.g)
            records.append(rec)
    return pd.DataFrame(records)


def sme_alignment(
    runs: dict[str, JudgeRun], meta: pd.DataFrame,
    thresholds: Optional[dict[str, float]] = None,
) -> pd.DataFrame:
    """Compare any framework metric non-pass with the overall SME outcome."""
    thresholds = thresholds or {}
    records = []
    for judge, jr in runs.items():
        if any(metric not in jr.scores for metric in SME_METRICS):
            continue
        d = jr.scores[SME_METRICS].join(meta["sme_correct"]).dropna()
        if d.empty:
            continue
        y = (1 - d["sme_correct"]).astype(int)
        p = pd.concat([_failure_prob(m, d[m]) for m in SME_METRICS], axis=1).max(axis=1)
        yhat = pd.concat([
            _failure_pred(m, d[m], thresholds.get(m)) for m in SME_METRICS
        ], axis=1).any(axis=1).astype(int)
        records.append({
            "judge": judge,
            "n": len(d),
            "sme_marked_incorrect": int(y.sum()),
            "judge_flagged": int(yhat.sum()),
            "accuracy": accuracy_score(y, yhat),
            "precision_bad": precision_score(y, yhat, zero_division=0),
            "recall_bad": recall_score(y, yhat, zero_division=0),
            "f1_bad": f1_score(y, yhat, zero_division=0),
            "kappa": _quiet(cohen_kappa_score, y, yhat),
            "auc": _quiet(roc_auc_score, y, p),
        })
    return pd.DataFrame(records)


def agreement(
    llm: JudgeRun, jev: JudgeRun, thresholds: Optional[dict[str, float]] = None
) -> pd.DataFrame:
    records = []
    for metric in FRAMEWORK_METRICS:
        if metric not in llm.scores or metric not in jev.scores:
            continue
        pair = pd.DataFrame({"llm": llm.scores[metric], "jev": jev.scores[metric]}).dropna()
        if pair.empty:
            continue
        threshold = (thresholds or {}).get(metric)
        a = _verdict(metric, pair.llm, threshold).astype(str)
        b = _verdict(metric, pair.jev, threshold).astype(str)
        records.append({
            "metric": metric,
            "n": len(pair),
            "mean_llm": pair.llm.mean(),
            "mean_jev": pair.jev.mean(),
            "mean_abs_diff": (pair.llm - pair.jev).abs().mean(),
            "pearson": _corr(pearsonr, pair.llm, pair.jev),
            "spearman": _corr(spearmanr, pair.llm, pair.jev),
            "verdict_agreement": (a == b).mean(),
            "kappa": _quiet(cohen_kappa_score, a, b),
        })
    return pd.DataFrame(records)


def all_pair_agreement(per_run: list[dict[str, JudgeRun]], thresholds: Optional[dict[str, float]] = None) -> pd.DataFrame:
    records = []
    for run_index, runs in enumerate(per_run, start=1):
        for judge_a, judge_b in itertools.combinations(runs, 2):
            result = agreement(runs[judge_a], runs[judge_b], thresholds)
            result["run"] = run_index
            result["judge_a"] = judge_a
            result["judge_b"] = judge_b
            records.append(result)
    frames = [record for record in records if not record.empty]
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def consistency(
    all_runs: dict[str, list[JudgeRun]], thresholds: Optional[dict[str, float]] = None
) -> pd.DataFrame:
    records = []
    for judge, runs in all_runs.items():
        if len(runs) < 2:
            continue
        base = runs[0].scores
        for metric in ALL_METRICS:
            if metric not in base:
                continue
            changes, flips = [], []
            for other in runs[1:]:
                if metric not in other.scores:
                    continue
                pair = pd.DataFrame({"a": base[metric], "b": other.scores[metric]}).dropna()
                changes.append((pair.a - pair.b).abs())
                threshold = (thresholds or {}).get(metric)
                flips.append(_verdict(metric, pair.a, threshold) != _verdict(metric, pair.b, threshold))
            if not changes:
                continue
            change, flip = pd.concat(changes), pd.concat(flips)
            if change.empty:
                continue
            records.append({
                "judge": judge,
                "metric": metric,
                "comparisons": len(change),
                "mean_abs_change": change.mean(),
                "max_abs_change": change.max(),
                "verdict_flip_rate": flip.mean(),
            })
    return pd.DataFrame(records)


def jev_confidence(
    jev: JudgeRun, gold: pd.DataFrame, cutoff: float,
    thresholds: Optional[dict[str, float]] = None,
) -> pd.DataFrame:
    records = []
    for metric in ALL_METRICS:
        pair = pd.DataFrame({
            "s": jev.scores[metric],
            "c": jev.scores[f"{metric}_conf"],
            "g": gold[GOLD_COL[metric]],
        }).dropna()
        if pair.empty:
            continue
        threshold = (thresholds or {}).get(metric)
        correct = _verdict(metric, pair.s, threshold) == _verdict(metric, pair.g, threshold, gold=True)
        high = pair.c >= cutoff
        records.append({
            "metric": metric,
            "n": len(pair),
            "mean_confidence": pair.c.mean(),
            "confidence_when_right": pair.c[correct].mean(),
            "confidence_when_wrong": pair.c[~correct].mean(),
            f"n_conf>={cutoff}": int(high.sum()),
            f"accuracy_conf>={cutoff}": correct[high].mean() if high.any() else np.nan,
            f"n_conf<{cutoff}": int((~high).sum()),
            f"accuracy_conf<{cutoff}": correct[~high].mean() if (~high).any() else np.nan,
        })
    return pd.DataFrame(records)


def latency_cost(all_runs: dict[str, list[JudgeRun]], meta: pd.DataFrame) -> pd.DataFrame:
    n_rows = len(meta)
    records = []
    for judge, runs in all_runs.items():
        for jr in runs:
            lat = pd.Series([c["latency_s"] for c in jr.calls], dtype=float)
            tokens_in = sum(c["input_tokens"] for c in jr.calls)
            tokens_out = sum(c["output_tokens"] for c in jr.calls)
            cost = 0.0
            unknown_pricing = False
            for call in jr.calls:
                model = call.get("model")
                if model == jj.JEV_MODEL or (isinstance(model, str) and model.startswith("jev-")):
                    price_in, price_out = jj.PRICE_PER_M
                elif model == hhem.MODEL_ID or judge == HHEM:
                    price_in, price_out = 0.0, 0.0
                else:
                    price_in, price_out = LLM_PRICES.get(model or ev.JUDGE_MODEL, (np.nan, np.nan))
                if not np.isfinite(price_in) or not np.isfinite(price_out):
                    unknown_pricing = True
                    continue
                cost += (call["input_tokens"] * price_in + call["output_tokens"] * price_out) / 1e6
            scored_metrics = ARM_METRICS.get(judge, FRAMEWORK_METRICS)
            missing = jr.scores[scored_metrics].isna().any(axis=1)
            records.append({
                "judge": judge,
                "run": jr.run,
                "rows": n_rows,
                "api_calls": len(jr.calls),
                "failed_calls": sum(1 for c in jr.calls if c["error"]),
                "retries": sum(max(0, c["attempts"] - 1) for c in jr.calls),
                "rows_missing_scores": int(missing.sum()),
                "out_of_range_scores": jr.out_of_range,
                "wall_time_s": jr.wall_s,
                "rows_per_s": n_rows / jr.wall_s if jr.wall_s else np.nan,
                "call_p50_s": lat.median(),
                "call_p95_s": lat.quantile(0.95),
                "call_max_s": lat.max(),
                "compute_s_per_row": lat.sum() / n_rows,
                "input_tokens": tokens_in,
                "output_tokens": tokens_out,
                "cost_usd": np.nan if unknown_pricing else cost,
                "cost_per_1k_rows_usd": np.nan if unknown_pricing or not n_rows else cost / n_rows * 1000,
            })
    return pd.DataFrame(records)


def framework_reports(all_runs: dict[str, list[JudgeRun]], meta: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Build query-level framework statuses and query/product/platform aggregates."""
    query_records: list[dict] = []
    aggregate_records: list[dict] = []
    scopes = [
        ("platform", []),
        ("evaluation_split", ["evaluation_split"]),
        ("product", ["product"]),
        ("sub_product", ["product", "sub_product"]),
        ("session", ["session_id"]),
    ]

    for judge, judge_runs in all_runs.items():
        for judge_run in judge_runs:
            metadata_columns = [column for column in (
                "product", "sub_product", "session_id", "evaluation_split", "session_turn",
                "session_length", "sme_correct", "retrieval_precision_at_k", "retrieval_recall_at_k",
            ) if column in meta]
            frame = meta[metadata_columns].copy()
            frame["judge"] = judge
            frame["run"] = judge_run.run
            for metric in FRAMEWORK_METRICS:
                if metric not in judge_run.scores:
                    continue
                frame[f"{metric}_score"] = judge_run.scores[metric].reindex(frame.index)
                frame[f"{metric}_status"] = frame[f"{metric}_score"].map(
                    lambda value: framework_status(metric, value)
                )
            frame["retrieval_precision_at_k"] = frame["retrieval_precision_at_k"].astype(float)
            frame["retrieval_recall_at_k"] = frame["retrieval_recall_at_k"].astype(float)
            query_records.extend(frame.reset_index(names="row_id").to_dict("records"))

            for scope, columns in scopes:
                groups = [("ALL", frame)] if not columns else frame.groupby(columns, dropna=False, sort=False)
                for group_key, group in groups:
                    keys = group_key if isinstance(group_key, tuple) else (group_key,)
                    group_labels = dict(zip(columns, keys))
                    for metric in FRAMEWORK_METRICS:
                        scores = group[f"{metric}_score"].dropna()
                        if scores.empty:
                            continue
                        statuses = group.loc[scores.index, f"{metric}_status"]
                        pass_count = int((statuses == "pass").sum())
                        review_count = int((statuses == "review").sum())
                        fail_count = int((statuses == "fail").sum())
                        is_rate_metric = metric in {"tone_appropriateness", "toxicity"}
                        compliance = pass_count / len(scores) if is_rate_metric else np.nan
                        status = (
                            aggregate_rate_status(metric, compliance)
                            if is_rate_metric else framework_status(metric, scores.mean())
                        )
                        aggregate_records.append({
                            "scope": scope,
                            **group_labels,
                            "judge": judge,
                            "run": judge_run.run,
                            "metric": metric,
                            "evaluated_n": len(scores),
                            "mean_score": scores.mean(),
                            "pass_n": pass_count,
                            "review_n": review_count,
                            "fail_n": fail_count,
                            "compliant_or_non_toxic_rate": compliance,
                            "framework_status": status,
                        })
                    for metric in ("retrieval_precision_at_k", "retrieval_recall_at_k"):
                        vals = group[metric].dropna()
                        aggregate_records.append({
                            "scope": scope,
                            **group_labels,
                            "judge": judge,
                            "run": judge_run.run,
                            "metric": metric,
                            "evaluated_n": len(vals),
                            "mean_score": vals.mean() if len(vals) else np.nan,
                            "pass_n": np.nan,
                            "review_n": np.nan,
                            "fail_n": np.nan,
                            "compliant_or_non_toxic_rate": np.nan,
                            "framework_status": "not_evaluated" if vals.empty else "descriptive_only",
                        })
    return pd.DataFrame(query_records), pd.DataFrame(aggregate_records)


def threshold_sweep(runs: dict[str, JudgeRun], gold: pd.DataFrame) -> pd.DataFrame:
    """Development-only common binary-cutoff diagnostics; never auto-select a test cutoff."""
    records = []
    for judge, judge_run in runs.items():
        for metric in BINARY_METRICS:
            pair = pd.DataFrame({"score": judge_run.scores[metric], "gold": gold[GOLD_COL[metric]]}).dropna()
            if pair.empty:
                continue
            y = _failure_true(metric, pair["gold"]).astype(int)
            for threshold in np.arange(0.30, 0.91, 0.05):
                predicted = _failure_pred(metric, pair["score"], float(threshold)).astype(int)
                records.append({
                    "judge": judge,
                    "metric": metric,
                    "development_threshold": round(float(threshold), 2),
                    "n": len(pair),
                    "recall_failure": recall_score(y, predicted, zero_division=0),
                    "precision_failure": precision_score(y, predicted, zero_division=0),
                    "f1_failure": f1_score(y, predicted, zero_division=0),
                    "balanced_accuracy": (recall_score(y, predicted, zero_division=0)
                                          + recall_score(1-y, 1-predicted, zero_division=0)) / 2,
                })
    return pd.DataFrame(records)


def arm_summary(acc: pd.DataFrame, sme: pd.DataFrame, latency: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for judge in latency["judge"].drop_duplicates():
        metric_rows = acc[acc["judge"] == judge] if not acc.empty else pd.DataFrame()
        binary_accuracy = metric_rows[metric_rows["metric"].isin(BINARY_METRICS)]["accuracy"]
        faithfulness = metric_rows[metric_rows["metric"] == "faithfulness"]
        correctness = metric_rows[metric_rows["metric"] == "answer_correctness"]
        sme_row = sme[sme["judge"] == judge] if not sme.empty else pd.DataFrame()
        op = latency[latency["judge"] == judge]
        rows.append({
            "arm": judge,
            "metrics_covered": ", ".join(metric_rows["metric"].unique()) if not metric_rows.empty else "faithfulness only",
            "mean_binary_framework_accuracy": binary_accuracy.mean() if not binary_accuracy.empty else np.nan,
            "faithfulness_accuracy": faithfulness["accuracy"].mean() if not faithfulness.empty else np.nan,
            "faithfulness_failure_recall": faithfulness["recall"].mean() if not faithfulness.empty else np.nan,
            "answer_correctness_status_agreement": correctness["accuracy"].mean() if not correctness.empty else np.nan,
            "answer_correctness_mae": correctness["mae"].mean() if not correctness.empty else np.nan,
            "SME_overall_agreement": sme_row["accuracy"].mean() if not sme_row.empty else np.nan,
            "wall_time_s_mean": op["wall_time_s"].mean(),
            "call_p50_s_mean": op["call_p50_s"].mean(),
            "call_p95_s_mean": op["call_p95_s"].mean(),
            "cost_per_1k_rows_usd": op["cost_per_1k_rows_usd"].mean(),
            "failed_calls": op["failed_calls"].sum(),
            "rows_missing_scores": op["rows_missing_scores"].sum(),
            "out_of_range_scores": op["out_of_range_scores"].sum(),
        })
    return pd.DataFrame(rows)


def decision_policy_table() -> pd.DataFrame:
    records = []
    for metric, band in METRIC_THRESHOLDS.items():
        records.append({"metric": metric, "query_pass": band["pass"], "query_review": band["review"],
                        "query_fail": f"< {band['review']}", "aggregate_pass": np.nan,
                        "aggregate_review": np.nan, "aggregate_fail": np.nan,
                        "formula_or_note": "Mean score aggregated at scope; not a per-row accuracy claim."})
    for metric, band in AGGREGATE_RATES.items():
        records.append({"metric": metric, "query_pass": "binary compliance flag", "query_review": "N/A",
                        "query_fail": "binary non-compliance flag", "aggregate_pass": band["pass"],
                        "aggregate_review": band["review"], "aggregate_fail": f"< {band['review']}",
                        "formula_or_note": "Tone: score >= 0.5 is compliant. Toxicity: score < 0.5 is non-toxic."})
    records.extend([
        {"metric": "answer_correctness", "query_pass": 0.80, "query_review": 0.50,
         "query_fail": "< 0.50", "aggregate_pass": np.nan, "aggregate_review": np.nan,
         "aggregate_fail": np.nan, "formula_or_note": "0.75 * factual F1 + 0.25 * semantic similarity; grounded on reference for every row."},
        {"metric": "document_retrieval_precision_recall_at_k", "query_pass": np.nan, "query_review": np.nan,
         "query_fail": np.nan, "aggregate_pass": np.nan, "aggregate_review": np.nan,
         "aggregate_fail": np.nan, "formula_or_note": "Exact normalized document IDs; descriptive until framework thresholds are approved."},
    ])
    for metric, note in DEFERRED_FRAMEWORK_METRICS.items():
        records.append({"metric": metric, "query_pass": np.nan, "query_review": np.nan,
                        "query_fail": np.nan, "aggregate_pass": np.nan, "aggregate_review": np.nan,
                        "aggregate_fail": np.nan, "formula_or_note": f"DEFERRED: {note}"})
    records.append({"metric": "lifecycle", "query_pass": DECISION_POLICY["stage_1"],
                    "query_review": DECISION_POLICY["stage_2"], "query_fail": "Owner-approved gate not set",
                    "aggregate_pass": DECISION_POLICY["approval"], "aggregate_review": "Human review sampling",
                    "aggregate_fail": DECISION_POLICY["automation"],
                    "formula_or_note": "Development/test split is by session; no automatic production action."})
    return pd.DataFrame(records)


def head_to_head(acc: pd.DataFrame, sme: pd.DataFrame, lat: pd.DataFrame, cons: pd.DataFrame) -> pd.DataFrame:
    def by_judge(frame: pd.DataFrame, column: str, metrics: Optional[list[str]] = None, agg: str = "mean") -> dict:
        if frame is None or frame.empty or column not in frame:
            return {}
        if metrics is not None:
            frame = frame[frame["metric"].isin(metrics)]
        return frame.groupby("judge")[column].agg(agg).to_dict()

    # (criterion, higher_is_better, show_as_ratio, values)
    criteria = [
        ("Accuracy vs gold (mean of 5 metrics)", True, False, by_judge(acc, "accuracy", BINARY_METRICS)),
        ("Failure-detection F1 vs gold (mean)", True, False, by_judge(acc, "f1", BINARY_METRICS)),
        ("AUC vs gold (mean)", True, False, by_judge(acc, "auc", BINARY_METRICS)),
        ("Brier score vs gold (mean)", False, False, by_judge(acc, "brier", BINARY_METRICS)),
        ("Hallucination recall (unfaithful answers caught)", True, False, by_judge(acc, "recall", ["faithfulness"])),
        ("Hallucination precision", True, False, by_judge(acc, "precision", ["faithfulness"])),
        ("Answer-correctness band accuracy", True, False, by_judge(acc, "accuracy", ["answer_correctness"])),
        ("SME agreement accuracy", True, False, by_judge(sme, "accuracy")),
        ("SME-incorrect answers caught (recall)", True, False, by_judge(sme, "recall_bad")),
        ("SME AUC", True, False, by_judge(sme, "auc")),
        ("Wall time for the dataset (s)", False, True, by_judge(lat, "wall_time_s")),
        ("Throughput (rows/s)", True, True, by_judge(lat, "rows_per_s")),
        ("Median call latency (s)", False, True, by_judge(lat, "call_p50_s")),
        ("p95 call latency (s)", False, True, by_judge(lat, "call_p95_s")),
        ("Cost per 1,000 rows (USD)", False, True, by_judge(lat, "cost_per_1k_rows_usd")),
        ("Failed calls (all runs)", False, False, by_judge(lat, "failed_calls", agg="sum")),
        ("Rows with missing scores (all runs)", False, False, by_judge(lat, "rows_missing_scores", agg="sum")),
        ("Run-to-run verdict flip rate", False, False, by_judge(cons, "verdict_flip_rate")),
        ("Run-to-run mean score change", False, False, by_judge(cons, "mean_abs_change")),
    ]
    records = []
    for name, higher, ratio, values in criteria:
        a, b = values.get(LLM, np.nan), values.get(JEV, np.nan)
        if pd.isna(a) or pd.isna(b):
            winner, note = "n/a", ""
        elif abs(a - b) < 1e-9:
            winner, note = "tie", ""
        else:
            winner = JEV if (b > a) == higher else LLM
            best, worst = (max(a, b), min(a, b)) if higher else (min(a, b), max(a, b))
            if ratio and best > 0 and worst > 0:
                note = f"{winner} {max(a, b) / min(a, b):.1f}x better"
            else:
                note = f"{winner} better by {abs(a - b):.3f}"
        records.append({
            "criterion": name,
            LLM: a,
            JEV: b,
            "better": "higher" if higher else "lower",
            "winner": winner,
            "note": note,
        })
    return pd.DataFrame(records)


def per_row_table(meta: pd.DataFrame, gold: Optional[pd.DataFrame], llm: Optional[JudgeRun],
                  jev: Optional[JudgeRun], t: float) -> pd.DataFrame:
    table = meta[["user_query", "sme_correct"]].copy()
    if gold is not None:
        table.insert(0, "scenario", gold["scenario"])
    for metric in ALL_METRICS:
        if gold is not None:
            table[f"gold_{metric}"] = gold[GOLD_COL[metric]]
        if llm is not None:
            table[f"llm_{metric}"] = llm.scores[metric]
        if jev is not None:
            table[f"jev_{metric}"] = jev.scores[metric]
            table[f"jev_{metric}_conf"] = jev.scores[f"{metric}_conf"]

    def verdicts(source: pd.DataFrame, is_gold: bool = False) -> dict[str, pd.Series]:
        return {m: _verdict(m, source[GOLD_COL[m] if is_gold else m], t, gold=is_gold) for m in ALL_METRICS}

    def mismatches(left: dict[str, pd.Series], right: dict[str, pd.Series]) -> list[str]:
        return [
            ", ".join(
                m for m in ALL_METRICS
                if pd.notna(left[m].get(i)) and pd.notna(right[m].get(i)) and left[m][i] != right[m][i]
            )
            for i in table.index
        ]

    if llm is not None and jev is not None:
        table["llm_vs_jev_disagree_on"] = mismatches(verdicts(llm.scores), verdicts(jev.scores))
    if gold is not None:
        gold_v = verdicts(gold, is_gold=True)
        for prefix, jr in (("llm", llm), ("jev", jev)):
            if jr is not None:
                table[f"{prefix}_wrong_vs_gold_on"] = mismatches(verdicts(jr.scores), gold_v)
    if llm is not None:
        table["llm_faithfulness_reason"] = llm.scores["faithfulness_reason"]
        table["llm_answer_correctness_reason"] = llm.scores["answer_correctness_reason"]
    return table


def load_gold(path: Path, meta: pd.DataFrame) -> pd.DataFrame:
    gold = pd.read_csv(path, encoding="utf-8-sig").set_index("row_id")
    misaligned = [
        i for i in gold.index
        if i not in meta.index or meta.at[i, "user_query"].strip() != str(gold.at[i, "user_query"]).strip()
    ]
    if misaligned:
        raise SystemExit(f"Gold labels do not line up with the input rows (row_ids {misaligned[:5]})")
    return gold


# ============================================================
# Main
# ============================================================
def _print(title: str, frame: Optional[pd.DataFrame]) -> None:
    if frame is None or frame.empty:
        return
    print(f"\n=== {title} ===")
    with pd.option_context("display.width", 250, "display.max_columns", 40, "display.max_colwidth", 60):
        print(frame.to_string(index=False, float_format=lambda v: f"{v:.3f}"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare judge arms on the ADI evaluation benchmark.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT, help="GT sheet (CSV) in the SME layout")
    parser.add_argument("--gold", default=str(DEFAULT_GOLD), help="gold-label CSV, or 'none' for real data")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="output folder")
    parser.add_argument("--repeats", type=int, default=2, help="runs per arm (>=2 measures consistency)")
    parser.add_argument("--workers", type=int, default=ev.MAX_WORKERS, help="concurrent calls")
    parser.add_argument("--threshold", type=float, default=0.5, help="score cut-off for binary pass/fail verdicts")
    parser.add_argument("--confidence", type=float, default=0.8, help="JEV high-confidence cut-off")
    parser.add_argument("--judges", choices=["both", "llm", "jev"], default="both",
                        help="legacy shorthand; ignored when --arms is given")
    parser.add_argument("--arms", nargs="+", choices=ARM_CHOICES, default=None,
                        help="arms to run: llm, jev, matched-gpt, gpt-mini, ragas-gpt, hybrid, hhem")
    parser.add_argument("--split", choices=["all", "dev", "test"], default="all",
                        help="evaluation split to run; threshold tuning is refused on 'test'")
    parser.add_argument("--tune", action="store_true",
                        help="development-only threshold sweep over dev rows (never the held-out test split)")
    args = parser.parse_args()

    arm_labels = list(args.arms) if args.arms else (["llm", "jev"] if args.judges == "both" else [args.judges])
    if args.tune and args.split == "test":
        raise SystemExit("Threshold tuning is not allowed on the held-out test split.")

    t = args.threshold
    thresholds = {metric: t for metric in BINARY_METRICS}

    jev_key = jj.api_key()
    needs_llm = any(label in ("llm", "matched-gpt", "gpt-mini", "ragas-gpt", "hybrid") for label in arm_labels)
    needs_jev = "jev" in arm_labels or "hybrid" in arm_labels
    if needs_llm:
        ev._client()
    if needs_jev:
        jj.preflight(jev_key)
    if "hhem" in arm_labels and importlib.util.find_spec("transformers") is None:
        raise SystemExit(
            "The 'hhem' arm needs transformers (pip install -r requirements-hhem.txt). "
            "Drop 'hhem' from --arms to run without it."
        )

    df = ev.load_input(str(args.input))
    rows = jj.prepare_rows(df)
    meta = pd.DataFrame(rows).set_index("row_id")
    gold = None if args.gold.lower() == "none" else load_gold(Path(args.gold), meta)
    ev.MAX_WORKERS = args.workers

    if args.split != "all":
        keep = meta[meta["evaluation_split"].str.casefold() == args.split].index
        if keep.empty:
            raise SystemExit(
                f"No rows in split '{args.split}'; dataset splits: "
                f"{sorted(meta['evaluation_split'].dropna().astype(str).unique())}"
            )
        meta = meta.loc[keep]
        rows = [r for r in rows if r["row_id"] in meta.index]
        df = df.loc[meta.index]
        if gold is not None:
            gold = gold.loc[gold.index.intersection(meta.index)]

    all_runs: dict[str, list[JudgeRun]] = {}
    llm_outputs: list[pd.DataFrame] = []
    jev_raws: list[dict] = []
    hybrid_raws: dict[int, list[dict]] = {}
    for run in range(1, args.repeats + 1):
        for label in arm_labels:
            print(f"\n--- {label} run {run}/{args.repeats} ---")
            try:
                if label == "llm":
                    jr, out = run_llm(df, meta, run)
                    all_runs.setdefault(LLM, []).append(jr)
                    llm_outputs.append(out)
                elif label == "jev":
                    jr, raws = run_jev(rows, args.workers, jev_key, run)
                    all_runs.setdefault(JEV, []).append(jr)
                    jev_raws.extend(raws)
                elif label == "matched-gpt":
                    jr, _ = run_gpt_arm(rows, args.workers, ARM_MODELS[MATCHED_GPT], MATCHED_GPT, run)
                    all_runs.setdefault(MATCHED_GPT, []).append(jr)
                elif label == "gpt-mini":
                    jr, _ = run_gpt_arm(rows, args.workers, ARM_MODELS[GPT_MINI], GPT_MINI, run)
                    all_runs.setdefault(GPT_MINI, []).append(jr)
                elif label == "ragas-gpt":
                    jr, _ = run_ragas_arm(rows, args.workers, run)
                    all_runs.setdefault(RAGAS_GPT, []).append(jr)
                elif label == "hybrid":
                    jr, raws = run_hybrid_arm(rows, args.workers, jev_key, run)
                    all_runs.setdefault(HYBRID, []).append(jr)
                    hybrid_raws.setdefault(run, []).extend(raws)
                elif label == "hhem":
                    jr, _ = run_hhem_arm(rows, run)
                    all_runs.setdefault(HHEM, []).append(jr)
            except SystemExit:
                raise
            except Exception as exc:  # one arm failing must not kill the whole benchmark
                print(f"  !! failed: {type(exc).__name__}: {exc}")
            else:
                print(f"  {len(jr.calls)} calls in {jr.wall_s:.1f}s")
    if not all_runs:
        raise SystemExit("No arm completed a run; nothing to analyse.")

    per_run = [{judge: runs[k] for judge, runs in all_runs.items()} for k in range(args.repeats)]
    acc = (
        _mean_over_runs([accuracy_vs_gold(r, gold, thresholds) for r in per_run], ["metric", "judge"])
        if gold is not None else pd.DataFrame()
    )
    sme = _mean_over_runs([sme_alignment(r, meta, thresholds) for r in per_run], ["judge"])
    agree = (
        _mean_over_runs([agreement(r[LLM], r[JEV], thresholds) for r in per_run], ["metric"])
        if LLM in all_runs and JEV in all_runs else pd.DataFrame()
    )
    arm_agree = all_pair_agreement(per_run, thresholds) if len(all_runs) > 1 else pd.DataFrame()
    lat = latency_cost(all_runs, meta)
    cons = consistency(all_runs, thresholds)
    conf = (
        jev_confidence(all_runs[JEV][0], gold, args.confidence, thresholds)
        if JEV in all_runs and gold is not None else None
    )
    summary = head_to_head(acc, sme, lat, cons) if LLM in all_runs and JEV in all_runs else pd.DataFrame()
    first = per_run[0]
    per_row = per_row_table(meta, gold, first.get(LLM), first.get(JEV), t)
    query_level, aggregates = framework_reports(all_runs, meta)
    policy_table = decision_policy_table()
    arms_table = arm_summary(acc, sme, lat)
    sweep = pd.DataFrame()
    if args.tune and gold is not None:
        dev_idx = meta[meta["evaluation_split"].str.casefold() == "dev"].index
        if dev_idx.empty:
            print("No dev-split rows available for the threshold sweep; skipping.")
        else:
            sweep = threshold_sweep(first, gold.loc[dev_idx])

    split_tag = args.split
    jev_models = sorted({m for jr in all_runs.get(JEV, []) for m in jr.models})
    sme_yes = int(meta["sme_correct"].sum())
    setup = pd.DataFrame(
        [
            ("Input", str(args.input)),
            ("Evaluation split", split_tag),
            ("Arms", ", ".join(arm_labels)),
            ("Rows (SME Yes / No)", f"{len(meta)} ({sme_yes} / {len(meta) - sme_yes})"),
            ("Gold labels", "none" if gold is None else str(args.gold)),
            ("LLM judge", f"{ev.JUDGE_MODEL} via OpenRouter, {ev.ROWS_PER_LLM_CALL} rows per call "
                          "(adi_gt_evaluator.py prompts and batching, unchanged)"),
            ("JEV", f"{', '.join(jev_models) or jj.JEV_MODEL} via {jj.JEV_URL}, 1 row per call, "
                    f"{len(jj.JEV_QUESTIONS)} Score questions (+1 correctness question for SME=No rows)"),
            ("Concurrency", args.workers),
            ("Runs per arm", args.repeats),
            ("Pass/fail threshold on 0-1 scores", t),
            ("Threshold sweep (dev-only)", "on" if not sweep.empty else "off"),
            ("Prices, USD per 1M tokens in/out",
             f"LLM {LLM_PRICES.get(ev.JUDGE_MODEL, ('?', '?'))}; JEV {jj.PRICE_PER_M} (output tokens free)"),
            ("Accuracy / agreement / SME tables", f"mean over {args.repeats} run(s); per-row sheet = run 1"),
        ],
        columns=["item", "value"],
    )

    sheets = {
        "Summary": summary,
        "Setup": setup,
        "Accuracy_vs_Gold": acc,
        "SME_Alignment": sme,
        "Agreement": agree,
        "Latency_Cost": lat,
        "Consistency": cons,
        "JEV_Confidence": conf,
    }
    args.out.mkdir(parents=True, exist_ok=True)
    xlsx = args.out / "jev_vs_llm_comparison.xlsx"
    with pd.ExcelWriter(xlsx, engine="openpyxl") as writer:
        for name, frame in sheets.items():
            if frame is not None and not frame.empty:
                frame.round(4).to_excel(writer, sheet_name=name, index=False)
        per_row.round(4).to_excel(writer, sheet_name="Per_Row", index_label="row_id")

    # Legacy names are kept for split=all (default) so existing consumers keep
    # working; every run additionally writes split-suffixed copies so dev/test
    # outputs never overwrite each other and a test result cannot be mistaken
    # for tuning evidence.
    per_row.round(4).to_csv(args.out / f"per_row_{split_tag}.csv", index_label="row_id", encoding="utf-8-sig")
    if not summary.empty:
        summary.round(4).to_csv(args.out / f"summary_{split_tag}.csv", index=False, encoding="utf-8-sig")
    for k, out in enumerate(llm_outputs, start=1):
        out.to_csv(args.out / f"llm_judge_run{k}_{split_tag}.csv", index=False, encoding="utf-8-sig")
    if jev_raws:
        with (args.out / f"jev_raw_responses_{split_tag}.jsonl").open("w", encoding="utf-8") as fh:
            for raw in jev_raws:
                fh.write(json.dumps(raw, ensure_ascii=False, default=str) + "\n")
    if hybrid_raws:
        with (args.out / f"hybrid_raw_responses_{split_tag}.jsonl").open("w", encoding="utf-8") as fh:
            for raw in itertools.chain.from_iterable(hybrid_raws.values()):
                fh.write(json.dumps(raw, ensure_ascii=False, default=str) + "\n")
    if not query_level.empty:
        query_level.round(4).to_csv(args.out / f"framework_query_level_{split_tag}.csv", index=False, encoding="utf-8-sig")
    if not aggregates.empty:
        aggregates.round(4).to_csv(args.out / f"framework_aggregates_{split_tag}.csv", index=False, encoding="utf-8-sig")
    policy_table.round(4).to_csv(args.out / "decision_policy.csv", index=False, encoding="utf-8-sig")
    if not arms_table.empty:
        arms_table.round(4).to_csv(args.out / f"arm_summary_{split_tag}.csv", index=False, encoding="utf-8-sig")
    if not arm_agree.empty:
        arm_agree.round(4).to_csv(args.out / f"arm_agreement_{split_tag}.csv", index=False, encoding="utf-8-sig")
    if not sweep.empty:
        sweep.round(4).to_csv(args.out / "threshold_sweep_dev.csv", index=False, encoding="utf-8-sig")
    if split_tag == "all":
        per_row.round(4).to_csv(args.out / "per_row.csv", index_label="row_id", encoding="utf-8-sig")
        if not summary.empty:
            summary.round(4).to_csv(args.out / "summary.csv", index=False, encoding="utf-8-sig")
        for k, out in enumerate(llm_outputs, start=1):
            out.to_csv(args.out / f"llm_judge_run{k}.csv", index=False, encoding="utf-8-sig")
        if jev_raws:
            with (args.out / "jev_raw_responses.jsonl").open("w", encoding="utf-8") as fh:
                for raw in jev_raws:
                    fh.write(json.dumps(raw, ensure_ascii=False, default=str) + "\n")

    _print("Setup", setup)
    _print("Head-to-head (LLM vs JEV)", summary)
    if not acc.empty:
        _print("Accuracy vs gold", acc[[c for c in (
            "metric", "judge", "n", "gold_failures", "flagged", "accuracy", "precision", "recall", "f1", "auc", "brier"
        ) if c in acc]])
    _print("SME alignment", sme)
    _print("Judge agreement", agree)
    _print("Arm agreement", arm_agree)
    _print("Latency / cost / reliability", lat[[
        "judge", "run", "api_calls", "failed_calls", "rows_missing_scores", "wall_time_s", "call_p50_s",
        "call_p95_s", "input_tokens", "output_tokens", "cost_usd",
    ]])
    _print("Consistency across runs", cons)
    _print("JEV confidence", conf)
    _print("Arm summary", arms_table)
    _print("Framework aggregates", aggregates)
    _print("Dev-only threshold sweep", sweep)
    print(f"\nWrote {xlsx} + framework CSVs under {args.out}")


if __name__ == "__main__":
    main()
