# Turbo V3 Verified Result (006040)

## Meta

- Run ID: `verify_turbo_v3_006040_20251215_064837`
- Timestamp (UTC): `2025-12-15T06:48:37Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `006040` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2834, win_rate=0.00%, pnl=None, mdd=0.00%, equity=1106734.4787456316

## Key Points

- Total Return: -98.89%
- Max Drawdown: -98.91%
- Trades: 2834
- Final Equity: 1,106,734 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1417

- Win Rate: 30.35%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): -0.00004

- **Expectancy (Net)**: **-0.00284**

- Net PnL Total: -4.02488

- SQN Score: -17.73918


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **NEGATIVE_EDGE**
- **REGIME_MISMATCH**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 49 | 2 | 100.00% | **0.00981** |  |
| TREND_DOWN | 67 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 2770 | 42 | 30.95% | **-0.00452** |  |
| CHOP_LOWVOL | 82809 | 1340 | 30.37% | **-0.00277** |  |
| PANIC | 1517 | 33 | 24.24% | **-0.00419** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00274

- Last 20% Median Exp: -0.00314

- Drop Ratio: -14.36%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
