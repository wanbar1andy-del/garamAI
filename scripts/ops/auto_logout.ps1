# scripts/ops/auto_logout.ps1
# Auto logout/stop at market close (weekday)
param(
    [string]$ProjectRoot = "C:\garam\garam",
    [string]$HolidayFile = "C:\garam\garam\config\krx_holidays.txt"   # optional
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

# Weekend/holiday guard (optional)
if ($now.DayOfWeek -in @("Saturday", "Sunday")) { exit 0 }
if (Is-Holiday -d $now -holidayFile $HolidayFile) { exit 0 }

$logDir = Join-Path $ProjectRoot "logs\ops"
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Force -Path $logDir | Out-Null }
$log = Join-Path $logDir ("auto_logout_{0}.log" -f (Get-Date -Format "yyyyMMdd"))

"[$(Get-Date -Format o)] auto_logout start" | Add-Content $log

# Kill engine + ingester python/pythonw
$targets = @(
    "ingest_kiwoom_realtime.py",
    "run_live_paper_x6d.py"
)

Get-WmiObject Win32_Process |
Where-Object {
    $_.CommandLine -ne $null -and (
        ($_.Name -in @("python.exe", "pythonw.exe")) -and
        ($targets | ForEach-Object { $_.CommandLine -like "*$_*" } | Where-Object { $_ } | Measure-Object).Count -gt 0
    )
} | ForEach-Object {
    "[$(Get-Date -Format o)] kill python pid=$($_.ProcessId) cmd=$($_.CommandLine)" | Add-Content $log
    Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
}

# Also kill wrapper powershells that contain those scripts (optional but reduces “ghost windows”)
Get-WmiObject Win32_Process |
Where-Object {
    $_.Name -eq "powershell.exe" -and $_.CommandLine -ne $null -and (
        $_.CommandLine -like "*ingest_kiwoom_realtime.py*" -or $_.CommandLine -like "*run_live_paper_x6d.py*"
    )
} | ForEach-Object {
    "[$(Get-Date -Format o)] kill powershell pid=$($_.ProcessId)" | Add-Content $log
    Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
}

"[$(Get-Date -Format o)] auto_logout done" | Add-Content $log
exit 0
