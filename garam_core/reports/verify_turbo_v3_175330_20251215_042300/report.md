# Turbo V3 Verified Result (175330)

## Meta

- Run ID: `verify_turbo_v3_175330_20251215_042300`
- Timestamp (UTC): `2025-12-15T04:23:00Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `175330` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=3272, win_rate=0.00%, pnl=None, mdd=0.00%, equity=417904.16190940345

## Key Points

- Total Return: -99.58%
- Max Drawdown: -99.58%
- Trades: 3272
- Final Equity: 417,904 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1636

- Win Rate: 26.10%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): -0.00027

- **Expectancy (Net)**: **-0.00307**

- Net PnL Total: -5.02540

- SQN Score: -23.12163


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **NEGATIVE_EDGE**
- **REGIME_MISMATCH**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 109 | 0 | 0.00% | **0.00000** |  |
| TREND_DOWN | 95 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 3937 | 62 | 35.48% | **-0.00196** |  |
| CHOP_LOWVOL | 90251 | 1543 | 25.41% | **-0.00317** |  |
| PANIC | 1339 | 31 | 41.94% | **-0.00042** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00294

- Last 20% Median Exp: -0.00330

- Drop Ratio: -12.24%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
