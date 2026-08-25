"""Knowledge Base tool — RAG over FAQs + documents (doc §4.3.A + §5)."""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import List, Optional

from ..config import get_settings
from ..llm import LLMClient, LLMResponse, token_info
from ..observability import EventEmitter
from ..rag import Chunk, Retriever
from ..schemas import ChatSource, MessageClass, MessageTag


_QA_SYSTEM = (
    "You are वार्तालाप (Vartalaap), an internal banking assistant. "
    "Answer using ONLY the provided context. If the context is insufficient, "
    "say you don't have enough information and suggest the user contact the "
    "relevant helpdesk. Cite sources inline as [S1], [S2] where S1 is the "
    "first source, etc. Keep answers concise, factual, and in the user's "
    "language when appropriate."
)


def _relevancy_bucket(score: float, high: float, medium: float) -> str:
    if score >= high:
        return "High"
    if score >= medium:
        return "Medium"
    return "Low"


def _chunk_to_source(chunk: Chunk, rank: int, high: float, medium: float) -> ChatSource:
    meta = chunk.metadata or {}
    score = float(meta.get("_rerank_score") or meta.get("_score") or 0.0)
    return ChatSource(
        title=str(meta.get("title") or meta.get("source_id") or f"Source {rank}"),
        type=str(meta.get("doc_type") or "DOC"),
        relevancy=_relevancy_bucket(score, high, medium),
        score=round(score, 4),
        snippet=chunk.text[:280],
        uri=str(meta.get("source_path") or ""),
    )


@dataclass
class KBResult:
    answer: str
    sources: List[ChatSource]
    faq_direct: bool
    model: str
    token_info_json: str


class KnowledgeBaseTool:
    def __init__(self, *, llm: Optional[LLMClient] = None) -> None:
        self.settings = get_settings()
        self.retriever = Retriever()
        self.llm = llm or LLMClient()

    # ------------------------------------------------------------------
    def run(
        self,
        *,
        refined_query: str,
        raw_query: str,
        bubble: Optional[str],
        history: list[dict[str, str]],
        emitter: EventEmitter,
    ) -> KBResult:
        emitter.emit(
            MessageTag.KNOWLEDGE_BASE_REQUEST,
            content=refined_query,
            msg_class=MessageClass.QUERY,
            apiname="vartalaap.kb",
            extra={
                "additionalinfouserquery": raw_query,
                "additionalinfotags": json.dumps({"bubble": bubble}),
            },
        )

        result = self.retriever.retrieve(refined_query, bubble=bubble)

        sources = [
            _chunk_to_source(c, i + 1, self.settings.faq_high_confidence, self.settings.faq_medium_confidence)
            for i, c in enumerate(result.chunks)
        ]

        # Per-doc envelopes for downstream analysis
        for i, chunk in enumerate(result.chunks):
            emitter.emit(
                MessageTag.KNOWLEDGE_BASE_RESPONSE_DOC,
                content=chunk.text[:400],
                msg_class=MessageClass.SYSTEM,
                apiname="vartalaap.kb",
                extra={
                    "azurekbresponsedocumentattributes": json.dumps(
                        {
                            "rank": i + 1,
                            "id": chunk.id,
                            "title": chunk.metadata.get("title"),
                            "doc_type": chunk.metadata.get("doc_type"),
                            "domain": chunk.metadata.get("domain"),
                            "score": chunk.metadata.get("_score"),
                            "rerank_score": chunk.metadata.get("_rerank_score"),
                        }
                    ),
                    "additionalinfosources": json.dumps(sources[i].model_dump()),
                },
            )

        # FAQ-first policy (doc §5.3)
        if (
            result.faq_hit is not None
            and result.faq_confidence >= self.settings.faq_high_confidence
        ):
            answer = str(result.faq_hit.metadata.get("answer") or result.faq_hit.text)
            emitter.emit(
                MessageTag.KNOWLEDGE_BASE_RESPONSE,
                content=answer,
                msg_class=MessageClass.RESPONSE,
                apiname="vartalaap.kb",
                extra={
                    "additionalinfoproducts": str(result.faq_hit.metadata.get("product") or ""),
                    "additionalinfosubproducts": str(result.faq_hit.metadata.get("role") or ""),
                    "additionalinfotags": json.dumps({"faq_confidence": result.faq_confidence}),
                },
            )
            return KBResult(
                answer=answer,
                sources=sources,
                faq_direct=True,
                model="faq-direct",
                token_info_json=json.dumps({"prompt_tokens": 0, "completion_tokens": 0}),
            )

        # LLM synthesis with retrieved context (doc §6.1)
        context_block, sources_used = self._build_context(result.chunks)
        history_block = self._history_block(history)

        prompt_builder_output = self._compose_prompt(
            refined_query=refined_query,
            context_block=context_block,
            history_block=history_block,
        )
        emitter.emit(
            MessageTag.PROMPT_BUILDER_QA_RESPONSE,
            content=prompt_builder_output,
            msg_class=MessageClass.SYSTEM,
            apiname="vartalaap.kb",
            extra={
                "additionalinfoprompttuserprompt": prompt_builder_output,
                "additionalinfomodel": self.settings.llm_model,
            },
        )

        emitter.emit(
            MessageTag.LLM_QA_REQUEST,
            content=prompt_builder_output,
            msg_class=MessageClass.QUERY,
            apiname="vartalaap.llm",
            extra={"additionalinfomodel": self.settings.llm_model},
        )
        resp: LLMResponse = self.llm.chat(system=_QA_SYSTEM, user=prompt_builder_output)
        emitter.emit(
            MessageTag.LLM_QA_RESPONSE,
            content=resp.content,
            msg_class=MessageClass.RESPONSE,
            apiname="vartalaap.llm",
            extra={
                "additionalinfomodel": resp.model,
                "additionalinfotokeninfo": token_info(resp),
            },
        )

        emitter.emit(
            MessageTag.KNOWLEDGE_BASE_RESPONSE,
            content=resp.content,
            msg_class=MessageClass.RESPONSE,
            apiname="vartalaap.kb",
            extra={
                "additionalinfoproducts": ",".join(sources_used),
                "additionalinfotags": json.dumps(
                    {"faq_confidence": result.faq_confidence, "reranker": result.used_reranker}
                ),
            },
        )

        return KBResult(
            answer=resp.content,
            sources=sources,
            faq_direct=False,
            model=resp.model,
            token_info_json=token_info(resp),
        )

    # ------------------------------------------------------------------
    def _build_context(self, chunks: List[Chunk]) -> tuple[str, list[str]]:
        lines: list[str] = []
        titles: list[str] = []
        for i, chunk in enumerate(chunks):
            title = chunk.metadata.get("title") or chunk.metadata.get("source_id") or f"Source {i+1}"
            titles.append(str(title))
            lines.append(f"[S{i+1}] {title}\n{chunk.text.strip()}")
        return "\n\n".join(lines), titles

    def _history_block(self, history: list[dict[str, str]]) -> str:
        if not history:
            return ""
        recent = history[-self.settings.history_turns * 2 :]
        turns = [f"{turn['role'].upper()}: {turn['content']}" for turn in recent]
        return "\n".join(turns)

    def _compose_prompt(self, *, refined_query: str, context_block: str, history_block: str) -> str:
        parts = [
            "USER QUESTION:",
            refined_query,
            "",
            "RETRIEVED CONTEXT (cite as [S1], [S2], ...):",
            context_block or "(no context retrieved)",
        ]
        if history_block:
            parts.extend(["", "RECENT CHAT HISTORY:", history_block])
        parts.append("")
        parts.append("Compose the final answer now.")
        return "\n".join(parts)
