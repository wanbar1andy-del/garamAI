$Action = New-ScheduledTaskAction -Execute "python.exe" -Argument "c:\garam\garam\scripts\run_today_simulation.py" -WorkingDirectory "c:\garam\garam"
$Trigger = New-ScheduledTaskTrigger -Daily -At 3:45PM
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
$TaskName = "GARAM_Daily_Simulation"
$Description = "Runs the daily simulation for GARAM dashboard at 15:45 KST"

Register-ScheduledTask -Action $Action -Trigger $Trigger -Settings $Settings -TaskName $TaskName -Description $Description -Force

Write-Host "Task '$TaskName' registered successfully."
