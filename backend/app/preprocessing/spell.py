"""Lightweight spell corrector.

Uses `rapidfuzz` for nearest-word matching against a small vocabulary of the
common banking / HR / IT terms found in the corpus. This purposely stays
deterministic so replay-based evaluation is stable.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List

from rapidfuzz import fuzz, process


_VOCAB: list[str] = [
    # Product / process
    "kyc", "aml", "cif", "cbs", "cbo", "loan", "credit", "debit", "salary",
    "account", "balance", "opening", "closing", "statement", "transaction",
    "policy", "leave", "appraisal", "rehiring", "reimbursement", "onboarding",
    "attendance", "payroll", "provident", "gratuity", "insurance", "medical",
    # Systems
    "unidesk", "kaleidoscope", "primectl", "oll", "edgerewards", "tradax",
    "finacle", "trracs", "gps", "azure", "openai", "chroma",
    # Support / channels
    "helpdesk", "ticket", "escalation", "download", "form", "annexure",
    # Bubble names
    "hr", "cr", "status", "aha", "law", "download", "conversational",
    "financial", "advisor",
]


@dataclass
class SpellResult:
    corrected: str
    edits: list[dict[str, str]]

    @property
    def changed(self) -> bool:
        return bool(self.edits)


def _tokenize(text: str) -> list[str]:
    return re.findall(r"\w+|\W+", text)


def spell_correct(text: str, *, threshold: int = 88) -> SpellResult:
    edits: List[dict[str, str]] = []
    tokens = _tokenize(text)
    corrected_tokens: list[str] = []
    for token in tokens:
        if not token.isalpha() or len(token) < 4 or token.lower() in _VOCAB:
            corrected_tokens.append(token)
            continue
        match = process.extractOne(token.lower(), _VOCAB, scorer=fuzz.WRatio)
        if match and match[1] >= threshold and match[0] != token.lower():
            replacement = match[0]
            if token[0].isupper():
                replacement = replacement.capitalize()
            edits.append({"from": token, "to": replacement, "score": str(match[1])})
            corrected_tokens.append(replacement)
        else:
            corrected_tokens.append(token)
    return SpellResult(corrected="".join(corrected_tokens), edits=edits)
