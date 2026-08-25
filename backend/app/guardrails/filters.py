"""Rule-based guardrails.

Runs on both the incoming query and the outgoing answer (matches doc §4.3.A
and §6.3).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List


_BLOCKED_PATTERNS = [
    (re.compile(r"\b(hack|exploit|bypass)\b.*\b(system|security|auth)\b", re.I),
     "Attempted security-bypass request"),
    (re.compile(r"\b(delete|drop|truncate)\s+(all|table|database)\b", re.I),
     "Destructive DB operation request"),
    (re.compile(r"\b(ssn|social security|aadhaar|aadhar|pan card)\s+of\b", re.I),
     "Sensitive personal identifier disclosure request"),
]

# Very light PII pattern for answer scrubbing.
_PII_REDACTORS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b"), "[REDACTED_CARD]"),
    (re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b"), "[REDACTED_PAN]"),
    (re.compile(r"\b\d{12}\b"), "[REDACTED_AADHAAR]"),
]


@dataclass
class GuardrailVerdict:
    allowed: bool
    reasons: List[str] = field(default_factory=list)
    scrubbed_text: str = ""

    def to_dict(self) -> dict[str, str | list[str]]:
        return {
            "allowed": "true" if self.allowed else "false",
            "reasons": self.reasons,
            "scrubbed_text": self.scrubbed_text,
        }


def check_query(text: str) -> GuardrailVerdict:
    reasons: list[str] = []
    for pattern, reason in _BLOCKED_PATTERNS:
        if pattern.search(text):
            reasons.append(reason)
    return GuardrailVerdict(allowed=not reasons, reasons=reasons, scrubbed_text=text)


def check_answer(text: str) -> GuardrailVerdict:
    scrubbed = text
    reasons: list[str] = []
    for pattern, replacement in _PII_REDACTORS:
        if pattern.search(scrubbed):
            reasons.append(f"Redacted PII: {replacement}")
            scrubbed = pattern.sub(replacement, scrubbed)
    return GuardrailVerdict(allowed=True, reasons=reasons, scrubbed_text=scrubbed)
