#!/usr/bin/env bash
# examples/start_ryuki.sh — Safe launcher for Ryuki Nox on Linux/macOS
#
# What this script does:
#   - checks ANTHROPIC_API_KEY
#   - sets recommended TORMENT env defaults for Ryuki
#   - reuses an already-running TORMENT server if present
#   - otherwise starts one locally
#   - launches examples/ryuki_chat.py
#   - only shuts down the server if this script started it
#
# Usage:
#   export ANTHROPIC_API_KEY=sk-ant-...
#   bash examples/start_ryuki.sh
#
# Optional overrides:
#   export TORMENT_URL=http://127.0.0.1:8787
#   export TORMENT_WORKSPACE=ryuki
#   export TORMENT_AGENT=ryuki_nox
#   export CLAUDE_MODEL=claude-sonnet-4-6
#
# Notes:
#   - This script does NOT install dependencies.
#   - Install requirements first before using it.
#   - It assumes you are running from the repo root.

set -euo pipefail

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

TORMENT_URL="${TORMENT_URL:-http://127.0.0.1:8787}"
TORMENT_WORKSPACE="${TORMENT_WORKSPACE:-ryuki}"
TORMENT_AGENT="${TORMENT_AGENT:-ryuki_nox}"
CLAUDE_MODEL="${CLAUDE_MODEL:-claude-sonnet-4-6}"

SERVER_STARTED_BY_SCRIPT=0
TORMENT_PID=""

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

info() {
    echo "  • $1"
}

ok() {
    echo "  ✅ $1"
}

warn() {
    echo "  ⚠️  $1"
}

cleanup() {
    if [[ "${SERVER_STARTED_BY_SCRIPT}" == "1" && -n "${TORMENT_PID}" ]]; then
        echo ""
        info "Stopping TORMENT server (PID ${TORMENT_PID})..."
        kill "${TORMENT_PID}" 2>/dev/null || true
        wait "${TORMENT_PID}" 2>/dev/null || true
        ok "Server stopped."
    fi
}

trap cleanup EXIT

health_ok() {
    curl -fsS "${TORMENT_URL}/health" >/dev/null 2>&1
}

require_cmd() {
    if ! command -v "$1" >/dev/null 2>&1; then
        echo ""
        echo "  Error: required command not found: $1"
        echo ""
        exit 1
    fi
}

# ---------------------------------------------------------------------------
# Preflight
# ---------------------------------------------------------------------------

echo ""
echo "========================================================================"
echo "  Ryuki Nox launcher"
echo "========================================================================"

if [[ -z "${ANTHROPIC_API_KEY:-}" ]]; then
    echo ""
    echo "  Error: ANTHROPIC_API_KEY not set."
    echo "  Run: export ANTHROPIC_API_KEY=sk-ant-..."
    echo ""
    exit 1
fi

require_cmd python
require_cmd curl

# Recommended TORMENT env defaults for this launcher
export TORMENT_EMBED_PROVIDER="${TORMENT_EMBED_PROVIDER:-st}"
export TORMENT_EMBED_MODEL="${TORMENT_EMBED_MODEL:-BAAI/bge-small-en-v1.5}"
export TORMENT_EMBED_DEVICE="${TORMENT_EMBED_DEVICE:-cpu}"
export TORMENT_PROFILE="${TORMENT_PROFILE:-companion}"
export TORMENT_CHARACTER_ENABLE="${TORMENT_CHARACTER_ENABLE:-1}"

info "TORMENT_URL      = ${TORMENT_URL}"
info "WORKSPACE        = ${TORMENT_WORKSPACE}"
info "AGENT            = ${TORMENT_AGENT}"
info "CLAUDE_MODEL     = ${CLAUDE_MODEL}"
info "EMBED_PROVIDER   = ${TORMENT_EMBED_PROVIDER}"
info "EMBED_MODEL      = ${TORMENT_EMBED_MODEL}"
info "EMBED_DEVICE     = ${TORMENT_EMBED_DEVICE}"
echo ""

# ---------------------------------------------------------------------------
# Server startup / reuse
# ---------------------------------------------------------------------------

if health_ok; then
    ok "Reusing existing TORMENT server at ${TORMENT_URL}"
else
    info "No running TORMENT server detected. Starting one..."
    python -m torment_service.app &
    TORMENT_PID=$!
    SERVER_STARTED_BY_SCRIPT=1

    info "Waiting for server readiness..."
    READY=0
    for _ in $(seq 1 30); do
        if health_ok; then
            READY=1
            break
        fi
        sleep 1
    done

    if [[ "${READY}" != "1" ]]; then
        echo ""
        echo "  Error: TORMENT server failed to become ready at ${TORMENT_URL}"
        echo ""
        exit 1
    fi

    ok "TORMENT server ready (PID ${TORMENT_PID})"
fi

# ---------------------------------------------------------------------------
# Launch Ryuki chat
# ---------------------------------------------------------------------------

echo ""
info "Launching examples/ryuki_chat.py ..."
echo ""

python examples/ryuki_chat.py