#!/usr/bin/env bash
set -euo pipefail
export TORMENT_DATA_DIR="${TORMENT_DATA_DIR:-$(pwd)/data}"
python -m uvicorn torment_service.app:app --host 127.0.0.1 --port 8787
