# Turbo V3 Verified Result (002790)

## Meta

- Run ID: `verify_turbo_v3_002790_20251215_080458`
- Timestamp (UTC): `2025-12-15T08:04:58Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `002790` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=3394, win_rate=0.00%, pnl=None, mdd=0.00%, equity=470223.6700872786

## Key Points

- Total Return: -99.53%
- Max Drawdown: -99.53%
- Trades: 3394
- Final Equity: 470,224 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1697

- Win Rate: 25.10%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): -0.00012

- **Expectancy (Net)**: **-0.00292**

- Net PnL Total: -4.94809

- SQN Score: -22.43289


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 26 | 0 | 0.00% | **0.00000** |  |
| TREND_DOWN | 51 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 1710 | 13 | 30.77% | **0.00114** |  |
| CHOP_LOWVOL | 91047 | 1665 | 25.05% | **-0.00296** |  |
| PANIC | 835 | 19 | 26.32% | **-0.00217** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00287

- Last 20% Median Exp: -0.00292

- Drop Ratio: -1.95%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
