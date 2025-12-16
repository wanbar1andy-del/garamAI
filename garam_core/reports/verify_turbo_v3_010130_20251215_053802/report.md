# Turbo V3 Verified Result (010130)

## Meta

- Run ID: `verify_turbo_v3_010130_20251215_053802`
- Timestamp (UTC): `2025-12-15T05:38:02Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `010130` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2573, win_rate=0.00%, pnl=None, mdd=0.00%, equity=3125671.0636333404

## Key Points

- Total Return: -96.87%
- Max Drawdown: -98.14%
- Trades: 2573
- Final Equity: 3,125,671 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1286

- Win Rate: 28.23%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00063

- **Expectancy (Net)**: **-0.00217**

- Net PnL Total: -2.79576

- SQN Score: -4.72948


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**
- **REGIME_MISMATCH**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 445 | 3 | 0.00% | **-0.02229** |  |
| TREND_DOWN | 320 | 2 | 0.00% | **-0.00500** |  |
| CHOP_HIGHVOL | 6880 | 61 | 32.79% | **-0.00320** |  |
| CHOP_LOWVOL | 85492 | 1182 | 28.00% | **-0.00220** |  |
| PANIC | 1532 | 38 | 31.58% | **0.00210** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00238

- Last 20% Median Exp: -0.00250

- Drop Ratio: -4.98%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
