"""Text2SQL tool (doc §4.3.B.3).

Uses a tiny in-memory SQLite DB with a couple of representative tables. The
LLM is asked to produce SQL against a documented schema; the SQL is executed
and the results are formatted for the user.
"""
from __future__ import annotations

import json
import re
import sqlite3
import threading
from dataclasses import dataclass
from typing import Optional

from ..config import get_settings
from ..llm import LLMClient, LLMResponse, token_info
from ..observability import EventEmitter
from ..schemas import ChatSource, MessageClass, MessageTag


_SCHEMA_DDL = """
CREATE TABLE customers (
    customer_id TEXT PRIMARY KEY,
    name TEXT,
    segment TEXT,           -- RETAIL | SME | CORPORATE
    branch TEXT,
    onboarded_on DATE
);

CREATE TABLE accounts (
    account_id TEXT PRIMARY KEY,
    customer_id TEXT REFERENCES customers(customer_id),
    product TEXT,           -- SAVINGS | CURRENT | LOAN | CREDIT_CARD
    balance REAL,
    opened_on DATE,
    status TEXT             -- ACTIVE | DORMANT | CLOSED
);

CREATE TABLE transactions (
    txn_id TEXT PRIMARY KEY,
    account_id TEXT REFERENCES accounts(account_id),
    txn_date DATE,
    amount REAL,
    channel TEXT,           -- ATM | UPI | NEFT | POS
    txn_type TEXT           -- CREDIT | DEBIT
);
"""

_SEED_ROWS = [
    ("customers", [
        ("C001", "Aarav Sharma", "RETAIL", "Mumbai-Fort", "2024-05-01"),
        ("C002", "Priya Iyer", "RETAIL", "Bangalore-MG", "2023-11-12"),
        ("C003", "Kunal Verma", "SME", "Delhi-CP", "2022-02-18"),
        ("C004", "Neha Kapoor", "CORPORATE", "Mumbai-BKC", "2021-07-30"),
        ("C005", "Rahul Menon", "RETAIL", "Kochi-MG", "2025-01-04"),
    ]),
    ("accounts", [
        ("A101", "C001", "SAVINGS", 154320.75, "2024-05-02", "ACTIVE"),
        ("A102", "C002", "SAVINGS", 87210.10, "2023-11-15", "ACTIVE"),
        ("A103", "C002", "CREDIT_CARD", -12450.00, "2024-03-20", "ACTIVE"),
        ("A104", "C003", "CURRENT", 9820500.00, "2022-02-25", "ACTIVE"),
        ("A105", "C003", "LOAN", -1500000.00, "2023-08-11", "ACTIVE"),
        ("A106", "C004", "CURRENT", 45230000.00, "2021-08-04", "ACTIVE"),
        ("A107", "C005", "SAVINGS", 2100.50, "2025-01-05", "DORMANT"),
    ]),
    ("transactions", [
        ("T0001", "A101", "2026-08-20", -1200.00, "UPI", "DEBIT"),
        ("T0002", "A101", "2026-08-22", 40000.00, "NEFT", "CREDIT"),
        ("T0003", "A102", "2026-08-19", -560.00, "POS", "DEBIT"),
        ("T0004", "A104", "2026-08-21", -250000.00, "NEFT", "DEBIT"),
        ("T0005", "A106", "2026-08-23", 1500000.00, "NEFT", "CREDIT"),
        ("T0006", "A103", "2026-08-24", -3450.00, "POS", "DEBIT"),
    ]),
]


_LOCK = threading.Lock()
_CONN: Optional[sqlite3.Connection] = None


def _get_conn() -> sqlite3.Connection:
    global _CONN
    if _CONN is not None:
        return _CONN
    with _LOCK:
        if _CONN is not None:
            return _CONN
        conn = sqlite3.connect(":memory:", check_same_thread=False)
        conn.executescript(_SCHEMA_DDL)
        for table, rows in _SEED_ROWS:
            placeholders = ",".join(["?"] * len(rows[0]))
            conn.executemany(f"INSERT INTO {table} VALUES ({placeholders})", rows)
        conn.commit()
        _CONN = conn
    return _CONN


_T2SQL_SYSTEM = (
    "You translate the user question into a single SQLite SELECT query against the "
    "schema below. Return ONLY the SQL statement, no explanation, no code fences. "
    "Never write DDL / DML that mutates data. Prefer explicit JOIN ... ON.\n\n"
    f"SCHEMA:\n{_SCHEMA_DDL}"
)


_SELECT_ONLY_RE = re.compile(r"^\s*select\b", re.IGNORECASE)
_FORBIDDEN_RE = re.compile(r"\b(insert|update|delete|drop|alter|create|attach)\b", re.IGNORECASE)


@dataclass
class T2SQLResult:
    answer: str
    sources: list[ChatSource]
    sql: str
    rows: list[dict]
    model: str
    token_info_json: str


class Text2SQLTool:
    def __init__(self, llm: Optional[LLMClient] = None) -> None:
        self.llm = llm or LLMClient()
        self.settings = get_settings()

    def run(self, *, query: str, emitter: EventEmitter) -> T2SQLResult:
        emitter.emit(
            MessageTag.KNOWLEDGE_BASE_REQUEST,
            content=query,
            msg_class=MessageClass.QUERY,
            apiname="vartalaap.text2sql",
            extra={"additionalinfotags": json.dumps({"tool": "text2sql"})},
        )

        emitter.emit(
            MessageTag.LLM_QA_REQUEST,
            content=query,
            msg_class=MessageClass.QUERY,
            apiname="vartalaap.text2sql.llm",
            extra={"additionalinfomodel": self.settings.llm_model},
        )
        resp: LLMResponse = self.llm.chat(
            system=_T2SQL_SYSTEM,
            user=query,
            temperature=0.0,
            max_tokens=300,
        )
        emitter.emit(
            MessageTag.LLM_QA_RESPONSE,
            content=resp.content,
            msg_class=MessageClass.RESPONSE,
            apiname="vartalaap.text2sql.llm",
            extra={
                "additionalinfomodel": resp.model,
                "additionalinfotokeninfo": token_info(resp),
            },
        )

        sql = _clean_sql(resp.content)

        rows: list[dict] = []
        error: Optional[str] = None
        if not sql or not _SELECT_ONLY_RE.match(sql) or _FORBIDDEN_RE.search(sql):
            error = "Generated SQL was blocked by guardrails or is not a SELECT."
        else:
            try:
                cur = _get_conn().execute(sql)
                cols = [d[0] for d in cur.description or []]
                rows = [dict(zip(cols, row)) for row in cur.fetchall()]
            except Exception as exc:  # noqa: BLE001
                error = f"SQL execution error: {exc}"

        formatted = _format_rows(rows) if not error else error
        answer = f"Ran the following SQL:\n\n```sql\n{sql}\n```\n\n{formatted}"

        source = ChatSource(
            title="Text-to-SQL result",
            type="DB",
            relevancy="High" if not error else "Low",
            score=0.9 if not error else 0.1,
            snippet=json.dumps({"sql": sql, "rows": rows[:5], "error": error}, indent=2),
            uri="sqlite://memory/vartalaap",
        )

        emitter.emit(
            MessageTag.KNOWLEDGE_BASE_RESPONSE,
            content=answer,
            msg_class=MessageClass.RESPONSE,
            apiname="vartalaap.text2sql",
            extra={
                "additionalinfotext2sqlquery": query,
                "additionalinfosqlquery": sql,
                "additionalinfoformattedsqlquery": formatted,
                "additionalinfoproducts": "text2sql",
            },
        )

        return T2SQLResult(
            answer=answer,
            sources=[source],
            sql=sql,
            rows=rows,
            model=resp.model,
            token_info_json=token_info(resp),
        )


def _clean_sql(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(?:sql)?", "", text, flags=re.IGNORECASE).strip()
    text = re.sub(r"```$", "", text).strip()
    text = text.rstrip(";").strip()
    return text


def _format_rows(rows: list[dict]) -> str:
    if not rows:
        return "_No rows returned._"
    headers = list(rows[0].keys())
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows[:20]:
        lines.append("| " + " | ".join(str(row.get(h, "")) for h in headers) + " |")
    if len(rows) > 20:
        lines.append(f"_...{len(rows) - 20} more rows_")
    return "\n".join(lines)
