# scripts/ops/auto_login.ps1
# Auto login/start for market day (weekday 08:45)
param(
    [string]$ProjectRoot = "C:\garam\garam",
    [string]$HolidayFile = "C:\garam\garam\config\krx_holidays.txt"   # optional: YYYY-MM-DD per line
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Is-Holiday([datetime]$d, [string]$holidayFile) {
    if (-not (Test-Path $holidayFile)) { return $false }
    $key = $d.ToString("yyyy-MM-dd")
    $lines = Get-Content $holidayFile -ErrorAction SilentlyContinue
    return $lines -contains $key
}

$now = Get-Date

# Weekend guard
if ($now.DayOfWeek -in @("Saturday", "Sunday")) {
    Write-Host "[INFO] Weekend. Skip auto_login." -ForegroundColor DarkGray
    exit 0
}

# Optional holiday guard
if (Is-Holiday -d $now -holidayFile $HolidayFile) {
    Write-Host "[INFO] Holiday ($($now.ToString('yyyy-MM-dd'))). Skip auto_login." -ForegroundColor DarkGray
    exit 0
}

# Already running guard (avoid duplicate launch)
$already = Get-WmiObject Win32_Process |
Where-Object { $_.CommandLine -ne $null -and $_.CommandLine -like "*ingest_kiwoom_realtime.py*" } |
Select-Object -First 1

if ($already) {
    Write-Host "[INFO] Ingester already running. PID=$($already.ProcessId). Skip." -ForegroundColor DarkGray
    exit 0
}

# Log
$logDir = Join-Path $ProjectRoot "logs\ops"
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Force -Path $logDir | Out-Null }
$log = Join-Path $logDir ("auto_login_{0}.log" -f (Get-Date -Format "yyyyMMdd"))

"[$(Get-Date -Format o)] auto_login start" | Add-Content $log

# Start (your existing start_all handles 32-bit ingester + 64-bit engine)
powershell -ExecutionPolicy Bypass -File (Join-Path $ProjectRoot "scripts\ops\start_all.ps1") *>> $log

"[$(Get-Date -Format o)] auto_login done" | Add-Content $log
exit 0
