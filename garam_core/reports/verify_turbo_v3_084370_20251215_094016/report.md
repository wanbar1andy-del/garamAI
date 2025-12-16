# Turbo V3 Verified Result (084370)

## Meta

- Run ID: `verify_turbo_v3_084370_20251215_094016`
- Timestamp (UTC): `2025-12-15T09:40:16Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `084370` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2670, win_rate=0.00%, pnl=None, mdd=0.00%, equity=2770967.9446246712

## Key Points

- Total Return: -97.23%
- Max Drawdown: -97.38%
- Trades: 2670
- Final Equity: 2,770,968 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1335

- Win Rate: 29.51%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00039

- **Expectancy (Net)**: **-0.00241**

- Net PnL Total: -3.21593

- SQN Score: -8.71374


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 227 | 1 | 0.00% | **-0.01757** |  |
| TREND_DOWN | 107 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 7339 | 73 | 34.25% | **-0.00115** |  |
| CHOP_LOWVOL | 86478 | 1242 | 29.23% | **-0.00250** |  |
| PANIC | 1205 | 19 | 31.58% | **-0.00076** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00244

- Last 20% Median Exp: -0.00191

- Drop Ratio: 21.81%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
