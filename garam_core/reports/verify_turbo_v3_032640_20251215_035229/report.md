# Turbo V3 Verified Result (032640)

## Meta

- Run ID: `verify_turbo_v3_032640_20251215_035229`
- Timestamp (UTC): `2025-12-15T03:52:29Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `032640` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=3009, win_rate=0.00%, pnl=None, mdd=0.00%, equity=921676.4249119424

## Key Points

- Total Return: -99.08%
- Max Drawdown: -99.08%
- Trades: 3009
- Final Equity: 921,676 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1504

- Win Rate: 26.80%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): -0.00010

- **Expectancy (Net)**: **-0.00290**

- Net PnL Total: -4.35823

- SQN Score: -29.73467


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 90 | 0 | 0.00% | **0.00000** |  |
| TREND_DOWN | 99 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 66 | 0 | 0.00% | **0.00000** |  |
| CHOP_LOWVOL | 94270 | 1481 | 26.33% | **-0.00294** |  |
| PANIC | 1349 | 23 | 56.52% | **-0.00038** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00287

- Last 20% Median Exp: -0.00300

- Drop Ratio: -4.52%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
