<#
.SYNOPSIS
    Garam System Morning Bootstrap Script
.DESCRIPTION
    Automates the daily startup process for the Garam Trading System.
    1. Checks for Administrator privileges.
    2. Verifies Kiwoom Open API connection.
    3. Runs System Health Check.
    4. (Optional) Starts the Shadow Loop.
.EXAMPLE
    .\scripts\morning_bootstrap.ps1 -StartShadow
#>

param (
    [switch]$StartShadow = $false
)

# 1. Check Admin Privileges
$currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Error "This script must be run as Administrator to access Kiwoom API components."
    exit 1
}

Write-Host "=[ GARAM SYSTEM BOOTSTRAP ]=" -ForegroundColor Cyan
Write-Host "Time: $(Get-Date)" -ForegroundColor Gray

# 2. Check Kiwoom Session (32-bit Python)
Write-Host "`n[1/3] Checking Kiwoom Session..." -ForegroundColor Yellow
# Assuming a specific 32-bit python environment or using the system's python if it's 32-bit compatible for PyQt5
# For now, we'll try 'python' and hope the user has the environment set up as per requirements.
# In a real deployment, might need full path to 32-bit python executable.
try {
    python scripts/check_kiwoom_session.py
    if ($LASTEXITCODE -eq 0) {
        Write-Host "SUCCESS: Kiwoom Connected." -ForegroundColor Green
    }
    else {
        Write-Error "FAILURE: Kiwoom NOT Connected. Please log in manually via KOA Studio or restart."
        exit 1
    }
}
catch {
    Write-Error "Failed to execute session check script."
    exit 1
}

# 3. Run System Health Check
Write-Host "`n[2/3] Running System Health Check..." -ForegroundColor Yellow
try {
    python scripts/run_system_health_check.py
    if ($LASTEXITCODE -eq 0) {
        Write-Host "SUCCESS: System Health OK." -ForegroundColor Green
    }
    else {
        Write-Warning "WARNING: System Health Check returned issues. Review logs."
        # We don't exit here, just warn, as some warnings might be acceptable (e.g. disk usage 80%)
    }
}
catch {
    Write-Error "Failed to execute health check."
    exit 1
}

# 4. Start Trading Loop (Shadow or Live Paper)
if ($StartShadow) {
    Write-Host "`n[3/3] Starting Trading Loop..." -ForegroundColor Yellow
    
    # Determine mode (default to SHADOW if not specified in env, but here we can force or parameterize)
    # For now, let's default to LIVE_PAPER if this script is run with a specific flag, or just use SHADOW as default.
    # Let's add a -Mode param.
    
    $Mode = "SHADOW"
    if ($env:TRADING_MODE) { $Mode = $env:TRADING_MODE }
    
    Write-Host "Mode: $Mode" -ForegroundColor Cyan
    
    # Start in a new window
    Start-Process python -ArgumentList "scripts/run_shadow_loop.py --mode=$Mode" -WorkingDirectory "$PSScriptRoot\.."
    Write-Host "Trading Loop ($Mode) started in new window." -ForegroundColor Green
}
else {
    Write-Host "`n[3/3] Trading Loop skipped (use -StartShadow to launch)." -ForegroundColor Gray
}

Write-Host "`nBootstrap Complete." -ForegroundColor Cyan
