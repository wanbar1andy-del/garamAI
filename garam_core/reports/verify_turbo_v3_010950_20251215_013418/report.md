# Turbo V3 Verified Result (010950)

## Meta

- Run ID: `verify_turbo_v3_010950_20251215_013418`
- Timestamp (UTC): `2025-12-15T01:34:18Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `010950` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=3483, win_rate=0.00%, pnl=None, mdd=0.00%, equity=504407.5329324899

## Key Points

- Total Return: -99.50%
- Max Drawdown: -99.50%
- Trades: 3483
- Final Equity: 504,408 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1741

- Win Rate: 25.50%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00001

- **Expectancy (Net)**: **-0.00279**

- Net PnL Total: -4.86200

- SQN Score: -24.65325


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 133 | 2 | 100.00% | **0.02612** |  |
| TREND_DOWN | 143 | 1 | 100.00% | **0.00063** |  |
| CHOP_HIGHVOL | 828 | 8 | 50.00% | **0.00389** |  |
| CHOP_LOWVOL | 93904 | 1712 | 25.18% | **-0.00285** |  |
| PANIC | 712 | 18 | 33.33% | **-0.00336** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00282

- Last 20% Median Exp: -0.00258

- Drop Ratio: 8.58%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
