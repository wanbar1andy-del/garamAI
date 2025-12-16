# Turbo V3 Verified Result (249420)

## Meta

- Run ID: `verify_turbo_v3_249420_20251215_095738`
- Timestamp (UTC): `2025-12-15T09:57:38Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `249420` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2212, win_rate=0.00%, pnl=None, mdd=0.00%, equity=6707368.279983447

## Key Points

- Total Return: -93.29%
- Max Drawdown: -93.99%
- Trades: 2212
- Final Equity: 6,707,368 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1106

- Win Rate: 27.94%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00070

- **Expectancy (Net)**: **-0.00210**

- Net PnL Total: -2.31870

- SQN Score: -3.98312


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**
- **REGIME_MISMATCH**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 111 | 2 | 50.00% | **-0.01055** |  |
| TREND_DOWN | 13 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 17431 | 174 | 30.46% | **-0.00068** |  |
| CHOP_LOWVOL | 58963 | 889 | 27.00% | **-0.00242** |  |
| PANIC | 1468 | 41 | 36.59% | **-0.00061** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00250

- Last 20% Median Exp: -0.00099

- Drop Ratio: 60.32%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
