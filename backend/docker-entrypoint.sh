#!/bin/sh
# Seed the KB on first boot, then hand off to the CMD (uvicorn by default).
set -e

CHROMA_DIR="${CHROMA_PATH:-/app/data/chroma}"
COLLECTION="${CHROMA_COLLECTION:-vartalaap_kb}"
SEED_MARK="${CHROMA_DIR}/${COLLECTION}.jsonl"

mkdir -p "$CHROMA_DIR" "${OBSERVABILITY_LOG_DIR:-/app/logs}" "${MLFLOW_TRACKING_URI:-/app/mlruns}"

if [ ! -f "$SEED_MARK" ]; then
    echo "[vartalaap] KB not seeded yet — running scripts/seed_kb.py --reset (first-run only)"
    python -m scripts.seed_kb --reset || echo "[vartalaap] seed failed, continuing"
else
    echo "[vartalaap] KB found at $SEED_MARK — skipping seed"
fi

exec "$@"
