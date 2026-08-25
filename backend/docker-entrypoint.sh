#!/bin/sh
# Seed the KB on first boot, then hand off to the CMD (uvicorn by default).
set -e

SEED_MARK="/app/data/chroma/${CHROMA_COLLECTION:-vartalaap_kb}.jsonl"

if [ ! -f "$SEED_MARK" ]; then
    echo "[vartalaap] KB not seeded yet — running scripts/seed_kb.py --reset (first-run only)"
    python -m scripts.seed_kb --reset || echo "[vartalaap] seed failed, continuing"
else
    echo "[vartalaap] KB found at $SEED_MARK — skipping seed"
fi

exec "$@"
