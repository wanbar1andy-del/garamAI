$ErrorActionPreference = "Stop"
Write-Host "Registering Scheduled Tasks..."

# Login Task (08:45)
$loginAction = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File C:\garam\garam\scripts\ops\auto_login.ps1"
$loginTrigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday, Tuesday, Wednesday, Thursday, Friday -At 8:45am
Register-ScheduledTask -TaskName "GARAM_AutoLogin" -Action $loginAction -Trigger $loginTrigger -User $env:UserName -Force
Write-Host " - Registered GARAM_AutoLogin"

# Logout Task (15:35)
$logoutAction = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File C:\garam\garam\scripts\ops\auto_logout.ps1"
$logoutTrigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday, Tuesday, Wednesday, Thursday, Friday -At 3:35pm
Register-ScheduledTask -TaskName "GARAM_AutoLogout" -Action $logoutAction -Trigger $logoutTrigger -User $env:UserName -Force
Write-Host " - Registered GARAM_AutoLogout"

Write-Host "Done."
