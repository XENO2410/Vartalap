# JEV vs LLM-as-a-judge for ADI evaluation

Benchmarks TypeSafe's **JEV** (`jev-1.13.0`, a "System One" model that returns typed scores with
probabilities instead of generated text) against the **GPT-4o LLM-as-a-judge** used to evaluate ADI
(Axis Deep Intelligence) chatbot answers. It also includes a JEV-only evaluator with the same input
and output format as the LLM evaluator, so JEV can be tested on its own.

## What's here

| Path | Purpose |
| --- | --- |
| `adi_gt_evaluator.py` | Existing LLM judge: GPT-4o via OpenRouter, 5 rows per call, plus deterministic metrics |
| `jev_judge.py` | JEV judge: same sheet in, same metric columns out, plus a confidence per metric |
| `compare_judges.py` | Runs both judges on the same rows and writes the comparison workbook |
| `data/build_synthetic_dataset.py` | Regenerates the 35-row synthetic sheet and its designer labels |
| `data/synthetic_adi_gt_35.csv` | Synthetic ground-truth sheet in the SME layout (12 columns) |
| `data/synthetic_adi_gt_35_gold.csv` | The label each row was designed to have; used to measure judge accuracy |
| `results/` | Outputs (see below) |

## Setup

Python 3.10+ (tested on 3.12).

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env   # then fill in the keys
```

- `TYPESAFE_API_KEY`: JEV key from https://console.typesafe.ai/keys
- `OPENROUTER_API_KEY`: only needed for the GPT-4o judge (`adi_gt_evaluator.py`, `compare_judges.py`)

Keys are read from `.env` in this folder, then from the parent folder's `.env` (so it also works
inside the ADI repo). Never share a `.env` file.

## Run

```powershell
python jev_judge.py data/synthetic_adi_gt_35.csv results/jev_eval.xlsx        # JEV only
python adi_gt_evaluator.py data/synthetic_adi_gt_35.csv results/llm_eval.xlsx  # GPT-4o only
python compare_judges.py                                                       # head-to-head, 2 runs each
python compare_judges.py --input path/to/real_gt.csv --gold none               # real SME sheet, no labels
```

`compare_judges.py` options: `--repeats N` (runs per judge; 2 or more measures consistency),
`--workers N` (concurrent calls, same for both judges), `--threshold 0.5` (pass/fail cut-off on 0-1
scores), `--judges both|llm|jev`.

## Input sheet

A CSV with the SME columns: `User Query`, `Response by ADI`, `Content Retrieved by ADI`,
`Use case Tagged by ADI`, `Product Tagged by ADI`, `Subproduct Tagged by ADI`,
`Subproduct Tagged by ADI - comment`, `Document Name Retrieved by ADI`, `SME Employee ID`,
`Is ADI response Correct? (Yes/No)`, `If ADI response incorrect(Enter right response)`,
`Document Name(s) Expected to be Referred`.

Product/subproduct match also needs `Product as per SME` and `Subproduct as per SME` columns;
without them those rates show 0%.

## How JEV judges

JEV does not generate text. Each row is one request: the row is the `state`
(`user_query`, `chatbot_response`, `retrieved_context`) and every metric is a **Score** question
whose levels mirror the GPT-4o prompt. Faithfulness, for example:

0. Most claims are missing from or contradict the retrieved context
1. Some are supported, but a key fact (number, limit, rule, step) is not
2. Nearly all are supported; only a minor detail is not
3. Every claim is supported (or there are no factual claims, e.g. a polite refusal)

JEV returns a probability for each level plus a confidence. The score is normalised to 0-1 to
match the LLM judge. For rows the SME marked incorrect, an answer-correctness question carries the
SME's corrected answer inside that question only, so it cannot influence the other metrics.

## Outputs (`results/`)

| File | Contents |
| --- | --- |
| `jev_vs_llm_comparison.xlsx` | Main report. Sheets: Summary (head-to-head with winner), Setup, Accuracy_vs_Gold, SME_Alignment, Agreement, Latency_Cost, Consistency, JEV_Confidence, Per_Row |
| `summary.csv` | The Summary sheet as CSV |
| `per_row.csv` | Per row (run 1): designer label, both judges' scores, JEV confidence, metrics where the judges disagree, metrics where each judge was wrong |
| `llm_judge_run<N>.csv` | Full `adi_gt_evaluator.py` output for each GPT-4o run, including its written reasons |
| `jev_raw_responses.jsonl` | Raw JEV answers per row and run: level probabilities, confidence, latency, tokens, model version |
| `jev_eval.csv` / `jev_eval.xlsx` | `jev_judge.py` output: evaluator columns with JEV scores and confidences, plus a summary sheet |

## Results so far (35 synthetic rows, 2 runs per judge, 2026-10-12)

| | GPT-4o judge | JEV |
| --- | --- | --- |
| Agreement with designer labels (5 metrics) | 94.6% | 98.6% |
| Hallucinations caught | 5 / 10 | 10 / 10 |
| Agreement with SME Yes/No | 78.6% | 88.6% |
| SME-incorrect answers caught | 57% | 87% |
| Answer-correctness band accuracy | 80% | 73% |
| Median call latency | 4.1 s | 0.35 s |
| Cost per 1,000 rows | $2.23 | $0.046 |
| Verdict changes between runs | 0.5% | 0.5% |

Caveats: this is a small synthetic sample, and the designer labels and JEV's question wording were
written by the same person. Validate on a real SME-labelled sheet before deciding. JEV gives no
written reasons, so keep an LLM where explanations are needed.

All data in `data/` is synthetic, not real Axis Bank content.
