# Turbo V3 Verified Result (042660)

## Meta

- Run ID: `verify_turbo_v3_042660_20251215_011515`
- Timestamp (UTC): `2025-12-15T01:15:15Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `042660` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2446, win_rate=0.00%, pnl=None, mdd=0.00%, equity=6125544.788557583

## Key Points

- Total Return: -93.87%
- Max Drawdown: -94.01%
- Trades: 2446
- Final Equity: 6,125,545 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1223

- Win Rate: 30.50%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00081

- **Expectancy (Net)**: **-0.00199**

- Net PnL Total: -2.42812

- SQN Score: -6.10775


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**
- **REGIME_MISMATCH**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 171 | 3 | 33.33% | **-0.01027** |  |
| TREND_DOWN | 290 | 2 | 0.00% | **-0.00594** |  |
| CHOP_HIGHVOL | 5623 | 52 | 40.38% | **-0.00033** |  |
| CHOP_LOWVOL | 88443 | 1143 | 30.10% | **-0.00210** |  |
| PANIC | 1278 | 23 | 30.43% | **0.00134** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00196

- Last 20% Median Exp: -0.00228

- Drop Ratio: -16.27%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
