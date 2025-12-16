# Turbo V3 Verified Result (462870)

## Meta

- Run ID: `verify_turbo_v3_462870_20251215_091846`
- Timestamp (UTC): `2025-12-15T09:18:46Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `462870` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2918, win_rate=0.00%, pnl=None, mdd=0.00%, equity=1081464.4619122182

## Key Points

- Total Return: -98.92%
- Max Drawdown: -98.93%
- Trades: 2918
- Final Equity: 1,081,464 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1459

- Win Rate: 26.25%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): -0.00005

- **Expectancy (Net)**: **-0.00285**

- Net PnL Total: -4.15266

- SQN Score: -16.49360


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 17 | 0 | 0.00% | **0.00000** |  |
| TREND_DOWN | 247 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 3493 | 35 | 42.86% | **-0.00146** |  |
| CHOP_LOWVOL | 89333 | 1401 | 25.84% | **-0.00285** |  |
| PANIC | 1108 | 23 | 26.09% | **-0.00454** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00303

- Last 20% Median Exp: -0.00291

- Drop Ratio: 4.09%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
