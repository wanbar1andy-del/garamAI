# Turbo V3 Verified Result (204320)

## Meta

- Run ID: `verify_turbo_v3_204320_20251215_082948`
- Timestamp (UTC): `2025-12-15T08:29:48Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `204320` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=3042, win_rate=0.00%, pnl=None, mdd=0.00%, equity=881395.4313071582

## Key Points

- Total Return: -99.12%
- Max Drawdown: -99.12%
- Trades: 3042
- Final Equity: 881,395 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1521

- Win Rate: 28.99%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): -0.00002

- **Expectancy (Net)**: **-0.00282**

- Net PnL Total: -4.29515

- SQN Score: -17.47222


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 87 | 4 | 50.00% | **-0.00073** |  |
| TREND_DOWN | 60 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 3051 | 26 | 23.08% | **-0.00742** |  |
| CHOP_LOWVOL | 91604 | 1465 | 28.60% | **-0.00277** |  |
| PANIC | 958 | 26 | 53.85% | **-0.00181** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00285

- Last 20% Median Exp: -0.00283

- Drop Ratio: 0.80%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
