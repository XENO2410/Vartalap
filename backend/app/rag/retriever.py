"""Retrieval layer — mirrors doc §5.2 (top-50 candidates → top-5 rerank)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List, Optional

from ..config import get_settings
from .embedder import Embedder
from .reranker import Reranker
from .store import Chunk, VectorStore


@dataclass
class RetrievalResult:
    chunks: List[Chunk]
    faq_hit: Optional[Chunk]
    faq_confidence: float
    used_reranker: bool


class Retriever:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.store = VectorStore()
        self.embedder = Embedder()
        self.reranker = Reranker()

    # ------------------------------------------------------------------
    def retrieve(
        self,
        query: str,
        *,
        bubble: Optional[str] = None,
        top_k_candidates: Optional[int] = None,
        top_k_final: Optional[int] = None,
    ) -> RetrievalResult:
        top_candidates = top_k_candidates or self.settings.retriever_top_k_candidates
        top_final = top_k_final or self.settings.retriever_top_k_final

        embedding = self.embedder.embed_one(query)
        where = self._build_filter(bubble)

        candidates = self.store.query(embedding, top_k=top_candidates, where=where)
        # If a bubble filter returns nothing, fall back to unfiltered so the demo
        # never returns an empty result.
        if not candidates and where:
            candidates = self.store.query(embedding, top_k=top_candidates)

        reranked = self.reranker.rerank(query, candidates, top_k=top_final)

        faq_hit, faq_conf = self._best_faq(reranked)

        return RetrievalResult(
            chunks=reranked,
            faq_hit=faq_hit,
            faq_confidence=faq_conf,
            used_reranker=self.settings.reranker_enabled,
        )

    # ------------------------------------------------------------------
    def _build_filter(self, bubble: Optional[str]) -> Optional[dict[str, Any]]:
        if not bubble or bubble.lower() == "all":
            return None
        return {"domain": bubble.upper()}

    def _best_faq(self, chunks: List[Chunk]) -> tuple[Optional[Chunk], float]:
        best: Optional[Chunk] = None
        best_score = 0.0
        for chunk in chunks:
            if chunk.metadata.get("doc_type") != "FAQ":
                continue
            score = float(
                chunk.metadata.get("_rerank_score") or chunk.metadata.get("_score") or 0.0
            )
            if score > best_score:
                best_score = score
                best = chunk
        return best, best_score
