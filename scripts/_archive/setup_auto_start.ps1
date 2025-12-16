# GARAM Paper Trading - Automatic Task Scheduler Setup
# Run this script as Administrator to create automatic startup

$taskName = "GARAM_Paper_Trading_Auto"
$scriptPath = "C:\garam\garam\scripts\start_paper_trading.bat"
$logPath = "C:\garam\garam\GARAM_Data\logs\scheduler.log"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "GARAM Paper Trading - Auto Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if running as Administrator
$currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
$isAdmin = $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "ERROR: This script must run as Administrator!" -ForegroundColor Red
    Write-Host "Right-click PowerShell and select 'Run as Administrator'" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit
}

Write-Host "[1/3] Checking if task already exists..." -ForegroundColor Yellow

# Remove existing task if it exists
$existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($existingTask) {
    Write-Host "  Found existing task. Removing..." -ForegroundColor Gray
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
}

Write-Host "[2/3] Creating new scheduled task..." -ForegroundColor Yellow

# Create action
$action = New-ScheduledTaskAction -Execute $scriptPath -WorkingDirectory "C:\garam\garam"

# Create trigger for weekdays at 08:50 AM
$trigger = New-ScheduledTaskTrigger -Daily -At 8:50AM

# Only run on weekdays (Monday to Friday)
$trigger.DaysOfWeek = "Monday", "Tuesday", "Wednesday", "Thursday", "Friday"

# Settings
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable `
    -DontStopOnIdleEnd

# Principal (run whether user is logged on or not)
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType S4U -RunLevel Highest

# Register the task
Register-ScheduledTask `
    -TaskName $taskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Principal $principal `
    -Description "GARAM Paper Trading - Automatic startup at market open (Mon-Fri 08:50)"

Write-Host "[3/3] Verifying task..." -ForegroundColor Yellow

$newTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($newTask) {
    Write-Host ""
    Write-Host "SUCCESS: Task created successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Task Details:" -ForegroundColor Cyan
    Write-Host "  Name: $taskName" -ForegroundColor White
    Write-Host "  Schedule: Every weekday (Mon-Fri) at 08:50 AM" -ForegroundColor White
    Write-Host "  Action: Start paper trading" -ForegroundColor White
    Write-Host "  Condition: Computer must be ON" -ForegroundColor White
    Write-Host ""
    Write-Host "What happens tomorrow:" -ForegroundColor Yellow
    Write-Host "  1. At 08:50, Windows will automatically run the script" -ForegroundColor White
    Write-Host "  2. Script waits until 09:00 (market open)" -ForegroundColor White
    Write-Host "  3. Paper trading starts with Kiwoom connection" -ForegroundColor White
    Write-Host "  4. Dashboard updates in real-time" -ForegroundColor White
    Write-Host ""
    Write-Host "To view task: Open Task Scheduler > Task Scheduler Library > $taskName" -ForegroundColor Gray
} else {
    Write-Host ""
    Write-Host "ERROR: Failed to create task!" -ForegroundColor Red
}

Write-Host ""
Read-Host "Press Enter to exit"
