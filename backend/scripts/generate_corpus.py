"""Materialise the 10x corpus modules into backend/data/documents/<bubble>/<slug>.md.

Usage (from the `backend/` directory):
    python -m scripts.generate_corpus

The script writes one markdown file per doc entry found in the corpus modules
(corpus_people, corpus_bank, corpus_ops, corpus_ai). Existing generated files
are overwritten; other documents in the tree are left untouched.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Allow "python scripts/generate_corpus.py" without PYTHONPATH gymnastics.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import BACKEND_ROOT  # noqa: E402

import scripts.corpus_ai as corpus_ai  # noqa: E402
import scripts.corpus_bank as corpus_bank  # noqa: E402
import scripts.corpus_ops as corpus_ops  # noqa: E402
import scripts.corpus_people as corpus_people  # noqa: E402

MODULES = [corpus_people, corpus_bank, corpus_ops, corpus_ai]

DOCS_ROOT = BACKEND_ROOT / "data" / "documents"


def main() -> None:
    total = 0
    per_bubble: dict[str, int] = {}

    for module in MODULES:
        for doc in module.DOCS:
            bubble = doc["bubble"]
            slug = doc["slug"]
            title = doc["title"]
            body = doc["body"].strip()

            out_dir = DOCS_ROOT / bubble
            out_dir.mkdir(parents=True, exist_ok=True)
            out_path = out_dir / f"{slug}.md"
            out_path.write_text(f"# {title}\n\n{body}\n", encoding="utf-8")

            total += 1
            per_bubble[bubble] = per_bubble.get(bubble, 0) + 1

    print("Generated corpus documents:")
    for bubble in sorted(per_bubble):
        print(f"  - {bubble}: {per_bubble[bubble]}")
    print(f"  TOTAL: {total}")


if __name__ == "__main__":
    main()
