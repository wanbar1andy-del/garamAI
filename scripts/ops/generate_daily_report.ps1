# Phase 9-B Daily Operation Auto Report
# Generates a Markdown report from latest logs.
# Usage (from repo root):
#   powershell -ExecutionPolicy Bypass -File .\scripts\ops\generate_daily_report.ps1

$ErrorActionPreference = "Stop"

function Get-RepoRoot {
    # scripts\ops\generate_daily_report.ps1 -> repo root is ..\.. from script root
    $scriptRoot = $PSScriptRoot
    $root = Resolve-Path (Join-Path $scriptRoot "..\..")
    return $root.Path
}

$repoRoot = Get-RepoRoot
$logDir = Join-Path $repoRoot "results\logs"
$reportDir = Join-Path $repoRoot "results\reports"

if (-not (Test-Path $reportDir)) { New-Item -ItemType Directory -Path $reportDir | Out-Null }

# --- Locate artifacts ---
$hbPath = Join-Path $logDir "engine_heartbeat.csv"
$trace = Get-ChildItem -Path $logDir -Filter "trace_*.csv" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
$trade = Get-ChildItem -Path $logDir -Filter "trade_log_*.csv" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
$crashPath = Join-Path $logDir "crash.log"

# --- Gate P0: Heartbeat ---
$P0 = "NOK"
$hbEvidence = $hbPath
$hbGapStatus = "N/A"
if (Test-Path $hbPath) {
    $hb = Import-Csv $hbPath
    if ($hb.Count -ge 2) {
        # gap check: consecutive ts diffs > 30 sec
        $gap = $false
        for ($i = 1; $i -lt $hb.Count; $i++) {
            $t0 = [datetime]$hb[$i - 1].ts
            $t1 = [datetime]$hb[$i].ts
            if (($t1 - $t0).TotalSeconds -gt 30) { $gap = $true; break }
        }
        $hbGapStatus = if ($gap) { "GAP_DETECTED" } else { "NO_GAP" }
        $P0 = if ($gap) { "NOK" } else { "OK" }
    }
}

# --- Gate P1: Trace ---
$P1 = "NOK"
$traceEvidence = if ($trace) { $trace.FullName } else { "(missing)" }
if ($trace -and (Test-Path $trace.FullName)) {
    $t = Import-Csv $trace.FullName
    if ($t.Count -ge 2) { $P1 = "OK" }
}

# --- Gate P3: Crash ---
$P3 = "NO"
$crashEvidence = $crashPath
if (Test-Path $crashPath) {
    $sz = (Get-Item $crashPath).Length
    if ($sz -gt 0) { $P3 = "YES" }
}

# --- EOD Safety Evidence ---
$eodFound = $false
$eodEvidence = "(not found)"
$logs = Get-ChildItem -Path $logDir -Filter "*.log" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending
foreach ($lg in $logs) {
    $txt = Get-Content $lg.FullName -ErrorAction SilentlyContinue
    if ($txt -match "EOD Force Close Triggered") {
        $eodFound = $true
        $eodEvidence = $lg.FullName
        break
    }
}
# Fallback: if trade log has reason=EOD on EXIT
if (-not $eodFound -and $trade -and (Test-Path $trade.FullName)) {
    $tr0 = Import-Csv $trade.FullName
    if (($tr0 | Where-Object { $_.decision -eq "EXIT" -and $_.reason -eq "EOD" }).Count -gt 0) {
        $eodFound = $true
        $eodEvidence = $trade.FullName
    }
}
$EOD = if ($eodFound) { "YES" } else { "NO" }

# --- Performance Summary ---
$totalRows = 0
$totalExits = 0
$winRate = "N/A"
$pnlSum = 0.0
$guardrail = "None"
$tradeEvidence = if ($trade) { $trade.FullName } else { "(missing)" }

if ($trade -and (Test-Path $trade.FullName)) {
    $tr = Import-Csv $trade.FullName
    $totalRows = $tr.Count

    # EXIT only (realized pnl)
    $exits = $tr | Where-Object { $_.decision -eq "EXIT" }
    $totalExits = $exits.Count

    if ($totalExits -gt 0) {
        $wins = 0
        $pnl = 0.0
        foreach ($row in $exits) {
            $v = 0.0
            [double]::TryParse($row.pnl, [ref]$v) | Out-Null
            $pnl += $v
            if ($v -gt 0) { $wins += 1 }
            if ($row.guardrail_flags -and $row.guardrail_flags.Trim().Length -gt 0) { $guardrail = $row.guardrail_flags }
        }
        $pnlSum = $pnl
        $winRate = [math]::Round(($wins / $totalExits) * 100, 1)
    }
    else {
        # still carry guardrail flags if any
        foreach ($row in $tr) {
            if ($row.guardrail_flags -and $row.guardrail_flags.Trim().Length -gt 0) { $guardrail = $row.guardrail_flags }
        }
    }
}

# --- Zero-Trade Diagnosis (09:20~10:00) ---
$dominantReason = "N/A"
$judgement = "N/A"
$diagDetails = @()
$noMa60Pct = 0.0
$featFailPct = 0.0

# "Trade Count = 0" means no EXITs (round trips)
if ($totalExits -eq 0 -and $trace -and (Test-Path $trace.FullName)) {
    $all = Import-Csv $trace.FullName
    if ($all.Count -gt 0) {
        $dt0 = [datetime]$all[0].ts
        $start = Get-Date ($dt0.ToString("yyyy-MM-dd") + " 09:20:00")
        $end = Get-Date ($dt0.ToString("yyyy-MM-dd") + " 10:00:00")
        $slice = $all | ForEach-Object { $_.ts = [datetime]$_.ts; $_ } | Where-Object { $_.ts -ge $start -and $_.ts -lt $end }

        if ($slice.Count -gt 0) {
            $grp = $slice | Group-Object reason | Sort-Object Count -Descending
            $dominantReason = $grp[0].Name

            $total = [double]$slice.Count
            $noMa60 = ($slice | Where-Object { $_.reason -eq "NO_MA60" }).Count
            $featFail = ($slice | Where-Object { $_.reason -eq "FEAT_FAIL" }).Count
            $noMa60Pct = [math]::Round(($noMa60 / $total) * 100, 2)
            $featFailPct = [math]::Round(($featFail / $total) * 100, 2)

            if ($noMa60Pct -gt 5.0 -or $featFailPct -gt 10.0) {
                $judgement = "Operational Defect (FAIL)"
            }
            else {
                $judgement = "Market Condition (PASS)"
            }

            $diagDetails += "TRACE_SRC   = $($trace.FullName)"
            $diagDetails += "WINDOW      = $start ~ $end"
            $diagDetails += "NO_MA60%    = $noMa60Pct"
            $diagDetails += "FEAT_FAIL%  = $featFailPct"

            # Save slice for audit
            $outSlice = Join-Path $logDir "trace_slice_0920_1000.csv"
            $slice | Export-Csv $outSlice -NoTypeInformation -Encoding UTF8
        }
        else {
            $dominantReason = "(No rows in 09:20~10:00 slice)"
            $judgement = "N/A"
        }
    }
}

# --- Report Date ---
$reportDate = (Get-Date).ToString("yyyy-MM-dd")
$outPath = Join-Path $reportDir ("Daily_Report_{0}.md" -f $reportDate)

# --- Compose Markdown ---
$md = @()
$md += "# Phase 9-B Daily Operation Report"
$md += "Date: $reportDate"
$md += ""
$md += "## 1. Operational Integrity (Gate Check)"
$md += "- P0 (Heartbeat): $P0  | GapCheck: $hbGapStatus  | Evidence: $hbEvidence"
$md += "- P1 (Trace): $P1      | Evidence: $traceEvidence"
$md += "- P3 (Crash): $P3      | Evidence: $crashEvidence"
$md += "- EOD Safety (15:20 Force Close): $EOD | Evidence: $eodEvidence"
$md += ""
$md += "## 2. Performance Summary"
$md += "- Trade Log: $tradeEvidence"
$md += "- Total Rows (ENTRY+EXIT): $totalRows"
$md += "- Total Exits (RoundTrips): $totalExits"
$md += "- Win Rate (EXIT only): $winRate%"
$md += ("- PnL (Sum, EXIT only): {0:N0} KRW" -f $pnlSum)
$md += "- Guardrails: $guardrail"
$md += ""
$md += "## 3. Zero-Trade Diagnosis (If Trades = 0)"
$md += "- Dominant Reason (09:20~10:00): $dominantReason"
$md += "- Judgement: $judgement"
if ($diagDetails.Count -gt 0) {
    $md += ""
    $md += "### Diagnostic Details"
    $md += $diagDetails
}
$md += ""
$md += "## 4. Operator Notes (Max 3 Lines)"
$md += "- "
$md += "- "
$md += "- "

$mdText = ($md -join "`r`n")
[System.IO.File]::WriteAllText($outPath, $mdText, [System.Text.Encoding]::UTF8)

Write-Host "OK: Report generated -> $outPath"
