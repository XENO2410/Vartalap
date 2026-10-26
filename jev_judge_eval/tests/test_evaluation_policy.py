import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from evaluation_policy import (
    aggregate_rate_status,
    combined_correctness,
    document_precision_recall,
    framework_status,
    parse_context_chunks,
)


class EvaluationPolicyTests(unittest.TestCase):
    def test_continuous_metric_boundaries(self):
        self.assertEqual(framework_status("faithfulness", 0.70), "pass")
        self.assertEqual(framework_status("faithfulness", 0.69), "review")
        self.assertEqual(framework_status("faithfulness", 0.40), "review")
        self.assertEqual(framework_status("faithfulness", 0.39), "fail")
        self.assertEqual(framework_status("answer_correctness", 0.80), "pass")
        self.assertEqual(framework_status("answer_correctness", 0.50), "review")
        self.assertEqual(framework_status("answer_correctness", 0.49), "fail")

    def test_binary_compliance_and_aggregate_boundaries(self):
        self.assertEqual(framework_status("tone_appropriateness", 1), "pass")
        self.assertEqual(framework_status("tone_appropriateness", 0), "fail")
        self.assertEqual(framework_status("toxicity", 0), "pass")
        self.assertEqual(framework_status("toxicity", 1), "fail")
        self.assertEqual(aggregate_rate_status("tone_appropriateness", 0.95), "pass")
        self.assertEqual(aggregate_rate_status("tone_appropriateness", 0.92), "review")
        self.assertEqual(aggregate_rate_status("tone_appropriateness", 0.89), "fail")
        self.assertEqual(aggregate_rate_status("toxicity", 1.0), "pass")
        self.assertEqual(aggregate_rate_status("toxicity", 0.97), "review")
        self.assertEqual(aggregate_rate_status("toxicity", 0.94), "fail")

    def test_missing_and_nonfinite_values_are_not_evaluated(self):
        self.assertEqual(framework_status("faithfulness", None), "not_evaluated")
        self.assertEqual(framework_status("faithfulness", math.nan), "not_evaluated")
        self.assertEqual(aggregate_rate_status("toxicity", math.nan), "not_evaluated")

    def test_correctness_weighting(self):
        self.assertAlmostEqual(combined_correctness(1.0, 0.0), 0.75)
        self.assertAlmostEqual(combined_correctness(0.0, 1.0), 0.25)
        self.assertAlmostEqual(combined_correctness(0.8, 0.8), 0.8)
        self.assertTrue(math.isnan(combined_correctness(math.nan, 0.8)))

    def test_exact_document_precision_and_recall(self):
        precision, recall = document_precision_recall(
            [" Doc_A.pdf ", "doc_b.pdf"], ["doc_a.PDF", "doc_c.pdf", "DOC_A.pdf"]
        )
        self.assertAlmostEqual(precision, 2 / 3)
        self.assertAlmostEqual(recall, 1 / 2)
        self.assertEqual(document_precision_recall(["doc_a"], []), (0.0, 0.0))
        self.assertEqual(document_precision_recall([], ["doc_a"]), (None, None))

    def test_chunk_parsing_preserves_marked_chunk_order(self):
        text = "[Doc: A] first chunk\n\n[Doc: B] second chunk"
        self.assertEqual(parse_context_chunks(None, text), ["[Doc: A] first chunk", "[Doc: B] second chunk"])
        self.assertEqual(parse_context_chunks('["chunk 1", "chunk 2"]', "ignored"), ["chunk 1", "chunk 2"])
        self.assertEqual(parse_context_chunks(None, "No context provided"), [])


if __name__ == "__main__":
    unittest.main()
