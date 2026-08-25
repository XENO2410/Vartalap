"""Query routing (doc §4).

Handles both explicit bubble/hashtag routing and free-text intent detection.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class Route(str, Enum):
    RAG = "rag"
    STATUS_API = "status_api"
    STATUS_DB = "status_db"
    TEXT2SQL = "text2sql"


@dataclass
class RoutingDecision:
    route: Route
    reason: str
    hashtags: list[str]
    bubble: Optional[str]
    matched_keywords: list[str]


# Keyword tables — cheap, deterministic router that stands in for the
# intent-based classifier described in the doc.
_STATUS_API_KEYWORDS = {
    "sr", "service request", "ticket", "status", "opening status",
    "trade pendency", "credit card status", "unidesk", "kaleidoscope",
    "eforms", "sdl",
}
_STATUS_DB_KEYWORDS = {
    "balance", "account balance", "customer info", "work step", "workstep",
    "loan status", "transaction status", "finacle", "tradax", "trracs",
    "gps",
}
_TEXT2SQL_KEYWORDS = {
    "how many", "count of", "sum of", "average", "list all", "show me all",
    "top 10", "top ten", "trend", "distribution",
}

_HASHTAG_RE = re.compile(r"#([a-zA-Z0-9_]+)")


def _match_any(text: str, vocabulary: set[str]) -> list[str]:
    lowered = text.lower()
    return sorted({kw for kw in vocabulary if kw in lowered})


def classify(query: str, *, bubble: Optional[str] = None) -> RoutingDecision:
    hashtags = [h.lower() for h in _HASHTAG_RE.findall(query)]

    if "status" in hashtags or (bubble and bubble.lower() == "status"):
        status_api_hits = _match_any(query, _STATUS_API_KEYWORDS)
        status_db_hits = _match_any(query, _STATUS_DB_KEYWORDS)
        if status_db_hits and not status_api_hits:
            return RoutingDecision(
                route=Route.STATUS_DB,
                reason="Status bubble + DB keywords",
                hashtags=hashtags,
                bubble=bubble,
                matched_keywords=status_db_hits,
            )
        return RoutingDecision(
            route=Route.STATUS_API,
            reason="Status bubble / #status hashtag",
            hashtags=hashtags,
            bubble=bubble,
            matched_keywords=status_api_hits or ["#status"],
        )

    text2sql_hits = _match_any(query, _TEXT2SQL_KEYWORDS)
    if text2sql_hits and any(k in query.lower() for k in ("account", "loan", "customer", "transaction")):
        return RoutingDecision(
            route=Route.TEXT2SQL,
            reason="Aggregate / analytical intent over bank data",
            hashtags=hashtags,
            bubble=bubble,
            matched_keywords=text2sql_hits,
        )

    return RoutingDecision(
        route=Route.RAG,
        reason="Default: generic knowledge base RAG",
        hashtags=hashtags,
        bubble=bubble,
        matched_keywords=[],
    )
