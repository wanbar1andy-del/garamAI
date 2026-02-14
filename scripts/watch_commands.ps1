
# scripts/watch_commands.ps1
$WatchDir = "C:\garam\garam\commands"
$ProcessedDir = "C:\garam\garam\commands\processed"
$LogFile = "C:\garam\garam\commands\execution.log"

Write-Host "Monitoring $WatchDir for commands..."

while ($true) {
    $Files = Get-ChildItem -Path $WatchDir -Filter "*.txt"
    
    foreach ($File in $Files) {
        $Content = Get-Content -Path $File.FullName -Raw
        $TimeStamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        
        Write-Host "[$TimeStamp] Executing $($File.Name)..."
        Add-Content -Path $LogFile -Value "[$TimeStamp] EXECUTING $($File.Name): $Content"
        
        try {
            # Execute content as PS command
            Invoke-Expression $Content
            Add-Content -Path $LogFile -Value "[$TimeStamp] SUCCESS"
        }
        catch {
            $ErrMsg = $_.Exception.Message
            Write-Host "Error: $ErrMsg" -ForegroundColor Red
            Add-Content -Path $LogFile -Value "[$TimeStamp] ERROR: $ErrMsg"
        }
        
        # Move to processed
        Move-Item -Path $File.FullName -Destination $ProcessedDir -Force
    }
    
    Start-Sleep -Seconds 2
}
