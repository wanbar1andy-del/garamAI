# Turbo V3 Verified Result (237690)

## Meta

- Run ID: `verify_turbo_v3_237690_20251215_083429`
- Timestamp (UTC): `2025-12-15T08:34:29Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `237690` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2763, win_rate=0.00%, pnl=None, mdd=0.00%, equity=1387653.092411535

## Key Points

- Total Return: -98.61%
- Max Drawdown: -98.65%
- Trades: 2763
- Final Equity: 1,387,653 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1381

- Win Rate: 27.15%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00004

- **Expectancy (Net)**: **-0.00276**

- Net PnL Total: -3.80851

- SQN Score: -13.89533


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 18 | 0 | 0.00% | **0.00000** |  |
| TREND_DOWN | 30 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 1886 | 10 | 30.00% | **-0.00323** |  |
| CHOP_LOWVOL | 92259 | 1335 | 26.59% | **-0.00279** |  |
| PANIC | 1213 | 36 | 47.22% | **-0.00138** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00296

- Last 20% Median Exp: -0.00204

- Drop Ratio: 31.11%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
