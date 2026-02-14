param(
    [string]$Root = "C:\garam\garam",
    [string]$Feed = "C:\garam\garam\feed_live.jsonl",
    [string]$Ingester = "C:\garam\garam\scripts\ops\ingest_kiwoom_realtime.py",
    [string]$PythonPath = "", 
    [int]$TailSeconds = 60
)

Set-Location $Root

Write-Host "=== Phase 30-3 Ingester Verification ==="
Write-Host "Root: $Root"

# 1) Locate Python
if ([string]::IsNullOrWhiteSpace($PythonPath)) {
    # Default look for .venv32/Scripts/python.exe
    $venv32 = Join-Path $Root ".venv32\Scripts\python.exe"
    if (Test-Path $venv32) {
        $PythonPath = $venv32
    }
    else {
        $PythonPath = (Get-Command python).Source
    }
}
Write-Host "Using Python: $PythonPath"

# 2) Check Architecture (MUST be 32-bit for Kiwoom)
$archCheck = & $PythonPath -c "import platform; print(platform.architecture()[0])"
Write-Host "Python Arch: $archCheck"

if ($archCheck -ne "32bit") {
    Write-Warning "CRITICAL: Kiwoom OpenAPI requires 32-bit Python."
    Write-Warning "Current Python is $archCheck."
    Write-Warning "Please install 32-bit Python (e.g. 3.9-32) and create a venv:"
    Write-Warning "  py -3.9-32 -m venv .venv32"
    Write-Warning "  .\.venv32\Scripts\pip install pyqt5 pywin32"
    Write-Warning "Then re-run this script."
    throw "Architecture Mismatch"
}

# 3) precheck
if (!(Test-Path $Ingester)) { throw "Ingester script missing: $Ingester" }

# Ensure feed exists (append-only)
if (!(Test-Path $Feed)) {
    New-Item -ItemType File -Path $Feed | Out-Null
}

# 2) start ingester (new window to allow Kiwoom UI interaction)
Write-Host "`n[1] Starting Ingester..."
$py = (Get-Command python).Source
# Use Start-Process to spawn independent process
$proc = Start-Process -FilePath $py -ArgumentList $Ingester -WorkingDirectory $Root -PassThru
Write-Host "Ingester PID: $($proc.Id)"
Write-Host "NOTE: Please interact with the Kiwoom Login Window if it appears!"

# 3) tail feed for a short period to confirm writes
Write-Host "`n[2] Tailing feed for $TailSeconds seconds..."
$end = (Get-Date).AddSeconds($TailSeconds)
$lastSize = (Get-Item $Feed).Length

while ((Get-Date) -lt $end) {
    Start-Sleep -Milliseconds 1000
    $size = (Get-Item $Feed).Length
    if ($size -gt $lastSize) {
        Write-Host "Feed grew: $lastSize -> $size bytes"
        $lastSize = $size
    }
}

# 4) validate last N lines are valid JSON
Write-Host "`n[3] Validating JSONL integrity (last 50 lines)..."
$lines = Get-Content $Feed -Tail 50
$ok = 0; $bad = 0
foreach ($l in $lines) {
    if ([string]::IsNullOrWhiteSpace($l)) { continue }
    try { $null = $l | ConvertFrom-Json; $ok++ } catch { $bad++ }
}
Write-Host "JSON parse OK=$ok BAD=$bad"
if ($bad -gt 0) { Write-Warning "JSONL has parse errors (partial lines or corruption)." }

# 3.5) Print last 3 lines for report convenience
Write-Host "`n[4] Last 3 Lines (feed tail):"
try {
    $tail3 = Get-Content $Feed -Tail 3 -ErrorAction Stop
    if ($tail3) {
        $tail3 | ForEach-Object { Write-Host $_ }
    }
    else {
        Write-Host "(feed is empty)"
    }
}
catch {
    Write-Warning "Failed to read last 3 lines: $($_.Exception.Message)"
}

Write-Host "`n[5] Stopping Ingester..."
Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
Write-Host "Done."
