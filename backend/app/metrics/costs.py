"""Rough per-model USD/1M-token pricing (OpenRouter list prices, approx).

Used only for the observability cost estimate — not a source of truth.
"""
from __future__ import annotations


# (prompt_usd_per_1m, completion_usd_per_1m)
_COST_PER_1M: dict[str, tuple[float, float]] = {
    "openai/gpt-4o-mini": (0.15, 0.60),
    "openai/gpt-4o": (2.50, 10.00),
    "openai/gpt-4-turbo": (10.00, 30.00),
    "google/gemini-flash-1.5": (0.075, 0.30),
    "google/gemini-2.5-flash": (0.10, 0.40),
    "google/gemini-2.5-pro": (1.25, 5.00),
    "anthropic/claude-3.5-haiku": (0.80, 4.00),
    "anthropic/claude-3.5-sonnet": (3.00, 15.00),
    "meta-llama/llama-3.1-8b-instruct": (0.05, 0.10),
    "meta-llama/llama-3.1-70b-instruct": (0.35, 0.40),
    "faq-direct": (0.0, 0.0),
    "offline-stub": (0.0, 0.0),
}

_DEFAULT_RATES = (0.15, 0.60)


def usd_cost(model: str | None, prompt_tokens: int, completion_tokens: int) -> float:
    key = (model or "").lower().strip()
    prompt_rate, completion_rate = _COST_PER_1M.get(key, _DEFAULT_RATES)
    return round(
        (prompt_tokens / 1_000_000.0) * prompt_rate
        + (completion_tokens / 1_000_000.0) * completion_rate,
        6,
    )
