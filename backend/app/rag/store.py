"""Persistent local vector store.

Originally backed by ChromaDB. `chroma-hnswlib` needs MSVC on Windows to
build against Python 3.12 (no prebuilt wheels), which turns a demo install
into a build-tools hunt. Since our corpus is small (< 1k chunks) we don't
need HNSW — a numpy dot-product over normalised embeddings is instant.

On-disk layout (under `data/chroma/`):
    <collection>.jsonl  # one record per line: {id, text, metadata}
    <collection>.npy    # (N, D) float32 embeddings, row-aligned with jsonl
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, List, Optional

import numpy as np

from ..config import get_settings


@dataclass
class Chunk:
    id: str
    text: str
    metadata: dict[str, Any]
    embedding: Optional[List[float]] = None


def _matches(metadata: dict[str, Any], where: dict[str, Any]) -> bool:
    for key, value in where.items():
        if metadata.get(key) != value:
            return False
    return True


class VectorStore:
    """Numpy-backed persistent vector store."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self._root: Path = self.settings.chroma_abs_path
        self._root.mkdir(parents=True, exist_ok=True)
        self._records_path: Path = self._root / f"{self.settings.chroma_collection}.jsonl"
        self._embeds_path: Path = self._root / f"{self.settings.chroma_collection}.npy"
        self._records: list[dict[str, Any]] = []
        self._embeddings: Optional[np.ndarray] = None
        self._loaded = False

    # ------------------------------------------------------------------
    def _ensure(self) -> None:
        if self._loaded:
            return
        self._loaded = True
        if self._records_path.exists():
            with self._records_path.open(encoding="utf-8") as fh:
                self._records = [json.loads(line) for line in fh if line.strip()]
        if self._embeds_path.exists():
            self._embeddings = np.load(self._embeds_path).astype(np.float32, copy=False)
        if self._embeddings is not None and len(self._records) != len(self._embeddings):
            # Corrupt on-disk state — start clean rather than serve mismatched rows.
            self._records = []
            self._embeddings = None

    def _persist(self) -> None:
        with self._records_path.open("w", encoding="utf-8") as fh:
            for record in self._records:
                fh.write(json.dumps(record, ensure_ascii=False) + "\n")
        if self._embeddings is not None and len(self._embeddings) > 0:
            np.save(self._embeds_path, self._embeddings.astype(np.float32, copy=False))
        elif self._embeds_path.exists():
            self._embeds_path.unlink()

    # ------------------------------------------------------------------
    def reset(self) -> None:
        self._records = []
        self._embeddings = None
        self._loaded = True
        for path in (self._records_path, self._embeds_path):
            if path.exists():
                path.unlink()

    def count(self) -> int:
        self._ensure()
        return len(self._records)

    # ------------------------------------------------------------------
    def upsert(self, chunks: Iterable[Chunk]) -> int:
        self._ensure()
        batch = list(chunks)
        if not batch:
            return 0

        by_id: dict[str, int] = {r["id"]: i for i, r in enumerate(self._records)}
        records = list(self._records)
        vectors: list[list[float]] = (
            [row.tolist() for row in self._embeddings]
            if self._embeddings is not None and len(self._embeddings) > 0
            else []
        )

        for chunk in batch:
            if chunk.embedding is None:
                raise ValueError(f"Chunk {chunk.id} has no embedding")
            record = {"id": chunk.id, "text": chunk.text, "metadata": chunk.metadata}
            if chunk.id in by_id:
                idx = by_id[chunk.id]
                records[idx] = record
                vectors[idx] = list(chunk.embedding)
            else:
                by_id[chunk.id] = len(records)
                records.append(record)
                vectors.append(list(chunk.embedding))

        self._records = records
        self._embeddings = np.asarray(vectors, dtype=np.float32) if vectors else None
        self._persist()
        return len(batch)

    # ------------------------------------------------------------------
    def query(
        self,
        query_embedding: List[float],
        *,
        top_k: int,
        where: Optional[dict[str, Any]] = None,
    ) -> list[Chunk]:
        self._ensure()
        if not self._records or self._embeddings is None or len(self._embeddings) == 0:
            return []

        q = np.asarray(query_embedding, dtype=np.float32)
        norm = float(np.linalg.norm(q)) or 1.0
        q = q / norm

        # Embedder returns L2-normalised vectors, so dot product == cosine similarity.
        scores = self._embeddings @ q

        if where:
            mask = np.array(
                [_matches(record.get("metadata", {}), where) for record in self._records]
            )
            if not mask.any():
                return []
            scores = np.where(mask, scores, -np.inf)

        top_k = min(top_k, len(self._records))
        if top_k <= 0:
            return []
        order = np.argpartition(-scores, top_k - 1)[:top_k]
        order = order[np.argsort(-scores[order])]

        out: list[Chunk] = []
        for idx in order:
            score = float(scores[int(idx)])
            if not np.isfinite(score):
                continue
            record = self._records[int(idx)]
            metadata = dict(record.get("metadata", {}))
            metadata["_score"] = score
            out.append(Chunk(id=record["id"], text=record["text"], metadata=metadata))
        return out
