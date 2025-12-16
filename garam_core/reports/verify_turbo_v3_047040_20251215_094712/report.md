# Turbo V3 Verified Result (047040)

## Meta

- Run ID: `verify_turbo_v3_047040_20251215_094712`
- Timestamp (UTC): `2025-12-15T09:47:12Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `047040` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2972, win_rate=0.00%, pnl=None, mdd=0.00%, equity=1117400.1479928496

## Key Points

- Total Return: -98.88%
- Max Drawdown: -98.89%
- Trades: 2972
- Final Equity: 1,117,400 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1486

- Win Rate: 23.49%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): -0.00003

- **Expectancy (Net)**: **-0.00283**

- Net PnL Total: -4.20823

- SQN Score: -16.90956


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 136 | 1 | 0.00% | **-0.03445** |  |
| TREND_DOWN | 54 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 628 | 4 | 25.00% | **-0.00604** |  |
| CHOP_LOWVOL | 92822 | 1454 | 23.59% | **-0.00275** |  |
| PANIC | 1006 | 27 | 18.52% | **-0.00535** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00268

- Last 20% Median Exp: -0.00311

- Drop Ratio: -16.13%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
