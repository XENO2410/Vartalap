"""Input-completeness tests: no context truncation and full history passing.

Locks in the rule that every judge-visible input field (retrieved context,
ordered chunks, reference answer, prior conversation) is passed in full.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import adi_gt_evaluator as ev
import jev_judge as jj
import judge_arms as arms
from evaluation_policy import parse_prior_conversation

LONG_CONTEXT = ("sentence about banking policies. " * 600) + "UNIQUE_TAIL_MARKER_XYZ"
HISTORY_JSON = '[{"role": "user", "content": "What is leave?"}, {"role": "assistant", "content": "12 days casual leave."}]'


def _row(history=None, context=LONG_CONTEXT):
    return {
        "row_id": 0,
        "user_query": "follow-up question",
        "adi_response": "short answer",
        "adi_context": context,
        "adi_chunks": ["chunk one", "chunk two"],
        "prior_conversation": parse_prior_conversation(history),
        "reference_answer": "reference answer",
        "needs_correctness": True,
    }


class ParseHistoryTests(unittest.TestCase):
    def test_parse_prior_conversation(self):
        turns = parse_prior_conversation(HISTORY_JSON)
        self.assertEqual(turns, [
            {"role": "user", "content": "What is leave?"},
            {"role": "assistant", "content": "12 days casual leave."},
        ])
        for bad in (None, "", "nan", "null", "[]", "{not json", '{"a": 1}'):
            self.assertEqual(parse_prior_conversation(bad), [])


class PromptCompletenessTests(unittest.TestCase):
    def test_metrics_prompt_keeps_full_context(self):
        prompt = ev.build_metrics_prompt([_row()])
        self.assertIn("UNIQUE_TAIL_MARKER_XYZ", prompt)
        self.assertGreater(len(prompt), len(LONG_CONTEXT))

    def test_metrics_prompt_includes_history(self):
        prompt = ev.build_metrics_prompt([_row(HISTORY_JSON)])
        self.assertIn("PRIOR_CONVERSATION:", prompt)
        self.assertIn("What is leave?", prompt)
        prompt_none = ev.build_metrics_prompt([_row(None)])
        self.assertIn("(none — this is the first turn)", prompt_none)


class JevPayloadTests(unittest.TestCase):
    def test_score_row_state_is_complete(self):
        captured = {}
        original = jj._post

        def fake_post(http, payload, max_attempts=5):
            captured["payload"] = payload
            return None, {"latency_s": 0.0, "attempts": 1, "input_tokens": 0,
                          "output_tokens": 0, "error": None}

        jj._post = fake_post
        try:
            jj.score_row(None, _row(HISTORY_JSON))
        finally:
            jj._post = original
        state = captured["payload"]["state"]
        self.assertEqual(state["retrieved_context"], LONG_CONTEXT)
        self.assertIn("UNIQUE_TAIL_MARKER_XYZ", state["retrieved_context"])
        self.assertEqual(len(state["prior_conversation"]), 2)
        self.assertEqual(state["retrieved_context_chunks"], ["chunk one", "chunk two"])


class ArmsStateTests(unittest.TestCase):
    def test_state_for_row_is_complete(self):
        state = arms._state_for_row(_row(HISTORY_JSON))
        self.assertEqual(state["retrieved_context"], LONG_CONTEXT)
        self.assertIn("UNIQUE_TAIL_MARKER_XYZ", state["retrieved_context"])
        self.assertEqual(len(state["prior_conversation"]), 2)
        self.assertEqual(state["retrieved_context_chunks"], ["chunk one", "chunk two"])


class PrepareRowsHistoryTests(unittest.TestCase):
    def test_prepare_rows_parses_history(self):
        df = pd.DataFrame([{
            "user_query": "q", "adi_response": "a", "adi_context": "ctx",
            "adi_chunks": "", "sme_correct": "Yes", "sme_correct_answer": "",
            "sme_product": "Cards", "sme_subproduct": "Credit",
            "Session ID": "s1", "Evaluation Split": "dev",
            "Session Turn": 2, "Session Length": 2,
            "Prior Conversation (JSON)": HISTORY_JSON,
            "adi_docs": "doc_a.pdf", "sme_expected_docs": "doc_a.pdf",
            "reference_answer": "ref",
        }])
        rows = jj.prepare_rows(df)
        self.assertEqual(len(rows), 1)
        self.assertEqual(len(rows[0]["prior_conversation"]), 2)
        self.assertEqual(rows[0]["prior_conversation"][0]["role"], "user")


if __name__ == "__main__":
    unittest.main()
