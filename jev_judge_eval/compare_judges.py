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

HERE = Path(__file__).resolve().parent
DEFAULT_INPUT = HERE / "data" / "synthetic_adi_gt_35.csv"
DEFAULT_GOLD = HERE / "data" / "synthetic_adi_gt_35_gold.csv"
DEFAULT_OUT = HERE / "results"

LLM, JEV = "LLM judge", "JEV"
# USD per 1M tokens (input, output), OpenRouter list prices.
LLM_PRICES = {"openai/gpt-4o": (2.50, 10.00), "openai/gpt-4o-mini": (0.15, 0.60)}

BINARY_METRICS = ["faithfulness", "answer_relevance", "context_relevance", "toxicity", "tone_appropriateness"]
ALL_METRICS = BINARY_METRICS + ["answer_correctness"]
SME_METRICS = ["faithfulness", "answer_relevance", "toxicity", "tone_appropriateness"]
GOLD_COL = {
    "faithfulness": "gold_faithful",
    "answer_relevance": "gold_answer_relevant",
    "context_relevance": "gold_context_relevant",
    "toxicity": "gold_toxic",
    "tone_appropriateness": "gold_tone_professional",
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
    # Correctness is only judged for SME=No rows with a GT answer; a failed call reads "No GT answer provided".
    judged = meta["needs_correctness"] & (scores["answer_correctness_reason"] != "No GT answer provided")
    scores.loc[~judged, "answer_correctness"] = np.nan

    calls = [
        {
            "latency_s": c["latency_s"],
            "attempts": c["attempts"],
            "input_tokens": c["prompt_tokens"],
            "output_tokens": c["completion_tokens"],
            "error": c["error"],
        }
        for c in ev.CALL_LOG
    ]
    return JudgeRun(LLM, run, scores, calls, wall, out_of_range, {ev.JUDGE_MODEL}), out


def run_jev(rows: list[dict], workers: int, api_key: str, run: int) -> tuple[JudgeRun, list[dict]]:
    scores, calls, wall, raws = jj.score_rows(rows, workers, api_key)
    models = {r["model"] for r in raws if r["model"]}
    return JudgeRun(JEV, run, scores, calls, wall, 0, models), [{"run": run, **r} for r in raws]


# ============================================================
# Analysis
# ============================================================
def _failure_true(metric: str, gold: pd.Series) -> pd.Series:
    return gold if metric == "toxicity" else 1 - gold


def _failure_prob(metric: str, score: pd.Series) -> pd.Series:
    return score if metric == "toxicity" else 1 - score


def _failure_pred(metric: str, score: pd.Series, threshold: float) -> pd.Series:
    return (score >= threshold) if metric == "toxicity" else (score < threshold)


def _band(score: pd.Series) -> pd.Series:
    return (score * 2).round() / 2


def _verdict(metric: str, values: pd.Series, threshold: float, gold: bool = False) -> pd.Series:
    if metric == "answer_correctness":
        verdict = values if gold else _band(values)
    elif gold:
        verdict = _failure_true(metric, values)
    else:
        verdict = _failure_pred(metric, values, threshold).astype(float)
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


def accuracy_vs_gold(runs: dict[str, JudgeRun], gold: pd.DataFrame, t: float) -> pd.DataFrame:
    records = []
    for metric in ALL_METRICS:
        for judge, jr in runs.items():
            pair = pd.DataFrame({"s": jr.scores[metric], "g": gold[GOLD_COL[metric]]}).dropna()
            if pair.empty:
                continue
            rec = {"metric": metric, "judge": judge, "n": len(pair), "mae_vs_gold": (pair.s - pair.g).abs().mean()}
            if metric == "answer_correctness":
                rec["accuracy"] = (_band(pair.s) == pair.g).mean()
            else:
                y = _failure_true(metric, pair.g).astype(int)
                p = _failure_prob(metric, pair.s)
                yhat = _failure_pred(metric, pair.s, t).astype(int)
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
            records.append(rec)
    return pd.DataFrame(records)


def sme_alignment(runs: dict[str, JudgeRun], meta: pd.DataFrame, t: float) -> pd.DataFrame:
    """Does the judge flag the answers the SME marked incorrect? (any of faithfulness, relevance,
    toxicity, tone failing = 'bad'; context relevance is excluded since it grades retrieval)."""
    records = []
    for judge, jr in runs.items():
        d = jr.scores[SME_METRICS].join(meta["sme_correct"]).dropna()
        if d.empty:
            continue
        y = (1 - d["sme_correct"]).astype(int)
        p = pd.concat([_failure_prob(m, d[m]) for m in SME_METRICS], axis=1).max(axis=1)
        yhat = pd.concat([_failure_pred(m, d[m], t) for m in SME_METRICS], axis=1).any(axis=1).astype(int)
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


def agreement(llm: JudgeRun, jev: JudgeRun, t: float) -> pd.DataFrame:
    records = []
    for metric in ALL_METRICS:
        pair = pd.DataFrame({"llm": llm.scores[metric], "jev": jev.scores[metric]}).dropna()
        if pair.empty:
            continue
        a = _verdict(metric, pair.llm, t).astype(str)
        b = _verdict(metric, pair.jev, t).astype(str)
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


def consistency(all_runs: dict[str, list[JudgeRun]], t: float) -> pd.DataFrame:
    records = []
    for judge, runs in all_runs.items():
        if len(runs) < 2:
            continue
        base = runs[0].scores
        for metric in ALL_METRICS:
            changes, flips = [], []
            for other in runs[1:]:
                pair = pd.DataFrame({"a": base[metric], "b": other.scores[metric]}).dropna()
                changes.append((pair.a - pair.b).abs())
                flips.append(_verdict(metric, pair.a, t) != _verdict(metric, pair.b, t))
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


def jev_confidence(jev: JudgeRun, gold: pd.DataFrame, t: float, cutoff: float) -> pd.DataFrame:
    records = []
    for metric in ALL_METRICS:
        pair = pd.DataFrame({
            "s": jev.scores[metric],
            "c": jev.scores[f"{metric}_conf"],
            "g": gold[GOLD_COL[metric]],
        }).dropna()
        if pair.empty:
            continue
        correct = _verdict(metric, pair.s, t) == _verdict(metric, pair.g, t, gold=True)
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
        price_in, price_out = jj.PRICE_PER_M if judge == JEV else LLM_PRICES.get(ev.JUDGE_MODEL, (np.nan, np.nan))
        for jr in runs:
            lat = pd.Series([c["latency_s"] for c in jr.calls], dtype=float)
            tokens_in = sum(c["input_tokens"] for c in jr.calls)
            tokens_out = sum(c["output_tokens"] for c in jr.calls)
            cost = (tokens_in * price_in + tokens_out * price_out) / 1e6
            missing = jr.scores[BINARY_METRICS].isna().any(axis=1) | (
                meta["needs_correctness"] & jr.scores["answer_correctness"].isna()
            )
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
                "cost_usd": cost,
                "cost_per_1k_rows_usd": cost / n_rows * 1000,
            })
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
    parser = argparse.ArgumentParser(description="Compare JEV with the GPT-4o LLM-as-a-judge.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT, help="GT sheet (CSV) in the SME layout")
    parser.add_argument("--gold", default=str(DEFAULT_GOLD), help="gold-label CSV, or 'none' for real data")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="output folder")
    parser.add_argument("--repeats", type=int, default=2, help="runs per judge (>=2 measures consistency)")
    parser.add_argument("--workers", type=int, default=ev.MAX_WORKERS, help="concurrent calls, same for both")
    parser.add_argument("--threshold", type=float, default=0.5, help="score cut-off for pass/fail verdicts")
    parser.add_argument("--confidence", type=float, default=0.8, help="JEV high-confidence cut-off")
    parser.add_argument("--judges", choices=["both", "llm", "jev"], default="both")
    args = parser.parse_args()

    use_llm = args.judges in ("both", "llm")
    use_jev = args.judges in ("both", "jev")
    jev_key = jj.api_key()
    if use_llm:
        ev._client()
    if use_jev:
        jj.preflight(jev_key)

    df = ev.load_input(str(args.input))
    rows = jj.prepare_rows(df)
    meta = pd.DataFrame(rows).set_index("row_id")
    gold = None if args.gold.lower() == "none" else load_gold(Path(args.gold), meta)
    ev.MAX_WORKERS = args.workers
    t = args.threshold

    all_runs: dict[str, list[JudgeRun]] = {}
    llm_outputs: list[pd.DataFrame] = []
    jev_raws: list[dict] = []
    for run in range(1, args.repeats + 1):
        if use_llm:
            print(f"\n--- LLM judge ({ev.JUDGE_MODEL}) run {run}/{args.repeats} ---")
            jr, out = run_llm(df, meta, run)
            all_runs.setdefault(LLM, []).append(jr)
            llm_outputs.append(out)
            print(f"  {len(jr.calls)} calls in {jr.wall_s:.1f}s")
        if use_jev:
            print(f"\n--- JEV ({jj.JEV_MODEL}) run {run}/{args.repeats} ---")
            jr, raws = run_jev(rows, args.workers, jev_key, run)
            all_runs.setdefault(JEV, []).append(jr)
            jev_raws.extend(raws)
            print(f"  {len(jr.calls)} calls in {jr.wall_s:.1f}s")

    per_run = [{judge: runs[k] for judge, runs in all_runs.items()} for k in range(args.repeats)]
    acc = (
        _mean_over_runs([accuracy_vs_gold(r, gold, t) for r in per_run], ["metric", "judge"])
        if gold is not None else pd.DataFrame()
    )
    sme = _mean_over_runs([sme_alignment(r, meta, t) for r in per_run], ["judge"])
    agree = (
        _mean_over_runs([agreement(r[LLM], r[JEV], t) for r in per_run], ["metric"])
        if use_llm and use_jev else pd.DataFrame()
    )
    lat = latency_cost(all_runs, meta)
    cons = consistency(all_runs, t)
    conf = jev_confidence(all_runs[JEV][0], gold, t, args.confidence) if use_jev and gold is not None else None
    summary = head_to_head(acc, sme, lat, cons) if use_llm and use_jev else pd.DataFrame()
    first = per_run[0]
    per_row = per_row_table(meta, gold, first.get(LLM), first.get(JEV), t)

    jev_models = sorted({m for jr in all_runs.get(JEV, []) for m in jr.models})
    sme_yes = int(meta["sme_correct"].sum())
    setup = pd.DataFrame(
        [
            ("Input", str(args.input)),
            ("Rows (SME Yes / No)", f"{len(meta)} ({sme_yes} / {len(meta) - sme_yes})"),
            ("Gold labels", "none" if gold is None else str(args.gold)),
            ("LLM judge", f"{ev.JUDGE_MODEL} via OpenRouter, {ev.ROWS_PER_LLM_CALL} rows per call "
                          "(adi_gt_evaluator.py prompts and batching, unchanged)"),
            ("JEV", f"{', '.join(jev_models) or jj.JEV_MODEL} via {jj.JEV_URL}, 1 row per call, "
                    f"{len(jj.JEV_QUESTIONS)} Score questions (+1 correctness question for SME=No rows)"),
            ("Concurrency (both judges)", args.workers),
            ("Runs per judge", args.repeats),
            ("Pass/fail threshold on 0-1 scores", t),
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
    _print("Head-to-head", summary)
    if not acc.empty:
        _print("Accuracy vs gold", acc[[c for c in (
            "metric", "judge", "n", "gold_failures", "flagged", "accuracy", "precision", "recall", "f1", "auc", "brier"
        ) if c in acc]])
    _print("SME alignment", sme)
    _print("Judge agreement", agree)
    _print("Latency / cost / reliability", lat[[
        "judge", "run", "api_calls", "failed_calls", "rows_missing_scores", "wall_time_s", "call_p50_s",
        "call_p95_s", "input_tokens", "output_tokens", "cost_usd",
    ]])
    _print("Consistency across runs", cons)
    _print("JEV confidence", conf)
    print(f"\nWrote {xlsx}")


if __name__ == "__main__":
    main()
