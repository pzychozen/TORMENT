# examples/start_ryuki.ps1 — Safe launcher for Ryuki Nox on Windows PowerShell
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
#   $env:ANTHROPIC_API_KEY="sk-ant-..."
#   .\examples\start_ryuki.ps1
#
# Optional overrides:
#   $env:TORMENT_URL="http://127.0.0.1:8787"
#   $env:TORMENT_WORKSPACE="ryuki"
#   $env:TORMENT_AGENT="ryuki_nox"
#   $env:CLAUDE_MODEL="claude-sonnet-4-20250514"
#
# Notes:
#   - This script does NOT install dependencies.
#   - Install requirements first before using it.
#   - It assumes you are running from the repo root.

$ErrorActionPreference = "Stop"

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

if (-not $env:TORMENT_URL)       { $env:TORMENT_URL = "http://127.0.0.1:8787" }
if (-not $env:TORMENT_WORKSPACE) { $env:TORMENT_WORKSPACE = "ryuki" }
if (-not $env:TORMENT_AGENT)     { $env:TORMENT_AGENT = "ryuki_nox" }
if (-not $env:CLAUDE_MODEL)      { $env:CLAUDE_MODEL = "claude-sonnet-4-20250514" }

if (-not $env:TORMENT_EMBED_PROVIDER)   { $env:TORMENT_EMBED_PROVIDER = "st" }
if (-not $env:TORMENT_EMBED_MODEL)      { $env:TORMENT_EMBED_MODEL = "BAAI/bge-small-en-v1.5" }
if (-not $env:TORMENT_EMBED_DEVICE)     { $env:TORMENT_EMBED_DEVICE = "cpu" }
if (-not $env:TORMENT_PROFILE)          { $env:TORMENT_PROFILE = "companion" }
if (-not $env:TORMENT_CHARACTER_ENABLE) { $env:TORMENT_CHARACTER_ENABLE = "1" }

$serverStartedByScript = $false
$serverProcess = $null

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

function Write-Info($msg) {
    Write-Host "  • $msg"
}

function Write-Ok($msg) {
    Write-Host "  ✅ $msg"
}

function Write-Warn($msg) {
    Write-Host "  ⚠️  $msg"
}

function Test-TormentHealth {
    try {
        $null = Invoke-RestMethod -Uri "$($env:TORMENT_URL)/health" -TimeoutSec 2
        return $true
    } catch {
        return $false
    }
}

function Cleanup-Server {
    if ($serverStartedByScript -and $null -ne $serverProcess) {
        Write-Host ""
        Write-Info "Stopping TORMENT server (PID $($serverProcess.Id))..."
        try {
            Stop-Process -Id $serverProcess.Id -ErrorAction SilentlyContinue
        } catch {
        }
        Write-Ok "Server stopped."
    }
}

# ---------------------------------------------------------------------------
# Preflight
# ---------------------------------------------------------------------------

Write-Host ""
Write-Host "========================================================================"
Write-Host "  Ryuki Nox launcher"
Write-Host "========================================================================"

if (-not $env:ANTHROPIC_API_KEY) {
    Write-Host ""
    Write-Host "  Error: ANTHROPIC_API_KEY not set."
    Write-Host '  Run: $env:ANTHROPIC_API_KEY="sk-ant-..."'
    Write-Host ""
    exit 1
}

try {
    $null = Get-Command python -ErrorAction Stop
} catch {
    Write-Host ""
    Write-Host "  Error: python is not available in PATH."
    Write-Host ""
    exit 1
}

Write-Info "TORMENT_URL      = $($env:TORMENT_URL)"
Write-Info "WORKSPACE        = $($env:TORMENT_WORKSPACE)"
Write-Info "AGENT            = $($env:TORMENT_AGENT)"
Write-Info "CLAUDE_MODEL     = $($env:CLAUDE_MODEL)"
Write-Info "EMBED_PROVIDER   = $($env:TORMENT_EMBED_PROVIDER)"
Write-Info "EMBED_MODEL      = $($env:TORMENT_EMBED_MODEL)"
Write-Info "EMBED_DEVICE     = $($env:TORMENT_EMBED_DEVICE)"
Write-Host ""

# ---------------------------------------------------------------------------
# Server startup / reuse
# ---------------------------------------------------------------------------

if (Test-TormentHealth) {
    Write-Ok "Reusing existing TORMENT server at $($env:TORMENT_URL)"
} else {
    Write-Info "No running TORMENT server detected. Starting one..."
    $serverProcess = Start-Process python -ArgumentList "-m", "torment_service.app" -PassThru -NoNewWindow
    $serverStartedByScript = $true

    Write-Info "Waiting for server readiness..."
    $ready = $false
    for ($i = 0; $i -lt 30; $i++) {
        if (Test-TormentHealth) {
            $ready = $true
            break
        }
        Start-Sleep -Seconds 1
    }

    if (-not $ready) {
        Write-Host ""
        Write-Host "  Error: TORMENT server failed to become ready at $($env:TORMENT_URL)"
        Write-Host ""
        Cleanup-Server
        exit 1
    }

    Write-Ok "TORMENT server ready (PID $($serverProcess.Id))"
}

# ---------------------------------------------------------------------------
# Launch Ryuki chat
# ---------------------------------------------------------------------------

try {
    Write-Host ""
    Write-Info "Launching examples/ryuki_chat.py ..."
    Write-Host ""

    python examples/ryuki_chat.py
}
finally {
    Cleanup-Server
}