"""Message schema mirroring the ADI architecture doc §3 / §12.

Every field from the schema table is present as a nullable string so that the
observability sink can persist rows exactly as the doc specifies, and later be
consumed by MLflow / Kytee without any transformation.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Enums / constants (doc §4, §12)
# ---------------------------------------------------------------------------
class MessageTag(str, Enum):
    USER_QUERY = "USER_QUERY"
    LLM_LANG_REQUEST = "LLM_LANG_REQUEST"
    LLM_LANG_RESPONSE = "LLM_LANG_RESPONSE"
    GUARDRAILS_QUERY_FILTER_REQUEST = "GUARDRAILS_QUERY_FILTER_REQUEST"
    GUARDRAILS_QUERY_FILTER_RESPONSE = "GUARDRAILS_QUERY_FILTER_RESPONSE"
    LLM_REFINE_QUERY_RESPONSE = "LLM_REFINE_QUERY_RESPONSE"
    PROMPT_BUILDER_REFINE_QUERY_RESPONSE = "PROMPT_BUILDER_REFINE_QUERY_RESPONSE"
    PROMPT_BUILDER_LANG_REQUEST = "PROMPT_BUILDER_LANG_REQUEST"
    PROMPT_BUILDER_LANG_RESPONSE = "PROMPT_BUILDER_LANG_RESPONSE"
    LLM_QA_REQUEST = "LLM_QA_REQUEST"
    LLM_QA_RESPONSE = "LLM_QA_RESPONSE"
    PROMPT_BUILDER_QA_RESPONSE = "PROMPT_BUILDER_QA_RESPONSE"
    KNOWLEDGE_BASE_REQUEST = "KNOWLEDGE_BASE_REQUEST"
    KNOWLEDGE_BASE_RESPONSE = "KNOWLEDGE_BASE_RESPONSE"
    KNOWLEDGE_BASE_RESPONSE_DOC = "KNOWLEDGE_BASE_RESPONSE_DOC"
    CHAT_RESPONSE = "CHAT_RESPONSE"


class MessageClass(str, Enum):
    QUERY = "query"
    RESPONSE = "response"
    SYSTEM = "system"


class UseCase(str, Enum):
    RAG = "generic_rag"
    STATUS_API = "status_api"
    STATUS_DB = "status_db"
    TEXT2SQL = "text2sql"
    GUARDRAILED = "guardrailed"
    OUT_OF_SCOPE = "out_of_scope"


# ---------------------------------------------------------------------------
# Envelope — one row per emitted stage (matches schema table in the doc)
# ---------------------------------------------------------------------------
def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _today_partition() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


class MessageEnvelope(BaseModel):
    """One observability event = one row in the schema table."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    # Identity ----------------------------------------------------------------
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    identifiermessageid: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    identifiersessionid: Optional[str] = None
    identifieruserid: Optional[str] = None
    createddate: str = Field(default_factory=_now_iso)
    dt: str = Field(default_factory=_today_partition)  # daily partition

    # Message tag / class / type ---------------------------------------------
    # `class` is a python keyword → use alias
    class_: Optional[str] = Field(default=None, alias="class")
    messagetype: Optional[str] = None  # value of MessageTag
    apiname: Optional[str] = None

    # Content -----------------------------------------------------------------
    content: Optional[str] = None
    msgcontent: Optional[str] = None
    msgcommand: Optional[str] = None
    processedquery: Optional[str] = None

    # User query / preprocessing ---------------------------------------------
    additionalinfouserquery: Optional[str] = None
    originallanguage: Optional[str] = None
    islanguagetranslation: Optional[str] = None
    isspellcorrection: Optional[str] = None
    additionalinfoqueryafterguardrailsspellcorrection: Optional[str] = None
    additionalinfomlglossary: Optional[str] = None  # renamed in doc as glossary

    # Model + prompts ---------------------------------------------------------
    additionalinfomodel: Optional[str] = None
    additionalinfoprompttuserprompt: Optional[str] = None
    additionalinfotranslatedpromptclass: Optional[str] = None
    additionalinfotranslatedpromptanswer: Optional[str] = None
    additionalinfotranslatedprompttokeninfo: Optional[str] = None
    additionalinfotokeninfo: Optional[str] = None

    # Tool routing / tags / use case -----------------------------------------
    additionalinfotags: Optional[str] = None
    additionalinfoproducts: Optional[str] = None
    additionalinfosubproducts: Optional[str] = None
    additionalinfousecase: Optional[str] = None

    # KB + sources ------------------------------------------------------------
    additionalinfosources: Optional[str] = None
    azurekbresponsedocumentattributes: Optional[str] = None

    # DB / Text2SQL -----------------------------------------------------------
    additionalinfotext2sqlquery: Optional[str] = None
    additionalinfoformattedsqlquery: Optional[str] = None
    additionalinfosqlquery: Optional[str] = None

    # History -----------------------------------------------------------------
    historyrelevancyscore: Optional[str] = None


# ---------------------------------------------------------------------------
# Public chat contract (frontend <-> backend)
# ---------------------------------------------------------------------------
class ChatSource(BaseModel):
    title: str
    type: str  # PDF | DB | FAQ | MD | API
    relevancy: str  # High | Medium | Low
    score: float = 0.0
    snippet: Optional[str] = None
    uri: Optional[str] = None


class ChatTurn(BaseModel):
    role: str  # user | assistant
    content: str


class ChatRequest(BaseModel):
    query: str
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    bubble: Optional[str] = None  # e.g. "HR", "Status", "All"
    history: list[ChatTurn] = Field(default_factory=list)


class ChatResponse(BaseModel):
    session_id: str
    message_id: str
    answer: str
    sources: list[ChatSource] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)
    use_case: str
    tool_used: str
    reflexion_iterations: int = 0
    events: list[MessageEnvelope] = Field(default_factory=list)
