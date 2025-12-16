# Turbo V3 Verified Result (047810)

## Meta

- Run ID: `verify_turbo_v3_047810_20251215_061534`
- Timestamp (UTC): `2025-12-15T06:15:34Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `047810` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2716, win_rate=0.00%, pnl=None, mdd=0.00%, equity=1621712.1772361677

## Key Points

- Total Return: -98.38%
- Max Drawdown: -98.39%
- Trades: 2716
- Final Equity: 1,621,712 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1358

- Win Rate: 27.39%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00003

- **Expectancy (Net)**: **-0.00277**

- Net PnL Total: -3.76137

- SQN Score: -11.70990


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 209 | 0 | 0.00% | **0.00000** |  |
| TREND_DOWN | 103 | 1 | 100.00% | **0.00310** |  |
| CHOP_HIGHVOL | 2937 | 23 | 52.17% | **-0.00037** |  |
| CHOP_LOWVOL | 91445 | 1304 | 26.46% | **-0.00283** |  |
| PANIC | 1195 | 30 | 46.67% | **-0.00204** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00282

- Last 20% Median Exp: -0.00238

- Drop Ratio: 15.59%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
