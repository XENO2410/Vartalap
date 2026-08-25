"""Domain glossary — matches doc §4.3.A.1 (glossary applied during refinement)."""
from __future__ import annotations

import re
from typing import Dict, List, Tuple


# Bank / product / process abbreviations used across the ADI corpus.
_GLOSSARY: Dict[str, str] = {
    "kyc": "Know Your Customer",
    "aml": "Anti Money Laundering",
    "cif": "Customer Information File",
    "sr": "Service Request",
    "cr": "Change Request",
    "cbo": "Central Back Office",
    "cbs": "Core Banking System",
    "hr": "Human Resources",
    "faq": "Frequently Asked Question",
    "esb": "Enterprise Service Bus",
    "trrs": "TRRACS trade recon system",
    "gps": "General Purpose System",
    "aha": "AHA product suite",
    "cres": "Corporate Real Estate Services",
    "bi": "Business Intelligence",
    "ops": "Operations",
    "sdl": "Service Delivery Layer",
    "adi": "Axis Deep Intelligence assistant",
    "vartalaap": "Vartalaap conversational assistant",
}


class GlossaryExpander:
    """Expands known abbreviations found in the user query."""

    def __init__(self, extras: Dict[str, str] | None = None) -> None:
        table = dict(_GLOSSARY)
        if extras:
            table.update({k.lower(): v for k, v in extras.items()})
        self._table = table
        pattern = r"\b(" + "|".join(re.escape(k) for k in sorted(table, key=len, reverse=True)) + r")\b"
        self._pattern = re.compile(pattern, re.IGNORECASE)

    def apply(self, text: str) -> Tuple[str, List[Dict[str, str]]]:
        applied: List[Dict[str, str]] = []

        def _replace(match: re.Match[str]) -> str:
            key = match.group(0).lower()
            expansion = self._table.get(key)
            if not expansion:
                return match.group(0)
            applied.append({"term": key, "expansion": expansion})
            return f"{match.group(0)} ({expansion})"

        expanded = self._pattern.sub(_replace, text)
        return expanded, applied
