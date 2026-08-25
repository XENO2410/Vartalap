"""Mock Status Retrieval tool (doc §4.3.B.1 + §4.3.B.2).

Emulates the two workflows in the doc:
    - API invocation via ESB (Unidesk, Kaleidoscope, PrimeCTL, ...)
    - Direct DB integration (Finacle, Tradax, TRRACS, GPS)
"""
from __future__ import annotations

import hashlib
import json
import random
from dataclasses import dataclass
from typing import Optional

from ..observability import EventEmitter
from ..schemas import ChatSource, MessageClass, MessageTag


_API_TOOLS = {
    "sr": ("Unidesk", "Service request status"),
    "ticket": ("Unidesk", "Ticket status"),
    "trade": ("Kaleidoscope", "Trade pendency"),
    "credit card": ("PrimeCTL", "Credit card application status"),
    "account opening": ("EdgeRewards", "Account opening state"),
    "eforms": ("SDL", "eForms submission state"),
}

_DB_TOOLS = {
    "balance": ("Finacle", "Account balance lookup"),
    "customer": ("Finacle", "Customer profile lookup"),
    "loan": ("Finacle", "Loan status lookup"),
    "trade": ("Tradax", "Trade booking record"),
    "recon": ("TRRACS", "Reconciliation state"),
    "position": ("GPS", "Position tracking"),
}


@dataclass
class StatusResult:
    answer: str
    sources: list[ChatSource]
    tool: str
    kind: str  # api | db


class StatusTool:
    """Deterministic mock that returns believable status payloads."""

    def run_api(self, *, query: str, emitter: EventEmitter) -> StatusResult:
        return self._run(query=query, emitter=emitter, kind="api")

    def run_db(self, *, query: str, emitter: EventEmitter) -> StatusResult:
        return self._run(query=query, emitter=emitter, kind="db")

    # ------------------------------------------------------------------
    def _run(self, *, query: str, emitter: EventEmitter, kind: str) -> StatusResult:
        table = _API_TOOLS if kind == "api" else _DB_TOOLS
        tool_key: Optional[str] = None
        for key in table:
            if key in query.lower():
                tool_key = key
                break

        chosen_tool, description = table.get(
            tool_key or next(iter(table)),
            (next(iter(table.values()))),
        )

        emitter.emit(
            MessageTag.KNOWLEDGE_BASE_REQUEST,
            content=query,
            msg_class=MessageClass.QUERY,
            apiname=f"vartalaap.status.{kind}",
            extra={
                "additionalinfotags": json.dumps({"kind": kind, "tool": chosen_tool}),
            },
        )

        payload = self._fake_payload(chosen_tool=chosen_tool, description=description, query=query)
        answer = self._render(payload, kind=kind)

        source = ChatSource(
            title=f"{chosen_tool} · {description}",
            type="API" if kind == "api" else "DB",
            relevancy="High",
            score=0.95,
            snippet=json.dumps(payload, indent=2),
            uri=f"internal://{chosen_tool.lower()}",
        )

        emitter.emit(
            MessageTag.KNOWLEDGE_BASE_RESPONSE_DOC,
            content=source.snippet,
            msg_class=MessageClass.SYSTEM,
            apiname=f"vartalaap.status.{kind}",
            extra={
                "azurekbresponsedocumentattributes": json.dumps(
                    {"tool": chosen_tool, "kind": kind, "payload": payload}
                ),
                "additionalinfosources": json.dumps(source.model_dump()),
            },
        )

        emitter.emit(
            MessageTag.KNOWLEDGE_BASE_RESPONSE,
            content=answer,
            msg_class=MessageClass.RESPONSE,
            apiname=f"vartalaap.status.{kind}",
            extra={"additionalinfoproducts": chosen_tool},
        )

        return StatusResult(answer=answer, sources=[source], tool=chosen_tool, kind=kind)

    # ------------------------------------------------------------------
    def _fake_payload(self, *, chosen_tool: str, description: str, query: str) -> dict:
        seed = int(hashlib.sha1(query.encode("utf-8")).hexdigest()[:8], 16)
        rng = random.Random(seed)
        statuses = ["OPEN", "IN_PROGRESS", "PENDING", "RESOLVED", "CLOSED"]
        return {
            "reference_id": f"{chosen_tool[:3].upper()}-{rng.randint(100000, 999999)}",
            "status": rng.choice(statuses),
            "last_updated": f"2026-08-{rng.randint(1, 25):02d}T{rng.randint(0, 23):02d}:{rng.randint(0,59):02d}:00Z",
            "owner_group": rng.choice(["CBO", "Ops", "IT Helpdesk", "HR"]),
            "description": description,
        }

    def _render(self, payload: dict, *, kind: str) -> str:
        return (
            f"Here is the {kind.upper()} status pulled from **{payload['description']}**:\n\n"
            f"- Reference: `{payload['reference_id']}`\n"
            f"- Status: **{payload['status']}**\n"
            f"- Owner group: {payload['owner_group']}\n"
            f"- Last updated: {payload['last_updated']}"
        )
