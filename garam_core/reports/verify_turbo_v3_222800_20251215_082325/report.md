# Turbo V3 Verified Result (222800)

## Meta

- Run ID: `verify_turbo_v3_222800_20251215_082325`
- Timestamp (UTC): `2025-12-15T08:23:25Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `222800` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2448, win_rate=0.00%, pnl=None, mdd=0.00%, equity=4874750.454760914

## Key Points

- Total Return: -95.13%
- Max Drawdown: -95.18%
- Trades: 2448
- Final Equity: 4,874,750 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1224

- Win Rate: 29.17%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00075

- **Expectancy (Net)**: **-0.00205**

- Net PnL Total: -2.50877

- SQN Score: -4.65063


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**
- **REGIME_MISMATCH**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 331 | 2 | 50.00% | **-0.01500** |  |
| TREND_DOWN | 436 | 3 | 0.00% | **-0.00389** |  |
| CHOP_HIGHVOL | 18150 | 202 | 29.21% | **-0.00458** |  |
| CHOP_LOWVOL | 74892 | 983 | 28.89% | **-0.00153** |  |
| PANIC | 1287 | 34 | 38.24% | **-0.00110** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00205

- Last 20% Median Exp: -0.00229

- Drop Ratio: -11.76%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
