# Register GARAM Daily Routine Task
# Runs daily at 15:45 (Market Close + 15m)

$TaskName = "GARAM_Daily_Routine"
$ScriptPath = "c:\garam\garam\scripts\daily_routine.py"
$PythonPath = "python" # Assumes python is in PATH. Ideally use absolute path to 32-bit python.
$WorkDir = "c:\garam\garam"

$Action = New-ScheduledTaskAction -Execute $PythonPath -Argument $ScriptPath -WorkingDirectory $WorkDir
$Trigger = New-ScheduledTaskTrigger -Daily -At 16:00
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

# Unregister if exists
Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue

# Register
Register-ScheduledTask -Action $Action -Trigger $Trigger -Settings $Settings -TaskName $TaskName -Description "Runs GARAM Daily Routine (Data Fetch + Trading Engine)"

Write-Host "✅ Task '$TaskName' registered successfully!"
Write-Host "   - Schedule: Daily at 16:00"
Write-Host "   - Command: $PythonPath $ScriptPath"
