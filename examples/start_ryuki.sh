#!/usr/bin/env bash
# start_ryuki.sh — Launch helper for Ryuki Nox
#
# Usage:
#   1. Set your API key:  export ANTHROPIC_API_KEY=sk-ant-...
#   2. Run this script:   bash examples/start_ryuki.sh
#
# This script:
#   - Installs dependencies if needed
#   - Configures real embeddings
#   - Starts the TORMENT server in the background
#   - Waits for it to be ready
#   - Launches the Ryuki chat client

set -e

# --- Check API key ---
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo ""
    echo "  Error: ANTHROPIC_API_KEY not set."
    echo "  Run: export ANTHROPIC_API_KEY=sk-ant-..."
    echo ""
    exit 1
fi

# --- Install deps ---
echo "  Installing dependencies..."
pip install -q requests anthropic sentence-transformers 2>/dev/null || \
pip install requests anthropic sentence-transformers

pip install -q -r requirements.txt 2>/dev/null || true

# --- Configure embeddings ---
export TORMENT_EMBED_PROVIDER=st
export TORMENT_EMBED_MODEL=BAAI/bge-small-en-v1.5
export TORMENT_EMBED_DEVICE=cpu
export TORMENT_PROFILE=companion
export TORMENT_CHARACTER_ENABLE=1

# --- Start TORMENT server ---
TORMENT_URL="${TORMENT_URL:-http://127.0.0.1:8787}"

echo "  Starting TORMENT server..."
python -m torment_service.app &
TORMENT_PID=$!

# Wait for server to be ready
echo "  Waiting for server..."
for i in $(seq 1 30); do
    if curl -s "${TORMENT_URL}/health" > /dev/null 2>&1; then
        echo "  TORMENT server ready (PID $TORMENT_PID)."
        break
    fi
    sleep 1
done

if ! curl -s "${TORMENT_URL}/health" > /dev/null 2>&1; then
    echo "  Error: TORMENT server failed to start."
    kill $TORMENT_PID 2>/dev/null || true
    exit 1
fi

# --- Launch chat ---
echo ""
python examples/ryuki_chat.py

# --- Cleanup ---
echo "  Stopping TORMENT server..."
kill $TORMENT_PID 2>/dev/null || true
wait $TORMENT_PID 2>/dev/null || true
echo "  Done."
