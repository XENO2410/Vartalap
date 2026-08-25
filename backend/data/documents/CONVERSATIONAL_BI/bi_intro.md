# Conversational BI — Getting Started

## What It Is
The `Conversational BI` bubble routes natural-language questions to the
Text-to-SQL agent, which drafts SQL against the reporting data mart, executes
it read-only, and returns a formatted result set.

## Available Datasets
- `customers` — one row per customer, with segment, branch, onboarding date.
- `accounts` — one row per account, product, balance, status.
- `transactions` — one row per transaction, txn_type, channel, amount.

Additional derived views are added quarterly; see the DDL under
`FINANCIAL_ADVISOR/mutual_funds.md` etc. for illustrative examples.

## Good Prompts
- "How many customers opened SAVINGS accounts?"
- "Top 5 customers by savings balance in Mumbai branches."
- "Average NEFT transaction amount last month by channel."
- "List customers with dormant SAVINGS accounts and balance under 5000."

## Guardrails
The engine will refuse to run SQL that:
- Writes data (INSERT / UPDATE / DELETE / DROP / ALTER / ATTACH).
- References tables outside the whitelisted set.
- Returns more than 5,000 rows in a single call.

## Limitations
- Text2SQL cannot answer questions that depend on documents (use the RAG
  bubbles for those).
- It does not yet handle time-series joins across all history — restrict to
  90 days for stable results.

## Reference
`CBI-INTRO-2026-01` · Owner: BI Platform team.
