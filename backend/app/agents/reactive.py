"""Reactive AI Agent — selects the right tool given the routing decision."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from ..routing import Route, RoutingDecision
from ..schemas import UseCase


@dataclass
class ToolSelection:
    tool_name: str        # kb | status_api | status_db | text2sql
    use_case: UseCase
    reason: str


def select_tool(decision: RoutingDecision) -> ToolSelection:
    if decision.route is Route.STATUS_API:
        return ToolSelection(
            tool_name="status_api",
            use_case=UseCase.STATUS_API,
            reason=decision.reason,
        )
    if decision.route is Route.STATUS_DB:
        return ToolSelection(
            tool_name="status_db",
            use_case=UseCase.STATUS_DB,
            reason=decision.reason,
        )
    if decision.route is Route.TEXT2SQL:
        return ToolSelection(
            tool_name="text2sql",
            use_case=UseCase.TEXT2SQL,
            reason=decision.reason,
        )
    return ToolSelection(
        tool_name="kb",
        use_case=UseCase.RAG,
        reason=decision.reason,
    )
