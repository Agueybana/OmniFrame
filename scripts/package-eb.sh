#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUTPUT="${ROOT_DIR}/omniframe-eb.zip"

cd "${ROOT_DIR}"
rm -f "${OUTPUT}"

zip -r "${OUTPUT}" . \
  -x "node_modules/*" \
  -x "dist/*" \
  -x ".venv/*" \
  -x "venv/*" \
  -x ".git/*" \
  -x ".local/*" \
  -x ".run/*" \
  -x ".env" \
  -x ".env.*" \
  -x ".DS_Store" \
  -x "__pycache__/*" \
  -x "*/__pycache__/*" \
  -x ".pytest_cache/*" \
  -x "backend/runtime/*" \
  -x "omniframe-eb.zip"

echo "${OUTPUT}"
