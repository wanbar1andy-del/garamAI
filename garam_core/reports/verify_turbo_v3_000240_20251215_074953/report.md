# Turbo V3 Verified Result (000240)

## Meta

- Run ID: `verify_turbo_v3_000240_20251215_074953`
- Timestamp (UTC): `2025-12-15T07:49:53Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `000240` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2947, win_rate=0.00%, pnl=None, mdd=0.00%, equity=1503866.5983132718

## Key Points

- Total Return: -98.50%
- Max Drawdown: -98.54%
- Trades: 2947
- Final Equity: 1,503,867 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1473

- Win Rate: 29.94%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00032

- **Expectancy (Net)**: **-0.00248**

- Net PnL Total: -3.64750

- SQN Score: -11.15536


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 280 | 0 | 0.00% | **0.00000** |  |
| TREND_DOWN | 176 | 2 | 0.00% | **-0.00505** |  |
| CHOP_HIGHVOL | 4371 | 56 | 35.71% | **-0.00130** |  |
| CHOP_LOWVOL | 86955 | 1390 | 29.71% | **-0.00252** |  |
| PANIC | 1548 | 25 | 32.00% | **-0.00224** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00268

- Last 20% Median Exp: -0.00225

- Drop Ratio: 15.75%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
