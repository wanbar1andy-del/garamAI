# Turbo V3 Verified Result (003550)

## Meta

- Run ID: `verify_turbo_v3_003550_20251215_004342`
- Timestamp (UTC): `2025-12-15T00:43:42Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `003550` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=3283, win_rate=0.00%, pnl=None, mdd=0.00%, equity=495581.1958500816

## Key Points

- Total Return: -99.50%
- Max Drawdown: -99.51%
- Trades: 3283
- Final Equity: 495,581 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1641

- Win Rate: 25.23%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): -0.00019

- **Expectancy (Net)**: **-0.00299**

- Net PnL Total: -4.89905

- SQN Score: -25.22492


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 101 | 2 | 100.00% | **0.00295** |  |
| TREND_DOWN | 49 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 393 | 3 | 0.00% | **-0.01749** |  |
| CHOP_LOWVOL | 94273 | 1616 | 25.12% | **-0.00296** |  |
| PANIC | 869 | 20 | 30.00% | **-0.00325** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00305

- Last 20% Median Exp: -0.00276

- Drop Ratio: 9.67%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
