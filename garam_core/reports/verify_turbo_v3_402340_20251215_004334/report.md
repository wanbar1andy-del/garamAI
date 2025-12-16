# Turbo V3 Verified Result (402340)

## Meta

- Run ID: `verify_turbo_v3_402340_20251215_004334`
- Timestamp (UTC): `2025-12-15T00:43:34Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `402340` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2632, win_rate=0.00%, pnl=None, mdd=0.00%, equity=3461065.655355555

## Key Points

- Total Return: -96.54%
- Max Drawdown: -96.54%
- Trades: 2632
- Final Equity: 3,461,066 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1316

- Win Rate: 29.03%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00046

- **Expectancy (Net)**: **-0.00234**

- Net PnL Total: -3.08505

- SQN Score: -7.85066


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**
- **REGIME_MISMATCH**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 578 | 5 | 80.00% | **0.00941** |  |
| TREND_DOWN | 208 | 2 | 50.00% | **0.00595** |  |
| CHOP_HIGHVOL | 7758 | 92 | 35.87% | **-0.00018** |  |
| CHOP_LOWVOL | 85959 | 1193 | 28.42% | **-0.00250** |  |
| PANIC | 1258 | 24 | 20.83% | **-0.00616** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00246

- Last 20% Median Exp: -0.00153

- Drop Ratio: 37.65%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
