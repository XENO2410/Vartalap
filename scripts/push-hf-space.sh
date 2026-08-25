#!/usr/bin/env bash
# Push backend/ to a Hugging Face Space via git subtree.
# Usage:
#   ./scripts/push-hf-space.sh XENO2410 vartalaap-api
# One-time prereqs:
#   - Create the Space at https://huggingface.co/new-space (Docker SDK).
#   - Create a write token at https://huggingface.co/settings/tokens
#     and export HF_TOKEN=hf_... before running.

set -euo pipefail

OWNER="${1:?Space owner required, e.g. XENO2410}"
NAME="${2:?Space name required, e.g. vartalaap-api}"
BRANCH="${3:-main}"
PREFIX="${4:-backend}"

if [ -z "${HF_TOKEN:-}" ]; then
  read -r -s -p "Hugging Face write token (hf_...): " HF_TOKEN
  echo
fi

REMOTE="hf-${NAME}"
URL="https://${OWNER}:${HF_TOKEN}@huggingface.co/spaces/${OWNER}/${NAME}"

echo "→ Setting remote '${REMOTE}'"
git remote remove "${REMOTE}" 2>/dev/null || true
git remote add "${REMOTE}" "${URL}"

echo "→ Pushing '${PREFIX}' subtree to ${REMOTE}/${BRANCH}"
git subtree push --prefix="${PREFIX}" "${REMOTE}" "${BRANCH}"

echo
echo "✓ Done. Space is building at:"
echo "  https://huggingface.co/spaces/${OWNER}/${NAME}"
echo
echo "Remove the tokenized remote when finished:"
echo "  git remote remove ${REMOTE}"
