"""Pure-function tests for compare_judges.py analysis — no API calls, no keys.

These exercise the dict-threshold contract, the missing-metric guards for
partial arms (e.g. HHEM faithfulness-only), the framework report scopes, the
dev-only threshold sweep, and the test-split tuning guard.
"""
from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import compare_judges as cj


def _scores() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "faithfulness": [0.1, 0.9],
            "answer_relevance": [0.9, 0.1],
            "context_relevance": [0.1, 0.9],
            "toxicity": [0.9, 0.1],
            "tone_appropriateness": [0.1, 0.9],
            "factual_precision": [0.5, 0.5],
            "factual_recall": [0.5, 0.5],
            "factual_correctness": [0.5, 0.5],
            "semantic_similarity": [0.5, 0.5],
            "answer_correctness": [0.5, 0.5],
        }
    )


def _gold() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "gold_faithful": [0.0, 1.0],
            "gold_answer_relevant": [1.0, 0.0],
            "gold_context_relevant": [0.0, 1.0],
            "gold_toxic": [1.0, 0.0],
            "gold_tone_professional": [0.0, 1.0],
            "gold_factual_precision": [0.5, 0.5],
            "gold_factual_recall": [0.5, 0.5],
            "gold_factual_correctness": [0.5, 0.5],
            "gold_semantic_similarity": [0.5, 0.5],
            "gold_answer_correctness": [0.5, 0.5],
        }
    )


def _run(label: str = "JEV") -> cj.JudgeRun:
    return cj.JudgeRun(label, 1, _scores(), [], 1.0)


def _meta() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "user_query": ["q1", "q2"],
            "sme_correct": [True, False],
            "product": ["Cards", "Loans"],
            "sub_product": ["Credit", "Home"],
            "session_id": ["s1", "s1"],
            "evaluation_split": ["dev", "test"],
            "session_turn": [1, 2],
            "session_length": [2, 2],
            "retrieval_precision_at_k": [1.0, 0.5],
            "retrieval_recall_at_k": [1.0, 0.5],
        }
    )


class ThresholdContractTests(unittest.TestCase):
    def test_accuracy_vs_gold_accepts_dict_thresholds(self):
        out = cj.accuracy_vs_gold({"JEV": _run()}, _gold(), {"faithfulness": 0.5})
        self.assertEqual(len(out), 10)  # one row per metric for the one judge
        self.assertIn("accuracy", out.columns)

    def test_scalar_threshold_is_rejected(self):
        # The analysis functions are dict-only; main() normalizes the CLI scalar.
        with self.assertRaises((AttributeError, TypeError)):
            cj.accuracy_vs_gold({"JEV": _run()}, _gold(), 0.5)

    def test_sme_alignment_accepts_dict_thresholds(self):
        out = cj.sme_alignment({"JEV": _run()}, _meta(), {"faithfulness": 0.5})
        self.assertEqual(len(out), 1)
        self.assertIn("accuracy", out.columns)


class PartialArmTests(unittest.TestCase):
    def test_faithfulness_only_arm_is_skipped_where_not_applicable(self):
        partial = cj.JudgeRun(
            "HHEM faithfulness", 1,
            pd.DataFrame({"faithfulness": [0.1, 0.9]}), [], 1.0,
        )
        acc = cj.accuracy_vs_gold({"HHEM faithfulness": partial}, _gold(), {})
        self.assertEqual(acc["metric"].unique().tolist(), ["faithfulness"])
        sme = cj.sme_alignment({"HHEM faithfulness": partial}, _meta(), {})
        self.assertTrue(sme.empty)
        agree = cj.agreement(partial, _run(), {})
        self.assertEqual(agree["metric"].unique().tolist(), ["faithfulness"])

    def test_consistency_skips_missing_metrics(self):
        partial = cj.JudgeRun(
            "HHEM faithfulness", 1,
            pd.DataFrame({"faithfulness": [0.1, 0.9]}), [], 1.0,
        )
        partial2 = cj.JudgeRun(
            "HHEM faithfulness", 2,
            pd.DataFrame({"faithfulness": [0.2, 0.8]}), [], 1.0,
        )
        out = cj.consistency({"HHEM faithfulness": [partial, partial2]}, {})
        self.assertEqual(out["metric"].unique().tolist(), ["faithfulness"])


class FrameworkReportTests(unittest.TestCase):
    def test_query_level_and_aggregates(self):
        query_level, aggregates = cj.framework_reports({"JEV": [_run()]}, _meta())
        self.assertEqual(len(query_level), 2)
        self.assertIn("platform", aggregates["scope"].values)
        for scope in ("platform", "product", "sub_product", "session"):
            self.assertIn(scope, aggregates["scope"].values)
        # retrieval columns are descriptive-only in aggregates
        retrieval = aggregates[aggregates["metric"] == "retrieval_precision_at_k"]
        self.assertEqual(retrieval["framework_status"].unique().tolist(), ["descriptive_only"])

    def test_threshold_sweep_dev_only(self):
        sweep = cj.threshold_sweep({"JEV": _run()}, _gold().iloc[:1])
        self.assertEqual(len(sweep), 13 * 5)  # 13 thresholds x 5 binary metrics
        self.assertIn("development_threshold", sweep.columns)

    def test_decision_policy_table(self):
        table = cj.decision_policy_table()
        self.assertIn("answer_correctness", table["metric"].values)
        self.assertIn("lifecycle", table["metric"].values)
        self.assertTrue((table["formula_or_note"].str.contains("DEFERRED")).any())

    def test_arm_summary(self):
        acc = cj.accuracy_vs_gold({"JEV": _run()}, _gold(), {"faithfulness": 0.5})
        sme = cj.sme_alignment({"JEV": _run()}, _meta(), {"faithfulness": 0.5})
        lat = cj.latency_cost({"JEV": [_run()]}, _meta())
        summary = cj.arm_summary(acc, sme, lat)
        self.assertEqual(summary["arm"].unique().tolist(), ["JEV"])
        self.assertIn("mean_binary_framework_accuracy", summary.columns)

    def test_jev_confidence_signature(self):
        # Regression: main() calls jev_confidence(judge_run, gold, cutoff, thresholds).
        run = _run()
        for metric in cj.ALL_METRICS:
            run.scores[f"{metric}_conf"] = [0.9, 0.6]
        out = cj.jev_confidence(run, _gold(), 0.8, {"faithfulness": 0.5})
        self.assertIn("faithfulness", out["metric"].values)
        self.assertIn("confidence_when_right", out.columns)

    def test_run_jev_models_is_hashable(self):
        # Regression: run_jev must pass the model-name set, not the raw dicts,
        # to JudgeRun.models (iterated by main()'s setup line).
        fake_scores = _scores().copy()
        original = cj.jj.score_rows
        cj.jj.score_rows = lambda rows, workers, key: (fake_scores, [], 1.0, [{"model": "jev-1.13.0"}])
        try:
            judge_run, _ = cj.run_jev([], 1, "k", 1)
        finally:
            cj.jj.score_rows = original
        self.assertEqual(judge_run.models, {"jev-1.13.0"})


class CliGuardTests(unittest.TestCase):
    def test_test_split_refuses_tuning(self):
        result = subprocess.run(
            [sys.executable, "-m", "compare_judges", "--split", "test", "--tune"],
            capture_output=True, text=True, cwd=str(Path(__file__).resolve().parents[1]),
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("not allowed", result.stderr or result.stdout)


if __name__ == "__main__":
    unittest.main()
