# Turbo V3 Verified Result (348370)

## Meta

- Run ID: `verify_turbo_v3_348370_20251215_094735`
- Timestamp (UTC): `2025-12-15T09:47:35Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `348370` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2340, win_rate=0.00%, pnl=None, mdd=0.00%, equity=2079274.175090791

## Key Points

- Total Return: -97.92%
- Max Drawdown: -98.11%
- Trades: 2340
- Final Equity: 2,079,274 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1170

- Win Rate: 23.93%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): -0.00009

- **Expectancy (Net)**: **-0.00289**

- Net PnL Total: -3.38501

- SQN Score: -6.68759


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **NEGATIVE_EDGE**
- **REGIME_MISMATCH**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 288 | 4 | 25.00% | **-0.01232** |  |
| TREND_DOWN | 294 | 1 | 0.00% | **-0.00722** |  |
| CHOP_HIGHVOL | 9533 | 88 | 26.14% | **-0.00535** |  |
| CHOP_LOWVOL | 83929 | 1042 | 23.51% | **-0.00265** |  |
| PANIC | 1448 | 35 | 31.43% | **-0.00277** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00260

- Last 20% Median Exp: -0.00379

- Drop Ratio: -45.62%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
