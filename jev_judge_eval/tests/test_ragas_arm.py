"""Pure-function tests for the RAGAS-style arm's scoring (no API calls).

Verifies that the framework formulas (claim-level ratios, factual F1, 75/25
correctness composite, graded tone/toxicity) are computed from the
decomposition output exactly as documented.
"""
from __future__ import annotations

import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import judge_arms as arms


def _row(context="ctx", chunks=("chunk a", "chunk b")):
    return {
        "row_id": 0,
        "user_query": "query",
        "adi_response": "response",
        "adi_context": context,
        "adi_chunks": list(chunks),
        "prior_conversation": [],
        "reference_answer": "reference",
    }


def _parsed(**overrides):
    parsed = {
        "claims": [
            {"text": "c1", "supported_by_context": True, "supported_by_reference": True},
            {"text": "c2", "supported_by_context": False, "supported_by_reference": True},
            {"text": "c3", "supported_by_context": True, "supported_by_reference": False},
        ],
        "reference_claims": [
            {"text": "r1", "covered_by_response": True},
            {"text": "r2", "covered_by_response": False},
        ],
        "answer_statements": [
            {"text": "s1", "relevant_to_query": True},
            {"text": "s2", "relevant_to_query": True},
            {"text": "s3", "relevant_to_query": False},
        ],
        "chunk_verdicts": [{"index": 0, "relevant_to_query": True}, {"index": 1, "relevant_to_query": False}],
        "tone_level": 3,
        "toxicity_level": 0,
        "semantic_level": 2,
    }
    parsed.update(overrides)
    return parsed


class RagasScoringTests(unittest.TestCase):
    def test_generation_ratios(self):
        scores, _ = arms._ragas_scores_from(_parsed(), _row())
        self.assertAlmostEqual(scores["faithfulness"], 2 / 3)          # 2 of 3 claims supported
        self.assertAlmostEqual(scores["answer_relevance"], 2 / 3)      # 2 of 3 statements relevant
        self.assertAlmostEqual(scores["context_relevance"], 1 / 2)     # 1 of 2 chunks relevant

    def test_correctness_components_and_composite(self):
        scores, _ = arms._ragas_scores_from(_parsed(), _row())
        # factual precision = 2/3, recall = 1/2, F1 = 2PR/(P+R)
        self.assertAlmostEqual(scores["factual_precision"], 2 / 3)
        self.assertAlmostEqual(scores["factual_recall"], 1 / 2)
        f1 = 2 * (2 / 3) * (1 / 2) / ((2 / 3) + (1 / 2))
        self.assertAlmostEqual(scores["factual_correctness"], f1)
        semantic = 2 / 3
        self.assertAlmostEqual(scores["semantic_similarity"], semantic)
        self.assertAlmostEqual(scores["answer_correctness"], 0.75 * f1 + 0.25 * semantic)

    def test_tone_and_toxicity_normalize(self):
        scores, _ = arms._ragas_scores_from(_parsed(), _row())
        self.assertAlmostEqual(scores["tone_appropriateness"], 1.0)
        self.assertAlmostEqual(scores["toxicity"], 0.0)

    def test_no_claims_and_no_reference(self):
        parsed = _parsed(claims=[], reference_claims=[])
        scores, _ = arms._ragas_scores_from(parsed, _row())
        self.assertAlmostEqual(scores["faithfulness"], 1.0)
        self.assertAlmostEqual(scores["answer_relevance"], 2 / 3)
        self.assertAlmostEqual(scores["factual_precision"], 0.0)
        self.assertTrue(math.isnan(scores["factual_recall"]))
        self.assertTrue(math.isnan(scores["answer_correctness"]))

    def test_out_of_range_levels_are_flagged(self):
        parsed = _parsed(tone_level=5, toxicity_level=-1)
        scores, out_of_range = arms._ragas_scores_from(parsed, _row())
        self.assertEqual(out_of_range, 2)
        self.assertTrue(math.isnan(scores["tone_appropriateness"]))
        self.assertTrue(math.isnan(scores["toxicity"]))

    def test_user_prompt_uses_complete_state(self):
        row = _row(context="full-context-with-UNIQUE_MARKER")
        prompt = arms._ragas_user_prompt(row)
        self.assertIn("UNIQUE_MARKER", prompt)
        self.assertIn("reference", prompt)


if __name__ == "__main__":
    unittest.main()
