# Turbo V3 Verified Result (0009K0)

## Meta

- Run ID: `verify_turbo_v3_0009K0_20251215_043412`
- Timestamp (UTC): `2025-12-15T04:34:12Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `0009K0` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=46, win_rate=0.00%, pnl=None, mdd=0.00%, equity=86721215.74271056

## Key Points

- Total Return: -13.28%
- Max Drawdown: -26.27%
- Trades: 46
- Final Equity: 86,721,216 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 23

- Win Rate: 21.74%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): -0.00308

- **Expectancy (Net)**: **-0.00588**

- Net PnL Total: -0.13532

- SQN Score: -0.59970


### Collapse Tags (Automated)

- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 127 | 1 | 0.00% | **-0.08000** |  |
| TREND_DOWN | 5 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 1357 | 15 | 6.67% | **-0.01415** |  |
| CHOP_LOWVOL | 1224 | 6 | 50.00% | **-0.00684** |  |
| PANIC | 43 | 1 | 100.00% | **0.19804** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: 0.00000

- Last 20% Median Exp: 0.00000

- Drop Ratio: 0.00%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
