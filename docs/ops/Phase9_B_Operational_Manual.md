# Phase 9-B Operational Manual (Paper Trading)

Objective: Verify **Operational Integrity** & **End-to-End Execution (Entry->Exit)** in Real-time Environment.  
Success Criteria (Week 1): **Zero Crashes, Zero Heartbeat Gaps, 100% EOD Execution.**

---

## 1. Daily Runbook (Strict Sequence)

Must follow this order to ensure log integrity.

### A. Pre-flight Cleanup (Before 08:50)

**Terminate Stale Engines:** Ensure no python.exe running the engine (Task Manager or taskkill).

**Clean Logs & Data:**

- `Remove-Item results/logs/* -Force`
- `Remove-Item GARAM_Data/realtime/* -Force`
- (Optional: Archive old logs if needed)

### B. Launch Sequence (08:50 ~ 08:55)

**Prepare Market Status (MA60):**

- Run Feeder briefly or use a dedicated script to generate `GARAM_Data/market_status.csv`
- Check: `ma60` column must not be empty.

**Start Feeder (Atomic Mode):**

- `python scripts/live/run_preflight_feeder.py`  # Or specific Kiwoom Feeder

**Start Engine (Engine V13):**

- `python -m scripts.live.run_live_policy_v2_phase7`
- Check Console: Confirm `[INFO] Loaded MA60 for N symbols (N > 300).`

### C. Health Check (First 60 Seconds)

**Heartbeat:** `results/logs/engine_heartbeat.csv`

- Must see new lines every 10 seconds.
- `lines_processed` must be increasing.

**Crash Log:** `results/logs/crash.log`

- Must be 0 bytes or non-existent.

**Trace Log:** `results/logs/trace_*.csv`

- Must be generated.

---

## 2. Zero-Trade Diagnosis Rule (Quantitative)

If Trade Count = 0, verify the cause using Trace Logs.

| Symptom (Trace Reason) | Diagnosis | Operational Status | Action |
|---|---|---|---|
| NO_MA60 (Dominant) | CRITICAL FAILURE | FAIL | Engine started before Market Status. Restart properly. |
| FEAT_FAIL (Dominant) | Ingestion Lag / Data Gap | FAIL | Check Feeder quality or Tolerance logic. |
| ROC_FAIL / VOL_FAIL | Market Condition | PASS | Strategy is working, just no opportunities. |
| TREND_FAIL | Bear Market | PASS | MA60 Filter is working. |
| COOLDOWN | Post-trade throttling | PASS | Normal behavior after trades. |

**Quantitative Fail Criteria (Hard Rules):**

- **NO_MA60 > 5%** in 09:20~10:00 slice ⇒ **FAIL** (Startup order / MarketStatus defect)
- **FEAT_FAIL > 10%** in 09:20~10:00 slice ⇒ **FAIL** (Feed quality / gap / tolerance issue)

---

## 3. End-of-Day Checklist (15:30)

### EOD Execution

- Log Evidence: `[WARNING] EOD Force Close Triggered` exists in console/log?
- Data Evidence: `trade_log_*.csv` shows flat positions (Qty:0) or EOD Sell recorded

### Metric Integrity (P0 Gate)

- Evidence: `engine_heartbeat.csv` `lines_processed` increased steadily
- Gap Check: No gaps > 30s

### Clean Shutdown

- Crash Evidence: `results/logs/crash.log` MUST be 0 bytes

---

## 4. Emergency Procedures

- **Crash Detected:** Immediate Stop → Copy `crash.log` → Report.
- **Heartbeat Flatline:** Feeder stuck? → Restart Feeder ONLY (Engine might recover).

---

## 5. Trace Slice Diagnosis (PowerShell, Date Auto-Detect)

Purpose: Diagnose "Zero Trade" days instantly.

```powershell
# 1. Extract Trace Slice (09:20~10:00) - Date Auto-Detect
$trace = Get-ChildItem results/logs/trace_*.csv | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $trace) { throw "No trace_*.csv found in results/logs" }

# Extract Date from First Line
$first = Import-Csv $trace.FullName | Select-Object -First 1
if (-not $first) { throw "Trace file exists but is empty" }

$dt0 = [datetime]$first.ts
$start = Get-Date ($dt0.ToString("yyyy-MM-dd") + " 09:20:00")
$end   = Get-Date ($dt0.ToString("yyyy-MM-dd") + " 10:00:00")

$out = "results/logs/trace_slice_0920_1000.csv"
Import-Csv $trace.FullName | ForEach-Object { $_.ts = [datetime]$_.ts; $_ } |
  Where-Object { $_.ts -ge $start -and $_.ts -lt $end } |
  Export-Csv $out -NoTypeInformation -Encoding UTF8

"TRACE_SRC = $($trace.FullName)"
"WINDOW    = $start ~ $end"

# 2. View Reason Distribution (Top 15)
Import-Csv $out | Group-Object reason | Sort-Object Count -Descending | Select-Object -First 15 | Format-Table Count, Name -AutoSize
```

**Judgement Criteria:**

PASS: ROC_FAIL, VOL_FAIL, TREND_FAIL, COOLDOWN (Dominant)

FAIL:

NO_MA60 > 5% (Check Market Status / Startup Order)

FEAT_FAIL > 10% (Check Feeder Quality)

## 6. Auto Report (One-Click Ops)

After market close (e.g., 15:35), run:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\ops\generate_daily_report.ps1
```

Output:

`results/reports/Daily_Report_YYYY-MM-DD.md`

This report includes:

P0/P1/P3/EOD gate status

Performance summary (trades, win rate, PnL, guardrails)

Zero-trade diagnosis (only when trades=0)

### 6.1 Chart Generation (Mandatory)

Run this immediately after the daily report:

```powershell
python .\scripts\ops\generate_ops_charts.py
```

Output: `results/reports/plots/*.png` (Equity, Drawdown, TradePnL)
