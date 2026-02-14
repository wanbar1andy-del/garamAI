param(
    [string]$ProjectRoot = "C:\garam\garam",
    [string]$GitSha = "phase10_ops",
    [string]$Python64 = "C:\Python313\python.exe"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Kill engine(s)
Write-Host "[OPS] Stopping existing Engine processes..." -ForegroundColor Yellow
Get-WmiObject Win32_Process |
Where-Object { $_.CommandLine -like "*run_live_paper_x6d.py*" } |
ForEach-Object { 
    Write-Host " - Killing PID $($_.ProcessId)" -ForegroundColor DarkGray
    Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue 
}

# Relaunch
Write-Host "[OPS] Launching new Engine..." -ForegroundColor Green
$shell = "powershell"
if (Get-Command pwsh -ErrorAction SilentlyContinue) { $shell = "pwsh" }

Start-Process -FilePath $shell -WorkingDirectory $ProjectRoot -ArgumentList @(
    "-NoExit", "-ExecutionPolicy", "Bypass", "-Command",
    "`$env:GIT_SHA='$GitSha'; & '$Python64' scripts/run_live_paper_x6d.py --config config/live_paper.yaml"
)

Write-Host "[OK] Engine restarted." -ForegroundColor Cyan
