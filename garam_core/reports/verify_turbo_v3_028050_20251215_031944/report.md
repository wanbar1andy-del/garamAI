# Turbo V3 Verified Result (028050)

## Meta

- Run ID: `verify_turbo_v3_028050_20251215_031944`
- Timestamp (UTC): `2025-12-15T03:19:44Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `028050` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=3102, win_rate=0.00%, pnl=None, mdd=0.00%, equity=787258.8450176043

## Key Points

- Total Return: -99.21%
- Max Drawdown: -99.22%
- Trades: 3102
- Final Equity: 787,259 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1551

- Win Rate: 26.43%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00000

- **Expectancy (Net)**: **-0.00280**

- Net PnL Total: -4.34254

- SQN Score: -19.08145


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 27 | 0 | 0.00% | **0.00000** |  |
| TREND_DOWN | 117 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 459 | 4 | 0.00% | **-0.00622** |  |
| CHOP_LOWVOL | 94257 | 1522 | 26.28% | **-0.00281** |  |
| PANIC | 1026 | 25 | 40.00% | **-0.00155** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00260

- Last 20% Median Exp: -0.00322

- Drop Ratio: -23.87%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
