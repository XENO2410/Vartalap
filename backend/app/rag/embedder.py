"""Embedding backends.

Runtime pipeline is deliberately lightweight so the backend fits Render
Free (512 MB RAM):

    1. If `HF_INFERENCE_TOKEN` is set, call the Hugging Face Inference API
       for the one query embedding per chat turn (free tier ~1000 req/day).
    2. Otherwise, if `sentence-transformers` happens to be installed
       (dev machines, `docker compose up` locally), use it — same quality
       as before.
    3. Last resort: a deterministic hash embedder so the pipeline still
       runs. Retrieval quality drops, but the demo doesn't 500.

Chunk embeddings for the bundled KB are pre-computed at commit time and
shipped under `data/chroma/<collection>.npy`, so nothing embeds documents
at runtime by default — only the user's query hits the API.
"""
from __future__ import annotations

import hashlib
import sys
import threading
from typing import Iterable, List

import numpy as np

from ..config import get_settings


_LOCK = threading.Lock()
_MODEL = None
_DIM = 384  # all-MiniLM-L6-v2


# ---------------------------------------------------------------------------
class _HashEmbedder:
    """Deterministic pseudo-embedder used when no real backend is reachable."""

    def __init__(self, dim: int = _DIM) -> None:
        self.dim = dim

    def encode(self, texts, **_: object) -> np.ndarray:  # noqa: D401
        if isinstance(texts, str):
            texts = [texts]
        vectors = np.zeros((len(texts), self.dim), dtype=np.float32)
        for i, text in enumerate(texts):
            digest = hashlib.sha256(text.lower().encode("utf-8")).digest()
            raw = np.frombuffer(
                (digest * (self.dim // len(digest) + 1))[: self.dim], dtype=np.uint8
            ).astype(np.float32)
            v = (raw - 127.5) / 127.5
            norm = np.linalg.norm(v) or 1.0
            vectors[i] = v / norm
        return vectors


# ---------------------------------------------------------------------------
class _HFInferenceEmbedder:
    """Hugging Face Inference API (free tier) — 1 outbound call per query."""

    def __init__(self, *, token: str, model: str) -> None:
        import httpx

        self._httpx = httpx
        self._model = model
        self._url = (
            f"https://api-inference.huggingface.co/pipeline/feature-extraction/{model}"
        )
        self._headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        }
        self._client = httpx.Client(timeout=30.0)
        self.dim = _DIM

    def encode(self, texts, **_: object) -> np.ndarray:  # noqa: D401
        if isinstance(texts, str):
            texts = [texts]
        # HF Inference expects a "wait_for_model" hint on cold starts.
        payload = {
            "inputs": list(texts),
            "options": {"wait_for_model": True, "use_cache": True},
        }
        resp = self._client.post(self._url, headers=self._headers, json=payload)
        resp.raise_for_status()
        arr = np.asarray(resp.json(), dtype=np.float32)
        if arr.ndim == 3:
            # Some pipelines return (batch, seq_len, dim) → mean-pool.
            arr = arr.mean(axis=1)
        if arr.ndim == 1:
            arr = arr.reshape(1, -1)
        norms = np.linalg.norm(arr, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        return arr / norms


# ---------------------------------------------------------------------------
class _SentenceTransformerEmbedder:
    """Local torch-based embedder — only used when `sentence-transformers`
    is installed (not in the shipped requirements)."""

    def __init__(self, *, model_name: str, device: str = "cpu") -> None:
        from sentence_transformers import SentenceTransformer  # type: ignore

        self._model = SentenceTransformer(model_name, device=device)
        self.dim = _DIM

    def encode(self, texts, **_: object) -> np.ndarray:  # noqa: D401
        if isinstance(texts, str):
            texts = [texts]
        return self._model.encode(
            list(texts),
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )


# ---------------------------------------------------------------------------
def _load_model():
    global _MODEL
    if _MODEL is not None:
        return _MODEL
    with _LOCK:
        if _MODEL is not None:
            return _MODEL
        settings = get_settings()
        backend = (settings.embedding_backend or "auto").lower()
        # Try HF Inference API first (production / hosted path).
        if backend in ("auto", "hf_api") and settings.hf_inference_token:
            try:
                model = _HFInferenceEmbedder(
                    token=settings.hf_inference_token,
                    model=settings.embedding_model,
                )
                _ = model.encode("warmup")
                _MODEL = model
                return _MODEL
            except Exception as exc:  # noqa: BLE001
                sys.stderr.write(f"[embedder] HF Inference API failed: {exc!r}\n")
        # Local torch path (dev machines, optional install).
        if backend in ("auto", "sentence_transformers"):
            try:
                _MODEL = _SentenceTransformerEmbedder(
                    model_name=settings.embedding_model,
                    device=settings.embedding_device,
                )
                return _MODEL
            except Exception:  # noqa: BLE001
                pass
        # Last resort.
        sys.stderr.write(
            "[embedder] Falling back to hash pseudo-embeddings (retrieval quality reduced)\n"
        )
        _MODEL = _HashEmbedder()
        return _MODEL


class Embedder:
    """Adapter with a stable `.embed(list[str]) -> list[list[float]]` shape."""

    def __init__(self) -> None:
        self.model = _load_model()

    def embed(self, texts: Iterable[str]) -> List[List[float]]:
        vectors = self.model.encode(list(texts))
        if hasattr(vectors, "tolist"):
            return vectors.tolist()
        return [list(v) for v in vectors]

    def embed_one(self, text: str) -> List[float]:
        return self.embed([text])[0]
