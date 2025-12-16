<#
.SYNOPSIS
    End-of-Day Batch for Live Paper Trading
.DESCRIPTION
    Runs daily aggregation, dataset building, and optional model training.
#>

$ErrorActionPreference = "Stop"
$today = Get-Date -Format "yyyyMMdd"
$env:TRADING_MODE = "LIVE_PAPER"

Write-Host "=[ EOD BATCH: LIVE_PAPER ($today) ]=" -ForegroundColor Cyan

# 1. Performance Aggregation
Write-Host "`n[1/3] Aggregating Performance..." -ForegroundColor Yellow
try {
    python scripts/run_shadow_performance.py --mode=LIVE_PAPER --date=$today
    Write-Host "Success." -ForegroundColor Green
}
catch {
    Write-Error "Failed to aggregate performance."
}

# 2. Build AI Dataset
Write-Host "`n[2/3] Building AI Dataset..." -ForegroundColor Yellow
try {
    # Assuming build_ai_dataset.py supports mode or we point it to the right logs
    # We might need to update build_ai_dataset.py to accept --mode
    # For now, let's assume it reads from config or we pass paths.
    # If not updated yet, this might fail or read shadow logs.
    # TODO: Update build_ai_dataset.py to support mode if needed.
    # For now, skip if not critical or run with warning.
    Write-Warning "AI Dataset build skipped (Pending NP-14.4 update for build_ai_dataset.py)"
}
catch {
    Write-Error "Failed to build dataset."
}

# 3. Model Training (Optional)
Write-Host "`n[3/3] Model Training (Skipped for now)..." -ForegroundColor Gray

Write-Host "`nEOD Batch Complete." -ForegroundColor Cyan
