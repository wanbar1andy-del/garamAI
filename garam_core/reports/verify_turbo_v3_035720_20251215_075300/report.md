# Turbo V3 Verified Result (035720)

## Meta

- Run ID: `verify_turbo_v3_035720_20251215_075300`
- Timestamp (UTC): `2025-12-15T07:53:00Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `035720` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2744, win_rate=0.00%, pnl=None, mdd=0.00%, equity=1759118.9565772337

## Key Points

- Total Return: -98.24%
- Max Drawdown: -98.29%
- Trades: 2744
- Final Equity: 1,759,119 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1372

- Win Rate: 27.11%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00007

- **Expectancy (Net)**: **-0.00273**

- Net PnL Total: -3.74280

- SQN Score: -11.49429


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 143 | 0 | 0.00% | **0.00000** |  |
| TREND_DOWN | 26 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 2974 | 19 | 21.05% | **-0.00688** |  |
| CHOP_LOWVOL | 91819 | 1332 | 27.25% | **-0.00259** |  |
| PANIC | 931 | 21 | 23.81% | **-0.00742** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00271

- Last 20% Median Exp: -0.00320

- Drop Ratio: -17.91%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
