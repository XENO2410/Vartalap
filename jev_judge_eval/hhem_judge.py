"""Optional Vectara HHEM-2.1-Open adapter for faithfulness only.

Install optional dependencies from requirements-hhem.txt. Model weights download on first run.
The local HHEM model returns a consistency score for (retrieved context, answer) pairs; it is not
an all-metric judge and its threshold must be calibrated against held-out ADI labels.
"""
from __future__ import annotations

import time
from typing import Optional

import pandas as pd

MODEL_ID = "vectara/hallucination_evaluation_model"


def score_rows(rows: list[dict], batch_size: int = 16) -> tuple[pd.Series, list[dict], float, list[dict]]:
    from transformers import AutoModelForSequenceClassification

    total_started = time.perf_counter()
    load_started = time.perf_counter()
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_ID, trust_remote_code=True)
    model_load_s = time.perf_counter() - load_started
    pairs = [
        (row.get("adi_context", "") or "No retrieved evidence", row.get("adi_response", ""))
        for row in rows
    ]
    started = time.perf_counter()
    scores = []
    calls = []
    raw = []
    for start in range(0, len(pairs), batch_size):
        batch = pairs[start:start + batch_size]
        batch_started = time.perf_counter()
        predicted = model.predict(batch)
        values = predicted.detach().cpu().reshape(-1).tolist() if hasattr(predicted, "detach") else list(predicted)
        calls.append({
            "latency_s": time.perf_counter() - batch_started,
            "attempts": 1,
            "input_tokens": 0,
            "output_tokens": 0,
            "error": None,
            "batch_rows": len(batch),
        })
        scores.extend(float(value) for value in values)
        raw.extend({"row_id": row["row_id"], "model": MODEL_ID, "faithfulness": score}
                   for row, score in zip(rows[start:start + batch_size], values))
    inference_wall_s = time.perf_counter() - started
    wall = time.perf_counter() - total_started
    raw.insert(0, {"model": MODEL_ID, "model_load_s": model_load_s, "inference_wall_s": inference_wall_s})
    return pd.Series(scores, index=[row["row_id"] for row in rows], name="faithfulness"), calls, wall, raw
