
# scripts/monitor_garam.ps1
$ScriptPath = "scripts/auto_pilot.py"
$FullScriptPath = "C:\garam\garam\scripts\auto_pilot.py"
$WorkDir = "C:\garam\garam"
$LogPath = "C:\garam\garam\logs\system_guardian.log"
$CheckIntervalSeconds = 60

function Log-Message {
    param ([string]$Msg)
    $TimeStamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $LogMsg = "[$TimeStamp] $Msg"
    Write-Host $LogMsg
    Add-Content -Path $LogPath -Value $LogMsg
}

Log-Message "Garam System Guardian Started (v2)."
Log-Message "Target: $FullScriptPath"

while ($true) {
    # Monitor Auto-Pilot (The Master Process)
    $AutoPilotProcess = Get-WmiObject Win32_Process | Where-Object { $_.CommandLine -like "*$ScriptPath*" }
    
    if (-not $AutoPilotProcess) {
        Log-Message "WARNING: Auto-Pilot is NOT running. Restarting..."
        try {
            Start-Process python -ArgumentList "$ScriptPath" -WorkingDirectory $WorkDir -WindowStyle Normal
            Log-Message "Restart Command Sent (Auto-Pilot)."
        }
        catch {
            Log-Message "ERROR: Failed to restart Auto-Pilot: $_"
        }
    } else {
        # Optional: Log heartbeat every hour or just keep silent to reduce noise
        # Log-Message "Auto-Pilot is running."
    }
    
    Start-Sleep -Seconds $CheckIntervalSeconds
}
