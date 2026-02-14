$ErrorActionPreference = "Stop"
Write-Host "Registering Telegram Tasks..." -ForegroundColor Cyan

# 1. Open (08:45)
# Using python directly
$action = New-ScheduledTaskAction -Execute "C:\Python313\python.exe" -Argument "C:\garam\garam\scripts\ops\telegram_ops_report.py open"
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday, Tuesday, Wednesday, Thursday, Friday -At 8:45am
Register-ScheduledTask -TaskName "GARAM_TG_Open" -Action $action -Trigger $trigger -User $env:UserName -Force
Write-Host " - Registered GARAM_TG_Open"

# 2. Noon (12:00)
$action = New-ScheduledTaskAction -Execute "C:\Python313\python.exe" -Argument "C:\garam\garam\scripts\ops\telegram_ops_report.py noon"
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday, Tuesday, Wednesday, Thursday, Friday -At 12:00pm
Register-ScheduledTask -TaskName "GARAM_TG_Noon" -Action $action -Trigger $trigger -User $env:UserName -Force
Write-Host " - Registered GARAM_TG_Noon"

# 3. Close (15:35)
$action = New-ScheduledTaskAction -Execute "C:\Python313\python.exe" -Argument "C:\garam\garam\scripts\ops\telegram_ops_report.py close"
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday, Tuesday, Wednesday, Thursday, Friday -At 3:35pm
Register-ScheduledTask -TaskName "GARAM_TG_Close" -Action $action -Trigger $trigger -User $env:UserName -Force
Write-Host " - Registered GARAM_TG_Close"

# 4. Anomaly (Every 5 mins)
# Trigger every 5 mins heavily relies on RepeatingInterval which is cleaner via schtasks /SC MINUTE manually or intricate PS object
# Using schtasks for this one for simplicity as requested by user pattern
Write-Host " - Registering GARAM_TG_Anomaly via schtasks..."
$cmd = "C:\Python313\python.exe C:\garam\garam\scripts\ops\telegram_ops_report.py anomaly"
schtasks /Create /F /TN "GARAM_TG_Anomaly" /SC MINUTE /MO 5 /ST 00:00 /TR $cmd /RL HIGHEST
# Note: user context might be inferred or we can force it, but usually schtasks defaults to current user.

Write-Host "Done."
