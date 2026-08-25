"""Local embeddings via sentence-transformers with a deterministic fallback.

OpenRouter proxies chat completions only, so we run embeddings locally (free,
CPU-friendly). If the model can't be loaded (e.g. offline first run), we drop
to a stable hash-based pseudo-embedding so the pipeline stays runnable.
"""
from __future__ import annotations

import hashlib
import threading
from typing import Iterable, List

import numpy as np

from ..config import get_settings


_LOCK = threading.Lock()
_MODEL = None
_DIM_FALLBACK = 384  # matches all-MiniLM-L6-v2 dimensionality


def _load_model():
    global _MODEL
    if _MODEL is not None:
        return _MODEL
    with _LOCK:
        if _MODEL is not None:
            return _MODEL
        settings = get_settings()
        try:
            from sentence_transformers import SentenceTransformer  # type: ignore

            _MODEL = SentenceTransformer(settings.embedding_model, device=settings.embedding_device)
        except Exception:  # noqa: BLE001
            _MODEL = _HashEmbedder(dim=_DIM_FALLBACK)
    return _MODEL


class _HashEmbedder:
    """Cheap deterministic embedder used when the model cannot be loaded."""

    def __init__(self, dim: int = _DIM_FALLBACK) -> None:
        self.dim = dim

    def encode(self, texts, **_: object) -> np.ndarray:  # noqa: D401
        if isinstance(texts, str):
            texts = [texts]
        vectors = np.zeros((len(texts), self.dim), dtype=np.float32)
        for i, text in enumerate(texts):
            digest = hashlib.sha256(text.lower().encode("utf-8")).digest()
            # Tile digest bytes across the vector to get a stable signal.
            raw = np.frombuffer(
                (digest * (self.dim // len(digest) + 1))[: self.dim], dtype=np.uint8
            ).astype(np.float32)
            vector = (raw - 127.5) / 127.5
            norm = np.linalg.norm(vector) or 1.0
            vectors[i] = vector / norm
        return vectors


class Embedder:
    """Adapter with a stable `.embed(list[str]) -> list[list[float]]` shape."""

    def __init__(self) -> None:
        self.model = _load_model()

    def embed(self, texts: Iterable[str]) -> List[List[float]]:
        vectors = self.model.encode(
            list(texts),
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        if hasattr(vectors, "tolist"):
            return vectors.tolist()
        return [list(v) for v in vectors]

    def embed_one(self, text: str) -> List[float]:
        return self.embed([text])[0]
