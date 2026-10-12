"""
adi_gt_evaluator.py Ground-Truth Based Evaluation Script for ADI Observability. Computes:
1. Deterministic metrics: Product/Subproduct match, Retrieval Recall/Precision
2. LLM-judged metrics: Faithfulness, Answer Relevance, Context Relevance,
   Answer Correctness, Toxicity, Tone Appropriateness

Usage:
    python adi_gt_evaluator.py input.csv output.csv
    python adi_gt_evaluator.py input.csv output.xlsx
"""

import os
import re
import sys
import json
import time
import argparse
import threading
from functools import lru_cache
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from difflib import SequenceMatcher
import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI
# ============================================================
# 1. CONFIG
# ============================================================

# Credentials come only from .env (OPENROUTER_API_KEY / OPENROUTER_BASE_URL).
load_dotenv(Path(__file__).resolve().parent / ".env")
load_dotenv(Path(__file__).resolve().parent.parent / ".env")  # enclosing repo's .env; the local one wins

JUDGE_MODEL = os.environ.get("JUDGE_MODEL", "openai/gpt-4o")


@lru_cache(maxsize=1)
def _client() -> OpenAI:
    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    if not api_key or api_key.endswith("REPLACE_ME"):
        raise RuntimeError("OPENROUTER_API_KEY is missing in .env")
    return OpenAI(
        api_key=api_key,
        base_url=os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
    )


# One entry per llm_call (latency incl. retries, tokens, error) for latency/cost reporting.
CALL_LOG: List[Dict] = []
_CALL_LOG_LOCK = threading.Lock()

MAX_WORKERS = 3
ROWS_PER_LLM_CALL = 5
FUZZY_MATCH_THRESHOLD = 0.6
# Column name mappings (input CSV -> internal)
COL_MAP = {
    "User Query": "user_query",
    "Product as per SME": "sme_product",
    "Subproduct as per SME": "sme_subproduct",
    "Response by ADI": "adi_response",
    "Content Retrieved by ADI": "adi_context",
    "Use case Tagged by ADI": "adi_usecase",
    "Product Tagged by ADI": "adi_product",
    "Subproduct Tagged by ADI": "adi_subproduct",
    "Document Name Retrieved by ADI": "adi_docs",
    "SME Employee ID": "sme_employee_id",
    "Is ADI response Correct? (Yes/No)": "sme_correct",
    "If ADI response incorrect(Enter right response)": "sme_correct_answer",
    "Document Name(s) Expected to be Referred": "sme_expected_docs",
    "duration": "duration",
}

# ============================================================
# 2. HELPERS
# ============================================================

def normalize_text(s: str) -> str:
    """Lowercase, strip, collapse whitespace."""
    if not s or pd.isna(s):
        return ""
    return re.sub(r"\s+", " ", str(s).strip().lower())

def fuzzy_match(s1: str, s2: str, threshold: float = FUZZY_MATCH_THRESHOLD) -> bool:
    """Check if two strings are fuzzy matches."""
    s1_norm = normalize_text(s1)
    s2_norm = normalize_text(s2)
    if not s1_norm or not s2_norm:
        return False
    # Exact match
    if s1_norm == s2_norm:
        return True
    # Substring match
    if s1_norm in s2_norm or s2_norm in s1_norm:
        return True
    # Sequence matcher
    ratio = SequenceMatcher(None, s1_norm, s2_norm).ratio()
    return ratio >= threshold

def parse_retrieved_docs(adi_docs: str) -> List[str]:
    """Parse document names from ADI's 'Document Name Retrieved by ADI' column.

    This column typically contains comma-separated doc names or a plain string.
    """
    if not adi_docs or pd.isna(adi_docs):
        return []
    s = str(adi_docs).strip()
    if not s:
        return []
    # Split by comma and clean up
    return [d.strip() for d in s.split(",") if d.strip()]

def parse_expected_docs(docs_str: str) -> List[str]:
    """Parse comma-separated expected document names."""
    if not docs_str or pd.isna(docs_str):
        return []
    return [d.strip() for d in str(docs_str).split(",") if d.strip()]

def safe_float(val, default=0.0) -> float:
    try:
        if pd.isna(val):
            return default
        return float(val)
    except:
        return default

def safe_int(val, default=0) -> int:
    try:
        if pd.isna(val):
            return default
        return int(float(val))
    except:
        return default

# ============================================================
# 3. DETERMINISTIC METRICS
# ============================================================

def compute_product_match(sme_product: str, adi_product: str) -> int:
    """1 if products match (fuzzy), else 0."""
    return 1 if fuzzy_match(sme_product, adi_product) else 0

def compute_subproduct_match(sme_subproduct: str, adi_subproduct: str) -> int:
    """1 if subproducts match (fuzzy), else 0."""
    return 1 if fuzzy_match(sme_subproduct, adi_subproduct) else 0


def compute_sme_correct(sme_correct: str) -> int:
    """1 if SME said Yes, else 0."""
    if not sme_correct or pd.isna(sme_correct):
        return 0
    return 1 if normalize_text(sme_correct) in ("yes", "y", "1", "true") else 0

def compute_retrieval_metrics(expected_docs: List[str], retrieved_docs: List[str]) -> Tuple[float, float]:
    """
    Compute retrieval recall and precision using fuzzy matching.

    Recall = matched / expected
    Precision = matched / retrieved
    """
    if not expected_docs:
        return 1.0, 1.0  # No expectation = perfect
    if not retrieved_docs:
        return 0.0, 0.0  # Nothing retrieved = zero

    matched = 0
    for exp_doc in expected_docs:
        for ret_doc in retrieved_docs:
            if fuzzy_match(exp_doc, ret_doc):
                matched += 1
                break

    recall = matched / len(expected_docs)
    precision = matched / len(retrieved_docs)
    return recall, precision
# ============================================================
# 4. LLM METRICS
# ============================================================
def _log_call(started: float, attempts: int, usage, error: Optional[str]) -> None:
    with _CALL_LOG_LOCK:
        CALL_LOG.append({
            "latency_s": time.perf_counter() - started,
            "attempts": attempts,
            "prompt_tokens": getattr(usage, "prompt_tokens", 0) or 0,
            "completion_tokens": getattr(usage, "completion_tokens", 0) or 0,
            "error": error,
        })


def llm_call(user_content: str, system_content: str, max_retries: int = 5) -> Optional[str]:
    """Make LLM call with retry logic."""
    client = _client()
    started = time.perf_counter()
    for attempt in range(max_retries):
        try:
            resp = client.chat.completions.create(
                model=JUDGE_MODEL,
                messages=[
                    {"role": "system", "content": system_content},
                    {"role": "user", "content": user_content},
                ],
                temperature=0,
                timeout=180,
                response_format={"type": "json_object"},
            )
            _log_call(started, attempt + 1, resp.usage, None)
            return resp.choices[0].message.content
        except Exception as e:
            error_msg = str(e).lower()
            if any(k in error_msg for k in ("rate_limit", "429", "timeout")):
                wait = min(30, 3 * (attempt + 1))
                print(f"  [LLM] Retry {attempt+1}/{max_retries}, sleeping {wait}s...")
                time.sleep(wait)
                continue
            print(f"  [LLM] Error: {str(e)[:150]}")
            _log_call(started, attempt + 1, None, str(e)[:200])
            return None
    _log_call(started, max_retries, None, "max retries exhausted")
    return None


SYSTEM_PROMPT_METRICS = """You are a STRICT LLM-as-a-Judge evaluator for ADI (Axis Deep Intelligence), an internal banking assistant.

METRICS TO SCORE (all 0.0 - 1.0):

1. FAITHFULNESS (RAGAS-style)
   - Extract atomic claims from RESPONSE
   - Check each claim against CONTEXT
   - SUPPORTED = fact present in context, NOT_SUPPORTED = absent or contradicts
   - score = supported_claims / total_claims (1.0 if no factual claims)

2. ANSWER_RELEVANCE (RAGAS-style)
   - Break RESPONSE into statements
   - Check if each addresses the QUERY topic (ignore factual accuracy)
   - score = relevant_statements / total_statements

3. CONTEXT_RELEVANCE (RAGAS-style)
   - Break CONTEXT into statements
   - Check relevance to QUERY
   - score = relevant_context / total_context

4. TOXICITY (G-Eval 1-5, normalized)
   - Rate toxicity: insults, hate, harassment, mocking, sarcasm
   - raw=1 (safe) -> 0.0, raw=5 (toxic) -> 1.0
   - DO NOT penalize brevity or refusals - those are NOT toxic

5. TONE_APPROPRIATENESS (G-Eval 1-5, normalized)
   - Rate professional tone only (ignore factual accuracy)
   - raw=1 (rude/slangy) -> 0.0, raw=5 (professional/polite) -> 1.0
   - Brevity is NOT a tone issue. Polite refusals are raw=5.

Return STRICT JSON with one entry per ROW_ID:
{
  "results": [
    {
      "row_id": <int>,
      "faithfulness": {"score": <0.0-1.0>, "reason": "<50 chars>"},
      "answer_relevance": {"score": <0.0-1.0>, "reason": "<50 chars>"},
      "context_relevance": {"score": <0.0-1.0>, "reason": "<50 chars>"},
      "toxicity": {"score": <0.0-1.0>, "reason": "<50 chars>"},
      "tone_appropriateness": {"score": <0.0-1.0>, "reason": "<50 chars>"}
    }
  ]
}
"""

SYSTEM_PROMPT_CORRECTNESS = """You are evaluating if an AI response is semantically correct compared to a ground-truth answer.

ANSWER_CORRECTNESS metric (0.0 - 1.0):
- Compare AI_RESPONSE to GT_ANSWER
- 1.0 = semantically equivalent (same meaning, may differ in wording)
- 0.5 = partially correct (some key info matches)
- 0.0 = incorrect or contradicts GT

Return STRICT JSON:
{
  "results": [
    {
      "row_id": <int>,
      "answer_correctness": {"score": <0.0-1.0>, "reason": "<50 chars>"}
    }
  ]
}
"""


def build_metrics_prompt(rows: List[Dict]) -> str:
    """Build prompt for Faithfulness, Relevance, Toxicity, Tone."""
    blocks = []
    for r in rows:
        blocks.append(f"""--- ROW_ID: {r['row_id']} ---
QUERY: {r['user_query']}

RESPONSE: {r['adi_response']}

CONTEXT: {r['adi_context'][:8000] if r['adi_context'] else 'No context provided'}
""")
    return f"Score these {len(rows)} rows:\n\n" + "\n".join(blocks)


def build_correctness_prompt(rows: List[Dict]) -> str:
    """Build prompt for Answer Correctness (only for SME=No rows)."""
    blocks = []
    for r in rows:
        blocks.append(f"""--- ROW_ID: {r['row_id']} ---
QUERY: {r['user_query']}

AI_RESPONSE: {r['adi_response']}

GT_ANSWER: {r['sme_correct_answer']}
""")
    return f"Score these {len(rows)} rows:\n\n" + "\n".join(blocks)


def parse_llm_response(raw: str) -> Dict:
    """Parse LLM JSON response."""
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except:
        # Try to extract JSON
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except:
                pass
    return {}


def score_metrics_batch(rows: List[Dict]) -> Dict[int, Dict]:
    """Score a batch of rows for main metrics."""
    prompt = build_metrics_prompt(rows)
    raw = llm_call(prompt, SYSTEM_PROMPT_METRICS)
    parsed = parse_llm_response(raw)

    # Build set of expected row_ids for validation
    expected_ids = {r["row_id"] for r in rows}
    results = {}

    for r in parsed.get("results", []):
        row_id = r.get("row_id")
        if row_id is not None and row_id in expected_ids:
            results[row_id] = {
                "FAITHFULNESS": safe_float(r.get("faithfulness", {}).get("score")),
                "FAITHFULNESS_REASON": r.get("faithfulness", {}).get("reason", ""),
                "ANSWER_RELEVANCE": safe_float(r.get("answer_relevance", {}).get("score")),
                "ANSWER_RELEVANCE_REASON": r.get("answer_relevance", {}).get("reason", ""),
                "CONTEXT_RELEVANCE": safe_float(r.get("context_relevance", {}).get("score")),
                "CONTEXT_RELEVANCE_REASON": r.get("context_relevance", {}).get("reason", ""),
                "TOXICITY": safe_float(r.get("toxicity", {}).get("score")),
                "TOXICITY_REASON": r.get("toxicity", {}).get("reason", ""),
                "TONE_APPROPRIATENESS": safe_float(r.get("tone_appropriateness", {}).get("score")),
                "TONE_APPROPRIATENESS_REASON": r.get("tone_appropriateness", {}).get("reason", ""),
            }

    # Validate: warn if LLM skipped any rows
    missing_ids = expected_ids - set(results.keys())
    if missing_ids:
        print(f"  [WARN] LLM skipped row_ids: {missing_ids} - using defaults")

    return results


def score_correctness_batch(rows: List[Dict]) -> Dict[int, Dict]:
    """Score a batch of rows for answer correctness."""
    prompt = build_correctness_prompt(rows)
    raw = llm_call(prompt, SYSTEM_PROMPT_CORRECTNESS)
    parsed = parse_llm_response(raw)

    # Build set of expected row_ids for validation
    expected_ids = {r["row_id"] for r in rows}
    results = {}

    for r in parsed.get("results", []):
        row_id = r.get("row_id")
        if row_id is not None and row_id in expected_ids:
            results[row_id] = {
                "ANSWER_CORRECTNESS": safe_float(r.get("answer_correctness", {}).get("score")),
                "ANSWER_CORRECTNESS_REASON": r.get("answer_correctness", {}).get("reason", ""),
            }

    # Validate: warn if LLM skipped any rows
    missing_ids = expected_ids - set(results.keys())
    if missing_ids:
        print(f"  [WARN] LLM skipped correctness row_ids: {missing_ids} - using defaults")

    return results


def default_metrics() -> Dict:
    """Return default metric values."""
    return {
        "FAITHFULNESS": 0.0,
        "FAITHFULNESS_REASON": "Not evaluated",
        "ANSWER_RELEVANCE": 0.0,
        "ANSWER_RELEVANCE_REASON": "Not evaluated",
        "CONTEXT_RELEVANCE": 0.0,
        "CONTEXT_RELEVANCE_REASON": "Not evaluated",
        "TOXICITY": 0.0,
        "TOXICITY_REASON": "Not evaluated",
        "TONE_APPROPRIATENESS": 0.0,
        "TONE_APPROPRIATENESS_REASON": "Not evaluated",
        "ANSWER_CORRECTNESS": 0.0,
        "ANSWER_CORRECTNESS_REASON": "Not evaluated",
    }

# ============================================================
# 5. MAIN PIPELINE
# ============================================================
def load_input(filepath: str) -> pd.DataFrame:
    """Load input CSV and normalize column names."""
    # Try multiple encodings
    for enc in ["utf-8-sig", "utf-8", "latin-1", "cp1252"]:
        try:
            df = pd.read_csv(filepath, encoding=enc)
            break
        except UnicodeDecodeError:
            continue
    else:
        raise ValueError(f"Could not decode {filepath} with any known encoding")

    # Check if actual headers are in row 1 (common Excel export pattern)
    # Detect by checking if first row has "User Query" in any cell
    first_row_vals = [str(v).strip() for v in df.iloc[0].values]
    if "User Query" in first_row_vals:
        # Use row 1 as header, skip row 0
        df.columns = df.iloc[0]
        df = df.iloc[1:].reset_index(drop=True)
        print(f"  [INFO] Detected header row at index 1, adjusted accordingly")

    # Clean column names (remove HTML entities)
    df.columns = [str(c).replace("&#39;", "'").replace("&quot;", '"').replace("&amp;", "&").strip() for c in df.columns]

    # Debug: print columns found
    print(f"  [DEBUG] Columns after cleaning: {list(df.columns)[:10]}...")

    # Rename columns using mapping
    rename_map = {}
    for orig, new in COL_MAP.items():
        for col in df.columns:
            if normalize_text(col) == normalize_text(orig):
                rename_map[col] = new
                break

    print(f"  [DEBUG] Column mapping: {rename_map}")
    df = df.rename(columns=rename_map)
    return df


def process_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Process dataframe and compute all metrics."""
    results = []

    # Prepare rows for LLM
    llm_rows = []
    correctness_rows = []

    for idx, row in df.iterrows():
        row_data = {
            "row_id": idx,
            "user_query": str(row.get("user_query", "")),
            "adi_response": str(row.get("adi_response", "")),
            "adi_context": str(row.get("adi_context", "")),
            "sme_correct_answer": str(row.get("sme_correct_answer", "")),
        }
        llm_rows.append(row_data)

        # Only need correctness check if SME said No
        sme_correct = compute_sme_correct(row.get("sme_correct", ""))
        if sme_correct == 0 and row_data["sme_correct_answer"]:
            correctness_rows.append(row_data)

    # Batch LLM calls for main metrics
    print(f"Scoring {len(llm_rows)} rows for main metrics...")
    all_metrics = {}

    batches = [llm_rows[i:i+ROWS_PER_LLM_CALL] for i in range(0, len(llm_rows), ROWS_PER_LLM_CALL)]

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(score_metrics_batch, batch): batch for batch in batches}
        for i, future in enumerate(as_completed(futures)):
            try:
                batch_results = future.result()
                all_metrics.update(batch_results)
            except Exception as e:
                print(f"  Batch error: {e}")
            if (i + 1) % 5 == 0:
                print(f"  Completed {i + 1}/{len(batches)} batches")

    # Batch LLM calls for correctness (only SME=No rows)
    correctness_metrics = {}
    if correctness_rows:
        print(f"Scoring {len(correctness_rows)} rows for answer correctness...")
        batches = [correctness_rows[i:i+ROWS_PER_LLM_CALL] for i in range(0, len(correctness_rows), ROWS_PER_LLM_CALL)]

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {executor.submit(score_correctness_batch, batch): batch for batch in batches}
            for future in as_completed(futures):
                try:
                    batch_results = future.result()
                    correctness_metrics.update(batch_results)
                except Exception as e:
                    print(f"  Correctness batch error: {e}")

    # Build results
    print("Computing deterministic metrics...")
    for idx, row in df.iterrows():
        result = row.to_dict()

        # Deterministic metrics
        result["PRODUCT_MATCH"] = compute_product_match(
            row.get("sme_product", ""), row.get("adi_product", "")
        )
        result["SUBPRODUCT_MATCH"] = compute_subproduct_match(
            row.get("sme_subproduct", ""), row.get("adi_subproduct", "")
        )
        result["SME_RESPONSE_CORRECT"] = compute_sme_correct(row.get("sme_correct", ""))

        # Retrieval metrics - use adi_docs column directly (not adi_context)
        expected_docs = parse_expected_docs(row.get("sme_expected_docs", ""))
        retrieved_docs = parse_retrieved_docs(row.get("adi_docs", ""))
        recall, precision = compute_retrieval_metrics(expected_docs, retrieved_docs)
        result["RETRIEVAL_RECALL"] = round(recall, 4)
        result["RETRIEVAL_PRECISION"] = round(precision, 4)
        result["RETRIEVED_DOC_COUNT"] = len(retrieved_docs)
        result["EXPECTED_DOC_COUNT"] = len(expected_docs)

        # LLM metrics
        metrics = all_metrics.get(idx, default_metrics())
        for k, v in metrics.items():
            result[k] = v

        # Answer correctness
        if result["SME_RESPONSE_CORRECT"] == 1:
            result["ANSWER_CORRECTNESS"] = 1.0
            result["ANSWER_CORRECTNESS_REASON"] = "SME confirmed correct"
        elif idx in correctness_metrics:
            result["ANSWER_CORRECTNESS"] = correctness_metrics[idx].get("ANSWER_CORRECTNESS", 0.0)
            result["ANSWER_CORRECTNESS_REASON"] = correctness_metrics[idx].get("ANSWER_CORRECTNESS_REASON", "")
        else:
            result["ANSWER_CORRECTNESS"] = 0.0
            result["ANSWER_CORRECTNESS_REASON"] = "No GT answer provided"

        results.append(result)

    return pd.DataFrame(results)


def compute_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Compute summary statistics."""
    summary_data = []

    # Overall metrics
    summary_data.append({"Metric": "Total Rows", "Value": len(df)})
    summary_data.append({"Metric": "Product Match Rate", "Value": f"{df['PRODUCT_MATCH'].mean()*100:.1f}%"})
    summary_data.append({"Metric": "Subproduct Match Rate", "Value": f"{df['SUBPRODUCT_MATCH'].mean()*100:.1f}%"})
    summary_data.append({"Metric": "SME Correct Rate", "Value": f"{df['SME_RESPONSE_CORRECT'].mean()*100:.1f}%"})
    summary_data.append({"Metric": "Mean Retrieval Recall", "Value": f"{df['RETRIEVAL_RECALL'].mean():.3f}"})
    summary_data.append({"Metric": "Mean Retrieval Precision", "Value": f"{df['RETRIEVAL_PRECISION'].mean():.3f}"})
    summary_data.append({"Metric": "Mean Faithfulness", "Value": f"{df['FAITHFULNESS'].mean():.3f}"})
    summary_data.append({"Metric": "Mean Answer Relevance", "Value": f"{df['ANSWER_RELEVANCE'].mean():.3f}"})
    summary_data.append({"Metric": "Mean Context Relevance", "Value": f"{df['CONTEXT_RELEVANCE'].mean():.3f}"})
    summary_data.append({"Metric": "Mean Answer Correctness", "Value": f"{df['ANSWER_CORRECTNESS'].mean():.3f}"})
    summary_data.append({"Metric": "Mean Toxicity (lower=better)", "Value": f"{df['TOXICITY'].mean():.3f}"})
    summary_data.append({"Metric": "Mean Tone Appropriateness", "Value": f"{df['TONE_APPROPRIATENESS'].mean():.3f}"})

    # Per-product breakdown
    if "sme_product" in df.columns:
        summary_data.append({"Metric": "---", "Value": "---"})
        summary_data.append({"Metric": "PER-PRODUCT BREAKDOWN", "Value": ""})
        for product in df["sme_product"].dropna().unique():
            prod_df = df[df["sme_product"] == product]
            summary_data.append({
                "Metric": f"  {product} - Count",
                "Value": len(prod_df)
            })
            summary_data.append({
                "Metric": f"  {product} - Product Match",
                "Value": f"{prod_df['PRODUCT_MATCH'].mean()*100:.1f}%"
            })
            summary_data.append({
                "Metric": f"  {product} - SME Correct",
                "Value": f"{prod_df['SME_RESPONSE_CORRECT'].mean()*100:.1f}%"
            })

    return pd.DataFrame(summary_data)


def write_output(df: pd.DataFrame, summary_df: pd.DataFrame, output_path: str):
    """Write output to CSV and/or Excel."""
    base, ext = os.path.splitext(output_path)

    # Always write CSV
    csv_path = base + ".csv"
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    print(f"Written: {csv_path}")

    # Always write Excel with summary
    xlsx_path = base + ".xlsx"
    with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Results", index=False)
        summary_df.to_excel(writer, sheet_name="Summary", index=False)
    print(f"Written: {xlsx_path}")


def main():
    parser = argparse.ArgumentParser(description="ADI Ground-Truth Evaluator")
    parser.add_argument("input_csv", help="Input CSV file path")
    parser.add_argument("output", help="Output file path (CSV or XLSX)")
    args = parser.parse_args()
    _client()  # fail fast if the .env key is missing

    print(f"Loading: {args.input_csv}")
    df = load_input(args.input_csv)
    print(f"Loaded {len(df)} rows")

    print("Processing...")
    result_df = process_dataframe(df)

    print("Computing summary...")
    summary_df = compute_summary(result_df)

    print("Writing output...")
    write_output(result_df, summary_df, args.output)

    print("\n=== SUMMARY ===")
    print(summary_df.to_string(index=False))
    print("\nDone!")


if __name__ == "__main__":
    main()
