# Phase 9-B Daily Operation Report

Date: YYYY-MM-DD  
Operator: [Your Name]  
Status: [PASS / FAIL]

---

## 1. Operational Integrity (Gate Check)

| Gate | Metric | Status | Evidence Location |
|---|---|---|---|
| P0: Ingestion | Heartbeat | [OK/NOK] | results/logs/engine_heartbeat.csv |
| P1: Trace | Log Generation | [OK/NOK] | results/logs/trace_*.csv |
| P3: Stability | Crash Detected | [YES/NO] | results/logs/crash.log (Size=0) |
| EOD Safety | Force Close | [YES/NO] | Log: [WARNING] EOD Force Close |

---

## 2. Performance Summary

- Total Trades: [N] (Entry + Exit)
- Win Rate: [%] (Wins / Total)
- PnL: [Amount] (KRW)
- Guardrails: [None / DailyLoss / Strike]

---

## 3. Zero-Trade Diagnosis (If Trades = 0)

Run PowerShell Trace Slice (09:20~10:00)

- Dominant Reason: [ROC_FAIL / VOL_FAIL / TREND_FAIL / NO_MA60 / FEAT_FAIL]
- Judgment: [Market Condition (PASS) / Operational Defect (FAIL)]

---

## 4. Operator Notes (Max 3 Lines)

1)  
2)  
3)  
