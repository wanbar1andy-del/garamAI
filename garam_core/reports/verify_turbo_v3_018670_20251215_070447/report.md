# Turbo V3 Verified Result (018670)

## Meta

- Run ID: `verify_turbo_v3_018670_20251215_070447`
- Timestamp (UTC): `2025-12-15T07:04:47Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `018670` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=3217, win_rate=0.00%, pnl=None, mdd=0.00%, equity=481353.8928033994

## Key Points

- Total Return: -99.52%
- Max Drawdown: -99.53%
- Trades: 3217
- Final Equity: 481,354 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1608

- Win Rate: 27.18%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): -0.00021

- **Expectancy (Net)**: **-0.00301**

- Net PnL Total: -4.84298

- SQN Score: -22.36288


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 8 | 0 | 0.00% | **0.00000** |  |
| TREND_DOWN | 2 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 4630 | 78 | 28.21% | **-0.00359** |  |
| CHOP_LOWVOL | 86362 | 1511 | 27.27% | **-0.00292** |  |
| PANIC | 958 | 19 | 15.79% | **-0.00755** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00327

- Last 20% Median Exp: -0.00285

- Drop Ratio: 12.80%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
