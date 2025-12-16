# Turbo V3 Verified Result (300720)

## Meta

- Run ID: `verify_turbo_v3_300720_20251215_100508`
- Timestamp (UTC): `2025-12-15T10:05:08Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `300720` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2521, win_rate=0.00%, pnl=None, mdd=0.00%, equity=1722259.1608232465

## Key Points

- Total Return: -98.28%
- Max Drawdown: -98.38%
- Trades: 2521
- Final Equity: 1,722,259 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1260

- Win Rate: 29.13%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): -0.00015

- **Expectancy (Net)**: **-0.00295**

- Net PnL Total: -3.71936

- SQN Score: -18.26570


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 263 | 3 | 0.00% | **-0.01940** |  |
| TREND_DOWN | 245 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 369 | 7 | 14.29% | **-0.00627** |  |
| CHOP_LOWVOL | 90871 | 1223 | 29.27% | **-0.00287** |  |
| PANIC | 1879 | 27 | 29.63% | **-0.00405** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00309

- Last 20% Median Exp: -0.00325

- Drop Ratio: -5.14%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
