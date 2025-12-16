# GARAM Unified Launcher
# Usage: ./run_garam.ps1 -Mode [Live|Backtest|Research] -Profile [Safe|Aggressive]

param (
    [string]$Mode = "Research",
    [string]$Profile = "Safe"
)

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
$python_cmd = "python" # Assumes python is in path or venv active

Write-Host "=============================="
Write-Host " GARAM Generic Launcher"
Write-Host " Mode: $Mode"
Write-Host " Profile: $Profile"
Write-Host "=============================="

# 1. Environment Check
if (-not (Test-Path "$root/.env")) {
    Write-Warning ".env file not found. Running setup..."
    & "$root/start_setup.ps1"
}

# 2. Mode Selection
switch ($Mode.ToLower()) {
    "live" {
        Write-Host "[*] Launching LIVE Trading..."
        # Example: call the live runner
        # & $python_cmd scripts/live/run_live_kiwoom.py --profile $Profile
        Write-Host "Command: $python_cmd garam_core/live/run_live_kiwoom.py --profile $Profile" 
        # Uncomment actual execution when ready
    }
    "backtest" {
        Write-Host "[*] Launching Backtest..."
        # & $python_cmd scripts/research/run_all.py --profile $Profile
    }
    "research" {
        Write-Host "[*] Launching Research Loop..."
        # & $python_cmd scripts/research/run_all.py ...
    }
    default {
        Write-Error "Unknown Mode: $Mode"
    }
}

Write-Host "Done."
