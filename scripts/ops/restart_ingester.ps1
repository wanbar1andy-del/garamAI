# scripts/ops/restart_ingester.ps1
# Kiwoom Ingester Restart (32-bit enforced)

param(
    [string]$ProjectRoot = "C:\garam\garam",
    [string]$Python32 = "C:\Python39-32\python.exe",
    [int]$HealthWaitSec = 45,
    [string]$FeedPath = ""   # 비우면 $ProjectRoot\feed_live.jsonl
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ps32 = "$env:WINDIR\SysWOW64\WindowsPowerShell\v1.0\powershell.exe"

# --- Pre-flight ---
if (-not (Test-Path $ProjectRoot)) {
    Write-Host "[ERROR] ProjectRoot not found: $ProjectRoot" -ForegroundColor Red
    exit 2
}
if (-not (Test-Path $ps32)) {
    Write-Host "[ERROR] 32-bit PowerShell not found: $ps32" -ForegroundColor Red
    exit 2
}
if (-not (Test-Path $Python32)) {
    Write-Host "[ERROR] 32-bit Python not found: $Python32" -ForegroundColor Red
    exit 2
}

$logDir = Join-Path $ProjectRoot "logs\ops"
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Force -Path $logDir | Out-Null }
$bootLog = Join-Path $logDir ("kiwoom_ingester_boot_recovery_{0}.log" -f (Get-Date -Format "yyyyMMdd_HHmmss"))

if ([string]::IsNullOrWhiteSpace($FeedPath)) {
    $FeedPath = Join-Path $ProjectRoot "feed_live.jsonl"
}

Write-Host "[OPS] restart_ingester.ps1" -ForegroundColor DarkGray
Write-Host " - ProjectRoot: $ProjectRoot" -ForegroundColor DarkGray
Write-Host " - Python32   : $Python32" -ForegroundColor DarkGray
Write-Host " - FeedPath   : $FeedPath" -ForegroundColor DarkGray
Write-Host " - BootLog    : $bootLog" -ForegroundColor DarkGray

# --- Kill existing ingester(s) ---
Write-Host "[OPS] Stopping existing Ingester processes..." -ForegroundColor Yellow

# 1) Kill python/pythonw running the ingester (if any)
Get-WmiObject Win32_Process |
Where-Object {
    ($_.Name -in @("python.exe", "pythonw.exe")) -and
    ($_.CommandLine -ne $null) -and
    ($_.CommandLine -like "*ingest_kiwoom_realtime.py*")
} |
ForEach-Object {
    Write-Host " - Killing Python PID $($_.ProcessId)" -ForegroundColor DarkGray
    Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
}

# 2) Kill wrapper powershell that launched the ingester (if any)
Get-WmiObject Win32_Process |
Where-Object {
    ($_.Name -eq "powershell.exe") -and
    ($_.CommandLine -ne $null) -and
    ($_.CommandLine -like "*ingest_kiwoom_realtime.py*")
} |
ForEach-Object {
    Write-Host " - Killing PS PID $($_.ProcessId)" -ForegroundColor DarkGray
    Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
}

Start-Sleep -Seconds 1

# --- Relaunch ---
Write-Host "[OPS] Launching new Ingester (32-bit)..." -ForegroundColor Green

# NOTE: -NoProfile 권장 (프로필 훅으로 인한 예기치 않은 간섭 방지)
$p = Start-Process -FilePath $ps32 -WorkingDirectory $ProjectRoot -PassThru -ArgumentList @(
    "-NoExit", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command",
    "& '$Python32' scripts/ops/ingest_kiwoom_realtime.py 2>&1 | Tee-Object -FilePath '$bootLog'"
)

Write-Host "[OK] Ingester restarted." -ForegroundColor Cyan
Write-Host " - Wrapper PID: $($p.Id)" -ForegroundColor Gray
Write-Host " - BootLog    : $bootLog" -ForegroundColor Gray

# --- Quick Health Check: feed freshness ---
if (Test-Path $FeedPath) {
    $t0 = (Get-Item $FeedPath).LastWriteTime
}
else {
    $t0 = $null
}

Write-Host "[OPS] HealthCheck: waiting up to $HealthWaitSec sec for feed update..." -ForegroundColor Yellow

$deadline = (Get-Date).AddSeconds($HealthWaitSec)
$updated = $false

while ((Get-Date) -lt $deadline) {
    if (Test-Path $FeedPath) {
        $t1 = (Get-Item $FeedPath).LastWriteTime
        if ($t0 -eq $null -or $t1 -gt $t0) {
            $updated = $true
            break
        }
    }
    Start-Sleep -Seconds 2
}

if ($updated) {
    $last = (Get-Item $FeedPath).LastWriteTime
    Write-Host "[PASS] Feed is updating. LastWriteTime=$last" -ForegroundColor Green
    exit 0
}
else {
    if (Test-Path $FeedPath) {
        $last = (Get-Item $FeedPath).LastWriteTime
        Write-Host "[WARN] Feed not updated within $HealthWaitSec sec. LastWriteTime=$last" -ForegroundColor Yellow
    }
    else {
        Write-Host "[WARN] Feed file missing: $FeedPath" -ForegroundColor Yellow
    }
    Write-Host "       Check BootLog: $bootLog" -ForegroundColor DarkGray
    exit 1
}
