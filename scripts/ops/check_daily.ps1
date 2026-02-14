# scripts/ops/check_daily.ps1
# Phase 10 Daily Monitoring Helper (v3.2 Operational Hardening)
# Goal: 4-Axis Monitoring (Liveness / ERROR / NO_FILL / DataFlow + Feed Freshness)
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File scripts/ops/check_daily.ps1
#   powershell -ExecutionPolicy Bypass -File scripts/ops/check_daily.ps1 -Full
#   powershell -ExecutionPolicy Bypass -File scripts/ops/check_daily.ps1 -StaleMinutes 5 -Tail 20
#   powershell -ExecutionPolicy Bypass -File scripts/ops/check_daily.ps1 -FeedStaleMinutes 2
#   powershell -ExecutionPolicy Bypass -File scripts/ops/check_daily.ps1 -FeedPath C:\garam\garam\feed_live.jsonl

param(
    [string]$LogDir = "C:\garam\garam\logs\shadow",
    [int]$StaleMinutes = 3,           # 엔진 로그 갱신이 이 분 이상 없으면 FAIL (Liveness)
    [int]$Tail = 5,                   # 마지막 N줄 출력
    [switch]$Full,                    # 전체 파일 스캔 (큰 파일이면 느림)
    [string]$FeedPath = "",           # feed_live.jsonl 경로(비우면 LogDir 기반으로 자동 추정)
    [int]$FeedStaleMinutes = 2,       # 장중 feed 파일 갱신이 이 분 이상 없으면 WARN (Feed Stale)
    [int]$NoFillWarnThreshold = 0     # NO_FILL count > X 이면 WARN (기본 0 = 하나라도 있으면 WARN)
)

Set-StrictMode -Version Latest
Write-Host "[OPS] check_daily.ps1 loaded (v3.2)" -ForegroundColor DarkGray
$ErrorActionPreference = "Stop"

function Write-Section([string]$title) {
    Write-Host ""
    Write-Host "=== $title ===" -ForegroundColor Cyan
}

function Get-ProjectRootFromLogDir([string]$logDir) {
    # logDir = C:\garam\garam\logs\shadow  -> projectRoot = C:\garam\garam
    $p1 = Split-Path -Path $logDir -Parent  # ...\logs
    $p2 = Split-Path -Path $p1 -Parent      # ...\garam
    return $p2
}

function Get-MarketHoursInfo {
    $now = Get-Date
    $open = $now.Date.AddHours(9)
    $close = $now.Date.AddHours(15).AddMinutes(30)
    $isMarketHours = ($now -ge $open) -and ($now -le $close)
    return @{
        Now           = $now
        MarketOpen    = $open
        MarketClose   = $close
        IsMarketHours = $isMarketHours
    }
}

# 0) Basic validation
if (-not (Test-Path $LogDir)) {
    Write-Host "[ERROR] LogDir not found: $LogDir" -ForegroundColor Red
    exit 2
}

# 1) Latest engine log discovery
$LatestLog = Get-ChildItem -Path $LogDir -Filter "*.engine.jsonl" -File |
Sort-Object LastWriteTime -Descending |
Select-Object -First 1

if (-not $LatestLog) {
    Write-Host "[ERROR] No engine logs found in $LogDir" -ForegroundColor Red
    exit 2
}

Write-Host "=== Daily Monitor Report ===" -ForegroundColor Cyan
Write-Host "Target Log   : $($LatestLog.Name)" -ForegroundColor Gray
Write-Host "Last Modified: $($LatestLog.LastWriteTime)" -ForegroundColor Gray

$exitCode = 0
$warnReasons = @()

# 2) Liveness (engine log freshness)
$age = (Get-Date) - $LatestLog.LastWriteTime
if ($age.TotalMinutes -gt $StaleMinutes) {
    Write-Host "[FAIL] Liveness: engine log not updated for $([math]::Round($age.TotalMinutes,2)) minutes (threshold=$StaleMinutes)" -ForegroundColor Red
    $exitCode = 2
}
else {
    Write-Host "[PASS] Liveness: updated $([math]::Round($age.TotalSeconds,0)) seconds ago" -ForegroundColor Green
}

# 3) Determine scan range
$scanLines = $null
if (-not $Full) {
    $scanLines = Get-Content -Path $LatestLog.FullName -Tail 20000
}

# 4) ERROR Check
Write-Section "ERROR Check"
$Errors = $null
if ($Full) {
    $Errors = Select-String -Path $LatestLog.FullName -Pattern '"event"\s*:\s*"ERROR"'
}
else {
    $Errors = $scanLines | Select-String -Pattern '"event"\s*:\s*"ERROR"'
}

if ($Errors -and $Errors.Count -gt 0) {
    Write-Host "[FAIL] Found $($Errors.Count) ERROR events!" -ForegroundColor Red
    $Errors | Select-Object -Last 10 | ForEach-Object { Write-Host $_.Line.Trim() -ForegroundColor DarkRed }
    $exitCode = 2
}
else {
    Write-Host "[PASS] No ERROR events found." -ForegroundColor Green
}

# 5) NO_FILL Check (threshold-based)
Write-Section "NO_FILL Check"
$NoFills = $null
if ($Full) {
    $NoFills = Select-String -Path $LatestLog.FullName -Pattern '"broker_order_id"\s*:\s*"NO_FILL"'
}
else {
    $NoFills = $scanLines | Select-String -Pattern '"broker_order_id"\s*:\s*"NO_FILL"'
}

$noFillCount = 0
if ($NoFills) { $noFillCount = $NoFills.Count }

if ($noFillCount -gt $NoFillWarnThreshold) {
    Write-Host "[WARN] Found $noFillCount NO_FILL events (threshold=$NoFillWarnThreshold)." -ForegroundColor Yellow
    $NoFills | Select-Object -Last 10 | ForEach-Object { Write-Host $_.Line.Trim() -ForegroundColor DarkYellow }
    if ($exitCode -lt 1) { $exitCode = 1 }
    $warnReasons += "NO_FILL"
}
else {
    Write-Host "[PASS] NO_FILL count = $noFillCount (threshold=$NoFillWarnThreshold)." -ForegroundColor Green
}

# 6) Latest HEARTBEAT Summary (Operational)
Write-Section "Latest HEARTBEAT Summary (Operational)"

$hbMatch = $null
if ($Full) {
    $hbMatch = Select-String -Path $LatestLog.FullName -Pattern '"event"\s*:\s*"HEARTBEAT"' | Select-Object -Last 1
}
else {
    $tailLines = $scanLines
    if (-not $tailLines) { $tailLines = Get-Content -Path $LatestLog.FullName -Tail 5000 }
    $hbMatch = $tailLines | Select-String -Pattern '"event"\s*:\s*"HEARTBEAT"' | Select-Object -Last 1
}

if ($hbMatch) {
    try {
        $hb = $hbMatch.Line | ConvertFrom-Json
        Write-Host ("ts_kst      : {0}" -f $hb.ts_kst) -ForegroundColor Gray
        Write-Host ("equity      : {0}" -f $hb.equity) -ForegroundColor Gray
        Write-Host ("dd          : {0}" -f $hb.dd) -ForegroundColor Gray
        if ($hb.PSObject.Properties.Match("regime_state").Count) { Write-Host ("regime_state: {0}" -f $hb.regime_state) -ForegroundColor Gray }
        if ($hb.PSObject.Properties.Match("active_pos").Count) { Write-Host ("active_pos  : {0}" -f $hb.active_pos) -ForegroundColor Gray }
        if ($hb.PSObject.Properties.Match("rx_total").Count) { Write-Host ("rx_total    : {0} | norm_ok: {1} | norm_fail: {2}" -f $hb.rx_total, $hb.norm_ok, $hb.norm_fail) -ForegroundColor Gray }
    }
    catch {
        Write-Host "[WARN] Failed to parse latest HEARTBEAT JSON. Showing raw line:" -ForegroundColor Yellow
        Write-Host $hbMatch.Line.Trim()
        if ($exitCode -lt 1) { $exitCode = 1 }
        $warnReasons += "HEARTBEAT_PARSE_FAIL"
    }
}
else {
    Write-Host "[WARN] No HEARTBEAT found in scan range." -ForegroundColor Yellow
    if ($exitCode -lt 1) { $exitCode = 1 }
    $warnReasons += "NO_HEARTBEAT"
}

# 7) Feed Freshness Check (Ingester)
Write-Section "Feed Freshness Check (Ingester)"

$projRoot = Get-ProjectRootFromLogDir -logDir $LogDir
if ([string]::IsNullOrWhiteSpace($FeedPath)) {
    $FeedPath = Join-Path $projRoot "feed_live.jsonl"
}
Write-Host ("FeedPath     : {0}" -f $FeedPath) -ForegroundColor Gray

$mh = Get-MarketHoursInfo
Write-Host ("Now          : {0}" -f $mh.Now) -ForegroundColor Gray
Write-Host ("MarketHours  : {0} ~ {1} | IsMarketHours={2}" -f $mh.MarketOpen, $mh.MarketClose, $mh.IsMarketHours) -ForegroundColor Gray

if (-not (Test-Path $FeedPath)) {
    Write-Host "[WARN] Feed file not found. (Ingester may not be writing.)" -ForegroundColor Yellow
    if ($exitCode -lt 1) { $exitCode = 1 }
    $warnReasons += "FEED_MISSING"
}
else {
    $feedItem = Get-Item -Path $FeedPath
    $feedAge = (Get-Date) - $feedItem.LastWriteTime
    Write-Host ("FeedLastWrite: {0} | AgeSec={1}" -f $feedItem.LastWriteTime, [math]::Round($feedAge.TotalSeconds, 0)) -ForegroundColor Gray

    if ($mh.IsMarketHours -and ($feedAge.TotalMinutes -gt $FeedStaleMinutes)) {
        Write-Host "[WARN] DATA_STALL (Feed Stale): feed not updated for $([math]::Round($feedAge.TotalMinutes,2)) minutes (threshold=$FeedStaleMinutes)" -ForegroundColor Yellow
        if ($exitCode -lt 1) { $exitCode = 1 }
        $warnReasons += "DATA_STALL_FEED"
    }
    else {
        Write-Host "[PASS] Feed freshness OK (or off-market)." -ForegroundColor Green
    }
}

# 8) Data Flow Check (rx_total + norm_ok deltas)
Write-Section "Data Flow Check (Engine Counters)"

$hbRaw = $null
if ($Full) {
    $hbRaw = Select-String -Path $LatestLog.FullName -Pattern '"event"\s*:\s*"HEARTBEAT"' | Select-Object -Last 2
}
else {
    $tailLines2 = $scanLines
    if (-not $tailLines2) { $tailLines2 = Get-Content -Path $LatestLog.FullName -Tail 5000 }
    $hbRaw = $tailLines2 | Select-String -Pattern '"event"\s*:\s*"HEARTBEAT"' | Select-Object -Last 2
}

$hbRaw = @($hbRaw)

if ($hbRaw -and $hbRaw.Count -eq 2) {
    try {
        $h1 = $hbRaw[0].Line | ConvertFrom-Json
        $h2 = $hbRaw[1].Line | ConvertFrom-Json

        $hasRx1 = $h1.PSObject.Properties.Match("rx_total").Count -gt 0
        $hasRx2 = $h2.PSObject.Properties.Match("rx_total").Count -gt 0
        $hasN1 = $h1.PSObject.Properties.Match("norm_ok").Count -gt 0
        $hasN2 = $h2.PSObject.Properties.Match("norm_ok").Count -gt 0

        if ($hasRx1 -and $hasRx2) {
            $deltaRx = [long]$h2.rx_total - [long]$h1.rx_total
            Write-Host ("HB Delta rx_total : +{0}" -f $deltaRx) -ForegroundColor Gray
        }
        else {
            $deltaRx = $null
            Write-Host "[INFO] rx_total missing in heartbeat(s). Skipping rx_total delta." -ForegroundColor DarkGray
        }

        if ($hasN1 -and $hasN2) {
            $deltaNormOk = [long]$h2.norm_ok - [long]$h1.norm_ok
            Write-Host ("HB Delta norm_ok  : +{0}" -f $deltaNormOk) -ForegroundColor Gray
        }
        else {
            $deltaNormOk = $null
            Write-Host "[INFO] norm_ok missing in heartbeat(s). Skipping norm_ok delta." -ForegroundColor DarkGray
        }

        # Decision logic
        if ($mh.IsMarketHours) {
            if ($deltaRx -ne $null -and $deltaRx -eq 0) {
                Write-Host "[WARN] DATA_STALL (rx_total Δ = 0) during Market Hours" -ForegroundColor Yellow
                if ($exitCode -lt 1) { $exitCode = 1 }
                $warnReasons += "DATA_STALL_RX"
            }
            elseif ($deltaRx -ne $null -and $deltaRx -gt 0 -and $deltaNormOk -ne $null -and $deltaNormOk -eq 0) {
                Write-Host "[WARN] TICK_SILENCE_OR_NORMALIZE_FAIL (rx_total Δ > 0 AND norm_ok Δ = 0) during Market Hours" -ForegroundColor Yellow
                if ($exitCode -lt 1) { $exitCode = 1 }
                $warnReasons += "TICK_SILENCE"
            }
            elseif ($deltaRx -ne $null -and $deltaRx -gt 0) {
                Write-Host "[PASS] Data is flowing (rx_total increasing)." -ForegroundColor Green
            }
            else {
                Write-Host "[INFO] Not enough counter signals for definitive flow 판단." -ForegroundColor DarkGray
            }
        }
        else {
            # Off-market: 흐름이 없어도 INFO 처리
            if ($deltaRx -ne $null -and $deltaRx -gt 0) {
                Write-Host "[INFO] Off-market but rx_total increased (acceptable: post-market/CONTROL/HEARTBEAT)." -ForegroundColor DarkGray
            }
            else {
                Write-Host "[INFO] Off-market: no flow increase (acceptable)." -ForegroundColor DarkGray
            }
        }
    }
    catch {
        Write-Host "[INFO] Skipped Data Flow Check (Parse fail)" -ForegroundColor DarkGray
    }
}
else {
    Write-Host "[INFO] Not enough heartbeats for Delta check (Need 2)." -ForegroundColor DarkGray
}

# 9) Tail output
Write-Section "Latest $Tail Log Entries"
Get-Content -Path $LatestLog.FullName -Tail $Tail

# 10) Final summary
Write-Section "Monitoring Complete"
if ($exitCode -eq 0) {
    Write-Host "[PASS] System looks healthy." -ForegroundColor Green
}
elseif ($exitCode -eq 1) {
    $reasons = ($warnReasons | Select-Object -Unique) -join ', '
    Write-Host "[WARN] System needs attention (non-fatal). Reasons: $reasons" -ForegroundColor Yellow
}
else {
    Write-Host "[FAIL] System unhealthy. Investigate immediately." -ForegroundColor Red
}

exit $exitCode
