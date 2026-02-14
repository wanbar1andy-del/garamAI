
# Start Paper Live (Real Feed) - Dry Run
# This uses Realtime Feed from Kiwoom but Mock Execution (Paper Money)

$LogDir = "logs/live_paper_real"
if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir }

$DateStr = Get-Date -Format "yyyyMMdd"
$LogFile = "$LogDir/paper_live_$DateStr.log"

Write-Host "=============================================" -ForegroundColor Green
Write-Host "   GARAM PAPER LIVE - REAL FEED MONITORING   " -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Green
Write-Host "Config: config/profile_micro_live.yaml"
Write-Host "Execution: PAPER (MOCK)"
Write-Host "Feed: REAL (Kiwoom)"
Write-Host "Log: $LogFile"

Write-Host "Starting Engine..."
# Check if python is available
python --version

# Run without --real-money flag
python -m pipeline.live.run_live_paper --config config/profile_micro_live.yaml --mode live --log_dir $LogDir
