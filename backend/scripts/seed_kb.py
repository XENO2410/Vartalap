"""Seeds the knowledge base from bundled sample data.

Usage (from the `backend/` directory):
    python -m scripts.seed_kb
    python -m scripts.seed_kb --reset
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Allow "python scripts/seed_kb.py" without PYTHONPATH gymnastics.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import BACKEND_ROOT  # noqa: E402
from app.rag import ingest  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed the Vartalaap KB.")
    parser.add_argument("--reset", action="store_true", help="Drop and recreate the Chroma collection.")
    parser.add_argument(
        "--docs",
        default=str(BACKEND_ROOT / "data" / "documents"),
        help="Root directory containing docs (recursively scanned).",
    )
    parser.add_argument(
        "--faqs",
        default=str(BACKEND_ROOT / "data" / "faqs.csv"),
        help="FAQ CSV path.",
    )
    args = parser.parse_args()

    docs_root = Path(args.docs)
    faqs_csv = Path(args.faqs)

    print(f"Documents root : {docs_root}")
    print(f"FAQ CSV        : {faqs_csv}")
    print(f"Reset          : {args.reset}")

    stats = ingest(documents_root=docs_root, faqs_csv=faqs_csv, reset=args.reset)
    print("Ingest complete:")
    for key, value in stats.items():
        print(f"  - {key}: {value}")


if __name__ == "__main__":
    main()
