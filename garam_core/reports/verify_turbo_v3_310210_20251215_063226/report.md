# Turbo V3 Verified Result (310210)

## Meta

- Run ID: `verify_turbo_v3_310210_20251215_063226`
- Timestamp (UTC): `2025-12-15T06:32:26Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `310210` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2506, win_rate=0.00%, pnl=None, mdd=0.00%, equity=1691059.3203800272

## Key Points

- Total Return: -98.31%
- Max Drawdown: -98.45%
- Trades: 2506
- Final Equity: 1,691,059 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1253

- Win Rate: 28.97%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00012

- **Expectancy (Net)**: **-0.00268**

- Net PnL Total: -3.36245

- SQN Score: -6.97037


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 159 | 2 | 100.00% | **0.02299** |  |
| TREND_DOWN | 103 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 17880 | 211 | 29.86% | **-0.00203** |  |
| CHOP_LOWVOL | 75925 | 1019 | 28.66% | **-0.00291** |  |
| PANIC | 1601 | 21 | 28.57% | **-0.00045** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00258

- Last 20% Median Exp: -0.00255

- Drop Ratio: 1.10%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
