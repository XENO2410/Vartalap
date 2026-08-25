"""Chunking + ingestion pipeline.

Sources supported (matches doc §5.1):
    - PDF files      (via `pypdf`)
    - Plain text     (`.txt` / `.md`)
    - CSV FAQ store  (question,answer,domain,role,product,freshness)

Everything ends up in the same Chroma collection with common metadata.
"""
from __future__ import annotations

import csv
import re
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator, List

from .embedder import Embedder
from .store import Chunk, VectorStore


CHUNK_TARGET_TOKENS = 1000  # doc §5.1 "~1000 tokens with overlap"
CHUNK_OVERLAP_TOKENS = 150


def _approx_token_count(text: str) -> int:
    # Rough: 4 characters ≈ 1 token, used only for chunk sizing.
    return max(1, len(text) // 4)


def _chunk_text(text: str, *, target_tokens: int, overlap_tokens: int) -> List[str]:
    text = re.sub(r"\r\n?", "\n", text).strip()
    if not text:
        return []
    # Split by paragraphs first, then greedily pack.
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks: List[str] = []
    current: list[str] = []
    current_tokens = 0
    for para in paragraphs:
        para_tokens = _approx_token_count(para)
        if current_tokens + para_tokens > target_tokens and current:
            chunks.append("\n\n".join(current).strip())
            # start next chunk with the tail of the last one for overlap
            tail = current[-1] if current else ""
            current = [tail] if _approx_token_count(tail) <= overlap_tokens else []
            current_tokens = _approx_token_count("\n\n".join(current)) if current else 0
        current.append(para)
        current_tokens += para_tokens
    if current:
        chunks.append("\n\n".join(current).strip())
    return chunks


# ---------------------------------------------------------------------------
@dataclass
class DocumentRecord:
    source_id: str
    title: str
    text: str
    doc_type: str  # PDF | MD | TXT | FAQ
    metadata: dict


def load_text_file(path: Path) -> DocumentRecord:
    text = path.read_text(encoding="utf-8", errors="ignore")
    return DocumentRecord(
        source_id=path.stem,
        title=path.stem.replace("_", " ").title(),
        text=text,
        doc_type="MD" if path.suffix.lower() == ".md" else "TXT",
        metadata={
            "domain": path.parent.name,
            "source_path": str(path),
        },
    )


def load_pdf(path: Path) -> DocumentRecord:
    try:
        from pypdf import PdfReader  # type: ignore
    except Exception:  # noqa: BLE001
        return load_text_file(path)
    reader = PdfReader(str(path))
    pages: list[str] = []
    for page in reader.pages:
        try:
            pages.append(page.extract_text() or "")
        except Exception:  # noqa: BLE001
            pages.append("")
    return DocumentRecord(
        source_id=path.stem,
        title=path.stem.replace("_", " ").title(),
        text="\n\n".join(pages),
        doc_type="PDF",
        metadata={
            "domain": path.parent.name,
            "source_path": str(path),
        },
    )


def iter_documents(root: Path) -> Iterator[DocumentRecord]:
    if not root.exists():
        return
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        suffix = path.suffix.lower()
        if suffix in {".md", ".txt"}:
            yield load_text_file(path)
        elif suffix == ".pdf":
            yield load_pdf(path)


# ---------------------------------------------------------------------------
def _faq_chunk(row: dict) -> DocumentRecord:
    question = row.get("question", "").strip()
    answer = row.get("answer", "").strip()
    domain = row.get("domain", "GENERAL").strip() or "GENERAL"
    role = row.get("role", "").strip()
    product = row.get("product", "").strip()
    freshness = row.get("freshness", "").strip()
    text = f"Q: {question}\nA: {answer}"
    return DocumentRecord(
        source_id=f"faq_{uuid.uuid5(uuid.NAMESPACE_URL, question).hex[:10]}",
        title=question[:80] or "FAQ",
        text=text,
        doc_type="FAQ",
        metadata={
            "domain": domain,
            "role": role,
            "product": product,
            "freshness": freshness,
            "question": question,
            "answer": answer,
        },
    )


def iter_faqs(csv_path: Path) -> Iterator[DocumentRecord]:
    if not csv_path.exists():
        return
    with csv_path.open(encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            if not row.get("question"):
                continue
            yield _faq_chunk(row)


# ---------------------------------------------------------------------------
def build_chunks(records: Iterable[DocumentRecord]) -> Iterator[Chunk]:
    for record in records:
        pieces = _chunk_text(
            record.text,
            target_tokens=CHUNK_TARGET_TOKENS,
            overlap_tokens=CHUNK_OVERLAP_TOKENS,
        ) or [record.text]
        for idx, piece in enumerate(pieces):
            meta = {
                **record.metadata,
                "source_id": record.source_id,
                "title": record.title,
                "doc_type": record.doc_type,
                "chunk_index": idx,
                "chunk_count": len(pieces),
            }
            yield Chunk(
                id=f"{record.source_id}::{idx}",
                text=piece.strip(),
                metadata=meta,
            )


def ingest(
    *,
    documents_root: Path,
    faqs_csv: Path,
    reset: bool = False,
) -> dict:
    store = VectorStore()
    embedder = Embedder()
    if reset:
        store.reset()

    records: list[DocumentRecord] = []
    records.extend(iter_documents(documents_root))
    records.extend(iter_faqs(faqs_csv))

    chunks = list(build_chunks(records))
    if not chunks:
        return {"documents": 0, "chunks": 0, "collection_size": store.count()}

    embeddings = embedder.embed([c.text for c in chunks])
    for chunk, vec in zip(chunks, embeddings):
        chunk.embedding = vec

    inserted = store.upsert(chunks)
    return {
        "documents": len(records),
        "chunks": inserted,
        "collection_size": store.count(),
    }
