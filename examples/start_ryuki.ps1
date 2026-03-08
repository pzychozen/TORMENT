# start_ryuki.ps1 — Launch helper for Ryuki Nox (Windows PowerShell)
#
# Usage:
#   1. Set your API key:  $env:ANTHROPIC_API_KEY="sk-ant-..."
#   2. Run this script:   .\examples\start_ryuki.ps1

# --- Check API key ---
if (-not $env:ANTHROPIC_API_KEY) {
    Write-Host ""
    Write-Host "  Error: ANTHROPIC_API_KEY not set."
    Write-Host '  Run: $env:ANTHROPIC_API_KEY="sk-ant-..."'
    Write-Host ""
    exit 1
}

# --- Install deps ---
Write-Host "  Installing dependencies..."
pip install requests anthropic sentence-transformers -q 2>$null
pip install -r requirements.txt -q 2>$null

# --- Configure embeddings ---
$env:TORMENT_EMBED_PROVIDER = "st"
$env:TORMENT_EMBED_MODEL = "BAAI/bge-small-en-v1.5"
$env:TORMENT_EMBED_DEVICE = "cpu"
$env:TORMENT_PROFILE = "companion"
$env:TORMENT_CHARACTER_ENABLE = "1"

# --- Start TORMENT server ---
Write-Host "  Starting TORMENT server..."
$serverJob = Start-Process python -ArgumentList "-m", "torment_service.app" -PassThru -NoNewWindow

# Wait for server
Write-Host "  Waiting for server..."
$ready = $false
for ($i = 0; $i -lt 30; $i++) {
    try {
        $null = Invoke-RestMethod -Uri "http://127.0.0.1:8787/health" -TimeoutSec 2
        $ready = $true
        Write-Host "  TORMENT server ready (PID $($serverJob.Id))."
        break
    } catch {
        Start-Sleep -Seconds 1
    }
}

if (-not $ready) {
    Write-Host "  Error: TORMENT server failed to start."
    Stop-Process -Id $serverJob.Id -ErrorAction SilentlyContinue
    exit 1
}

# --- Launch chat ---
Write-Host ""
python examples/ryuki_chat.py

# --- Cleanup ---
Write-Host "  Stopping TORMENT server..."
Stop-Process -Id $serverJob.Id -ErrorAction SilentlyContinue
Write-Host "  Done."
