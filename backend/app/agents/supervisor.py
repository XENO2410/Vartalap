"""Supervisor Agent — orchestrates one chat turn end-to-end (doc §2 / §4 / §7)."""
from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from typing import Optional

from ..config import get_settings
from ..guardrails import check_answer, check_query
from ..llm import LLMClient
from ..observability import EventEmitter
from ..preprocessing import GlossaryExpander, Translator, spell_correct
from ..routing import Route, classify
from ..schemas import (
    ChatRequest,
    ChatResponse,
    ChatSource,
    MessageClass,
    MessageEnvelope,
    MessageTag,
    UseCase,
)
from ..tools import KnowledgeBaseTool, StatusTool, Text2SQLTool
from .reactive import ToolSelection, select_tool
from .reflexion import ReflexionReviewer, ReflexionVerdict


@dataclass
class TurnOutcome:
    answer: str
    sources: list[ChatSource]
    use_case: UseCase
    tool_used: str
    reflexion_iterations: int
    events: list[MessageEnvelope]


class Supervisor:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.llm = LLMClient()
        self.glossary = GlossaryExpander()
        self.translator = Translator(self.llm)
        self.kb_tool = KnowledgeBaseTool(llm=self.llm)
        self.status_tool = StatusTool()
        self.t2s_tool = Text2SQLTool(llm=self.llm)
        self.reflexion = ReflexionReviewer(self.llm)

    # ------------------------------------------------------------------
    def handle(self, request: ChatRequest) -> ChatResponse:
        session_id = request.session_id or f"sess_{uuid.uuid4().hex[:12]}"
        emitter = EventEmitter(session_id=session_id, user_id=request.user_id)

        emitter.emit(
            MessageTag.USER_QUERY,
            content=request.query,
            msg_class=MessageClass.QUERY,
            apiname="vartalaap.frontend",
            extra={
                "additionalinfouserquery": request.query,
                "additionalinfotags": json.dumps({"bubble": request.bubble}),
            },
        )

        # ------------------------- Preprocessing ------------------------
        lang = self.translator.to_english(request.query)
        emitter.emit(
            MessageTag.LLM_LANG_REQUEST,
            content=request.query,
            msg_class=MessageClass.QUERY,
            apiname="vartalaap.preprocess.translate",
            extra={"originallanguage": lang.original_language},
        )
        emitter.emit(
            MessageTag.LLM_LANG_RESPONSE,
            content=lang.translated_text,
            msg_class=MessageClass.RESPONSE,
            apiname="vartalaap.preprocess.translate",
            extra={
                "islanguagetranslation": "true" if lang.translation_needed else "false",
                "originallanguage": lang.original_language,
                "additionalinfotranslatedpromptanswer": lang.translated_text,
                "additionalinfotranslatedprompttokeninfo": lang.token_info_json,
                "additionalinfomodel": lang.model,
            },
        )

        working_query = lang.translated_text
        spell = spell_correct(working_query)
        working_query = spell.corrected

        expanded, glossary_hits = self.glossary.apply(working_query)
        working_query = expanded

        emitter.emit(
            MessageTag.LLM_REFINE_QUERY_RESPONSE,
            content=working_query,
            msg_class=MessageClass.SYSTEM,
            apiname="vartalaap.preprocess",
            extra={
                "processedquery": working_query,
                "isspellcorrection": "true" if spell.changed else "false",
                "additionalinfoqueryafterguardrailsspellcorrection": working_query,
                "additionalinfomlglossary": json.dumps(glossary_hits),
            },
        )

        # ------------------------- Input guardrails ---------------------
        emitter.emit(
            MessageTag.GUARDRAILS_QUERY_FILTER_REQUEST,
            content=working_query,
            msg_class=MessageClass.QUERY,
            apiname="vartalaap.guardrails.input",
        )
        query_verdict = check_query(working_query)
        emitter.emit(
            MessageTag.GUARDRAILS_QUERY_FILTER_RESPONSE,
            content=json.dumps(query_verdict.to_dict()),
            msg_class=MessageClass.RESPONSE,
            apiname="vartalaap.guardrails.input",
            extra={"additionalinfotags": json.dumps(query_verdict.to_dict())},
        )
        if not query_verdict.allowed:
            answer = (
                "I can't help with that request. Please rephrase your question or "
                "contact the appropriate helpdesk if you need further assistance."
            )
            return self._finalise(
                emitter=emitter,
                request=request,
                session_id=session_id,
                answer=answer,
                sources=[],
                use_case=UseCase.GUARDRAILED,
                tool_used="guardrails",
                reflexion_iterations=0,
            )

        # ------------------------- Routing ------------------------------
        decision = classify(working_query, bubble=request.bubble)
        selection: ToolSelection = select_tool(decision)

        emitter.emit(
            MessageTag.PROMPT_BUILDER_LANG_REQUEST,
            content=working_query,
            msg_class=MessageClass.SYSTEM,
            apiname="vartalaap.router",
            extra={
                "additionalinfotags": json.dumps(
                    {
                        "route": decision.route.value,
                        "hashtags": decision.hashtags,
                        "matched": decision.matched_keywords,
                        "bubble": decision.bubble,
                    }
                ),
                "additionalinfousecase": selection.use_case.value,
            },
        )
        emitter.emit(
            MessageTag.PROMPT_BUILDER_LANG_RESPONSE,
            content=selection.tool_name,
            msg_class=MessageClass.SYSTEM,
            apiname="vartalaap.router",
            extra={
                "additionalinfotags": json.dumps({"tool": selection.tool_name, "reason": selection.reason}),
                "additionalinfousecase": selection.use_case.value,
            },
        )

        # ------------------------- Tool + reflexion loop ---------------
        history = [t.model_dump() for t in request.history[-self.settings.history_turns * 2 :]]
        answer, sources, iterations = self._run_with_reflexion(
            selection=selection,
            refined_query=working_query,
            raw_query=request.query,
            bubble=request.bubble,
            history=history,
            emitter=emitter,
        )

        # ------------------------- Output guardrails -------------------
        answer_verdict = check_answer(answer)
        if answer_verdict.reasons:
            answer = answer_verdict.scrubbed_text
            emitter.emit(
                MessageTag.GUARDRAILS_QUERY_FILTER_RESPONSE,
                content=json.dumps(answer_verdict.to_dict()),
                msg_class=MessageClass.RESPONSE,
                apiname="vartalaap.guardrails.output",
                extra={"additionalinfotags": json.dumps(answer_verdict.to_dict())},
            )

        return self._finalise(
            emitter=emitter,
            request=request,
            session_id=session_id,
            answer=answer,
            sources=sources,
            use_case=selection.use_case,
            tool_used=selection.tool_name,
            reflexion_iterations=iterations,
        )

    # ------------------------------------------------------------------
    def _run_with_reflexion(
        self,
        *,
        selection: ToolSelection,
        refined_query: str,
        raw_query: str,
        bubble: Optional[str],
        history: list[dict[str, str]],
        emitter: EventEmitter,
    ) -> tuple[str, list[ChatSource], int]:
        iterations = 0
        current_query = refined_query
        answer = ""
        sources: list[ChatSource] = []

        max_iters = self.settings.reflexion_max_iterations if self.settings.reflexion_enabled else 1

        while iterations < max_iters:
            iterations += 1
            answer, sources = self._invoke_tool(
                selection=selection,
                refined_query=current_query,
                raw_query=raw_query,
                bubble=bubble,
                history=history,
                emitter=emitter,
            )
            if not self.settings.reflexion_enabled:
                break
            verdict: ReflexionVerdict = self.reflexion.review(
                question=refined_query,
                answer=answer,
                emitter=emitter,
                iteration=iterations,
            )
            if verdict.valid or verdict.score >= 0.75 or iterations >= max_iters:
                break
            current_query = verdict.refined_query or current_query

        return answer, sources, iterations

    def _invoke_tool(
        self,
        *,
        selection: ToolSelection,
        refined_query: str,
        raw_query: str,
        bubble: Optional[str],
        history: list[dict[str, str]],
        emitter: EventEmitter,
    ) -> tuple[str, list[ChatSource]]:
        if selection.tool_name == "kb":
            result = self.kb_tool.run(
                refined_query=refined_query,
                raw_query=raw_query,
                bubble=bubble,
                history=history,
                emitter=emitter,
            )
            return result.answer, result.sources
        if selection.tool_name == "status_api":
            result = self.status_tool.run_api(query=refined_query, emitter=emitter)
            return result.answer, result.sources
        if selection.tool_name == "status_db":
            result = self.status_tool.run_db(query=refined_query, emitter=emitter)
            return result.answer, result.sources
        if selection.tool_name == "text2sql":
            result = self.t2s_tool.run(query=refined_query, emitter=emitter)
            return result.answer, result.sources
        raise ValueError(f"Unknown tool: {selection.tool_name}")

    # ------------------------------------------------------------------
    def _finalise(
        self,
        *,
        emitter: EventEmitter,
        request: ChatRequest,
        session_id: str,
        answer: str,
        sources: list[ChatSource],
        use_case: UseCase,
        tool_used: str,
        reflexion_iterations: int,
    ) -> ChatResponse:
        suggestions = _make_suggestions(request.query, request.bubble)
        emitter.emit(
            MessageTag.CHAT_RESPONSE,
            content=answer,
            msg_class=MessageClass.RESPONSE,
            apiname="vartalaap.chat",
            extra={
                "additionalinfoproducts": tool_used,
                "additionalinfousecase": use_case.value,
                "additionalinfosources": json.dumps([s.model_dump() for s in sources]),
                "additionalinfotags": json.dumps(
                    {
                        "tool": tool_used,
                        "reflexion_iterations": reflexion_iterations,
                        "bubble": request.bubble,
                    }
                ),
            },
        )
        return ChatResponse(
            session_id=session_id,
            message_id=emitter.events[-1].identifiermessageid or "",
            answer=answer,
            sources=sources,
            suggestions=suggestions,
            use_case=use_case.value,
            tool_used=tool_used,
            reflexion_iterations=reflexion_iterations,
            events=emitter.snapshot(),
        )


# ----------------------------------------------------------------------
def _make_suggestions(query: str, bubble: Optional[str]) -> list[str]:
    base = query.strip().rstrip("?").strip() or "this topic"
    tags = f" ({bubble})" if bubble and bubble.lower() != "all" else ""
    return [
        f"Show related policies for {base}{tags}",
        f"What are the eligibility criteria for {base}?",
        f"Where can I download the form for {base}?",
    ]
