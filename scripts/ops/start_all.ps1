# scripts/ops/start_all.ps1
# Phase 10 Startup Helper (Operational)
# Usage:
#   powershell -ExecutionPolicy Bypass -File scripts/ops/start_all.ps1
#   powershell -ExecutionPolicy Bypass -File scripts/ops/start_all.ps1 -GitSha phase10_ops

param(
    [string]$ProjectRoot = "C:\garam\garam",
    [string]$GitSha = "phase10_ops"
)

Set-StrictMode -Version Latest
Write-Host "[OPS] start_all.ps1 loaded" -ForegroundColor DarkGray
$ErrorActionPreference = "Stop"

Write-Host "=== Starting Phase 10 Operations ===" -ForegroundColor Cyan
Write-Host "ProjectRoot: $ProjectRoot" -ForegroundColor Gray
Write-Host "GIT_SHA    : $GitSha" -ForegroundColor Gray

if (-not (Test-Path $ProjectRoot)) {
    Write-Host "[ERROR] ProjectRoot not found: $ProjectRoot" -ForegroundColor Red
    exit 2
}

# Ensure Logs Directory
$LogDir = Join-Path $ProjectRoot "logs\ops"
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
}

# Explicit Python Paths
$python32 = "C:\Python39-32\python.exe"     # Ingester (Kiwoom)
$python64 = "C:\Python313\python.exe"       # Engine (Logic)

# 32-bit Shell for Ingester
$ps32 = "$env:WINDIR\SysWOW64\WindowsPowerShell\v1.0\powershell.exe"

# 1) Kiwoom Ingester (32-bit Enforced + Boot Log)
if (-not (Test-Path $python32)) {
    Write-Host "[ERROR] 32-bit Python not found at $python32" -ForegroundColor Red
    exit 2
}

Write-Host "[1/2] Launching Kiwoom Ingester (32-bit)..." -ForegroundColor Yellow
$bootLog = Join-Path $LogDir "kiwoom_ingester_boot.log"
$ingester = @{
    FilePath         = $ps32
    WorkingDirectory = $ProjectRoot
    ArgumentList     = @(
        "-NoExit",
        "-ExecutionPolicy", "Bypass",
        "-Command",
        "& '$python32' scripts/ops/ingest_kiwoom_realtime.py 2>&1 | Tee-Object -FilePath '$bootLog'"
    )
}
Start-Process @ingester

# 2) Shadow Engine (64-bit Enforced)
if (-not (Test-Path $python64)) {
    Write-Host "[WARN] 64-bit Python not found at $python64. Falling back to default 'python'." -ForegroundColor Yellow
    $python64 = "python"
}

Write-Host "[2/2] Launching Shadow Engine (Live Paper)..." -ForegroundColor Yellow
$shell = "powershell"
if (Get-Command pwsh -ErrorAction SilentlyContinue) { $shell = "pwsh" }

$engine = @{
    FilePath         = $shell
    WorkingDirectory = $ProjectRoot
    ArgumentList     = @(
        "-NoExit",
        "-ExecutionPolicy", "Bypass",
        "-Command",
        "`$env:GIT_SHA='$GitSha'; & '$python64' scripts/run_live_paper_x6d.py --config config/live_paper.yaml"
    )
}
Start-Process @engine

Write-Host "Done. Two windows should appear." -ForegroundColor Green
Write-Host " - Window 1: Kiwoom Feed (Login required, 32-bit)" -ForegroundColor Gray
Write-Host " - Window 2: Shadow Engine (Heartbeats)" -ForegroundColor Gray
Write-Host ""
Write-Host "Daily check:" -ForegroundColor Gray
Write-Host "  powershell -ExecutionPolicy Bypass -File scripts/ops/check_daily.ps1" -ForegroundColor Gray
Write-Host "Debug Log: $bootLog" -ForegroundColor DarkGray
exit 0
