# Turbo V3 Verified Result (096770)

## Meta

- Run ID: `verify_turbo_v3_096770_20251215_043633`
- Timestamp (UTC): `2025-12-15T04:36:33Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `096770` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2471, win_rate=0.00%, pnl=None, mdd=0.00%, equity=1787189.2102099243

## Key Points

- Total Return: -98.21%
- Max Drawdown: -98.23%
- Trades: 2471
- Final Equity: 1,787,189 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1235

- Win Rate: 26.88%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): -0.00012

- **Expectancy (Net)**: **-0.00292**

- Net PnL Total: -3.60695

- SQN Score: -15.50967


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 441 | 4 | 25.00% | **-0.00426** |  |
| TREND_DOWN | 173 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 683 | 3 | 33.33% | **0.00511** |  |
| CHOP_LOWVOL | 93335 | 1207 | 26.93% | **-0.00288** |  |
| PANIC | 1257 | 21 | 23.81% | **-0.00615** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00310

- Last 20% Median Exp: -0.00236

- Drop Ratio: 23.91%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
