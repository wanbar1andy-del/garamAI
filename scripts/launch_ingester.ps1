
# Launch Ingester (Manual)
# Run this to start the Kiwoom Interface

Write-Host "Starting Garam Ingester..." -ForegroundColor Green
Set-Location "C:\garam\garam"

# Kill existing python instances to clean up
taskkill /F /IM python.exe 2>$null

# Run Ingester with 32-bit Python in same window to see errors
& "C:\Python39-32\python.exe" "pipeline/ingest/run_ingest_kiwoom.py"

if ($LASTEXITCODE -ne 0) {
    Write-Host "Ingester crashed with exit code $LASTEXITCODE" -ForegroundColor Red
    pause
}
