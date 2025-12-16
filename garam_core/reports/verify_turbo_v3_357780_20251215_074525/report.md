# Turbo V3 Verified Result (357780)

## Meta

- Run ID: `verify_turbo_v3_357780_20251215_074525`
- Timestamp (UTC): `2025-12-15T07:45:25Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `357780` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2762, win_rate=0.00%, pnl=None, mdd=0.00%, equity=1310782.3449479414

## Key Points

- Total Return: -98.69%
- Max Drawdown: -98.69%
- Trades: 2762
- Final Equity: 1,310,782 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1381

- Win Rate: 29.18%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): -0.00006

- **Expectancy (Net)**: **-0.00286**

- Net PnL Total: -3.95522

- SQN Score: -14.90557


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 64 | 0 | 0.00% | **0.00000** |  |
| TREND_DOWN | 161 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 7048 | 83 | 26.51% | **-0.00318** |  |
| CHOP_LOWVOL | 85037 | 1269 | 29.24% | **-0.00281** |  |
| PANIC | 1378 | 29 | 34.48% | **-0.00417** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00279

- Last 20% Median Exp: -0.00276

- Drop Ratio: 0.74%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
