"""Optional cross-encoder reranker (mirrors doc §5.2)."""
from __future__ import annotations

import threading
from typing import List, Sequence

from ..config import get_settings
from .store import Chunk


_LOCK = threading.Lock()
_MODEL = None


def _load():
    global _MODEL
    if _MODEL is not None:
        return _MODEL
    with _LOCK:
        if _MODEL is not None:
            return _MODEL
        settings = get_settings()
        if not settings.reranker_enabled:
            _MODEL = _NoopReranker()
            return _MODEL
        try:
            from FlagEmbedding import FlagReranker  # type: ignore

            _MODEL = FlagReranker(settings.reranker_model, use_fp16=False)
        except Exception:  # noqa: BLE001
            _MODEL = _NoopReranker()
    return _MODEL


class _NoopReranker:
    def compute_score(self, pairs: Sequence[Sequence[str]], **_: object) -> list[float]:  # noqa: D401
        return [0.0 for _ in pairs]


class Reranker:
    def __init__(self) -> None:
        self.model = _load()

    def rerank(self, query: str, chunks: List[Chunk], *, top_k: int) -> List[Chunk]:
        if not chunks:
            return []
        if isinstance(self.model, _NoopReranker):
            # Fall back to embedding-cosine order.
            return sorted(chunks, key=lambda c: c.metadata.get("_score", 0.0), reverse=True)[:top_k]

        pairs = [[query, c.text] for c in chunks]
        scores = self.model.compute_score(pairs, normalize=True)
        if isinstance(scores, float):
            scores = [scores]
        for chunk, score in zip(chunks, scores):
            chunk.metadata["_rerank_score"] = float(score)
        return sorted(chunks, key=lambda c: c.metadata.get("_rerank_score", 0.0), reverse=True)[:top_k]
