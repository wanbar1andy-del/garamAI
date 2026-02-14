
# Start Micro Live (Real Money) - Single Day Supervision
# CAUTION: This enables REAL TRADING.

$LogDir = "logs/live"
if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir }

$DateStr = Get-Date -Format "yyyyMMdd"
$LogFile = "$LogDir/micro_live_$DateStr.log"

Write-Host "=============================================" -ForegroundColor Red
Write-Host "   GARAM MICRO LIVE - REAL MONEY EXECUTION   " -ForegroundColor Red
Write-Host "=============================================" -ForegroundColor Red
Write-Host "Config: config/profile_micro_live.yaml"
Write-Host "Capital: 1,000,000 KRW"
Write-Host "Log: $LogFile"

Write-Host "Starting Engine..."
# Check if python is available
python --version

python -m pipeline.live.run_live_paper --config config/profile_micro_live.yaml --mode live --real-money --log_dir $LogDir
