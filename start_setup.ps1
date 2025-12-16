# GARAM Initialization Script
# Run this script to set up the directory structure and environment.

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot

Write-Host "=============================="
Write-Host " GARAM System Setup v2.0"
Write-Host "=============================="

# 1. Directory Structure Verification
$required_dirs = @(
    "AgentKit",
    "GARAM_LocalAI",
    "GARAM_Data",
    "GARAM_Data/logs",
    "GARAM_Data/evidence",
    "GaramUI",
    "garam_core",
    "archive"
)

foreach ($dir in $required_dirs) {
    $path = Join-Path $root $dir
    if (-not (Test-Path $path)) {
        New-Item -ItemType Directory -Path $path -Force | Out-Null
        Write-Host "[+] Created directory: $dir"
    } else {
        Write-Host "[*] Exists: $dir"
    }
}

# 2. Config Initialization
$env_path = Join-Path $root ".env"
if (-not (Test-Path $env_path)) {
    $env_content = @"
# GARAM Environment Configuration
GARAM_ENV=development
GARAM_ROOT=$root
KIWOOM_ACCOUNT=
TELEGRAM_TOKEN=
TELEGRAM_CHAT_ID=
OPENAI_API_KEY=
"@
    Set-Content -Path $env_path -Value $env_content -Encoding UTF8
    Write-Host "[+] Created .env template."
} else {
    Write-Host "[*] .env already exists."
}

# 3. Path Setup (Optional convenience)
# (Could verify Python path here)

Write-Host "------------------------------"
Write-Host "Setup Complete."
Write-Host "Please edit .env with your API keys."
