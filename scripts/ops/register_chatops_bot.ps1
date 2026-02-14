$ErrorActionPreference = "Stop"
Write-Host "Registering Garam ChatOps Bot..." -ForegroundColor Cyan

# Bot Task (At Startup + Run Now)
# Daemon script so we want it to start on boot
$action = New-ScheduledTaskAction -Execute "C:\Python313\python.exe" -Argument "C:\garam\garam\utils\telegram_bot_v2.py"
$trigger = New-ScheduledTaskTrigger -AtStartup
$user = $env:UserName

Register-ScheduledTask -TaskName "GARAM_TG_Bot" -Action $action -Trigger $trigger -User $user -Force
Write-Host " - Registered GARAM_TG_Bot (Startup)"

Write-Host "Done."
