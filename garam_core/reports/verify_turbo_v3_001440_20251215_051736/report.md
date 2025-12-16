# Turbo V3 Verified Result (001440)

## Meta

- Run ID: `verify_turbo_v3_001440_20251215_051736`
- Timestamp (UTC): `2025-12-15T05:17:36Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `001440` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2401, win_rate=0.00%, pnl=None, mdd=0.00%, equity=2930671.099876921

## Key Points

- Total Return: -97.07%
- Max Drawdown: -97.15%
- Trades: 2401
- Final Equity: 2,930,671 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1200

- Win Rate: 26.25%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00018

- **Expectancy (Net)**: **-0.00262**

- Net PnL Total: -3.14422

- SQN Score: -9.75124


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 331 | 6 | 33.33% | **-0.01787** |  |
| TREND_DOWN | 324 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 4576 | 44 | 29.55% | **-0.00162** |  |
| CHOP_LOWVOL | 89246 | 1122 | 26.02% | **-0.00254** |  |
| PANIC | 1268 | 28 | 28.57% | **-0.00398** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00253

- Last 20% Median Exp: -0.00263

- Drop Ratio: -3.96%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
