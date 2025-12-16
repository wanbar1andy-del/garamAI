# Turbo V3 Verified Result (105560)

## Meta

- Run ID: `verify_turbo_v3_105560_20251215_042115`
- Timestamp (UTC): `2025-12-15T04:21:15Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `105560` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2838, win_rate=0.00%, pnl=None, mdd=0.00%, equity=1150542.7004056836

## Key Points

- Total Return: -98.85%
- Max Drawdown: -98.85%
- Trades: 2838
- Final Equity: 1,150,543 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1419

- Win Rate: 28.33%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00002

- **Expectancy (Net)**: **-0.00278**

- Net PnL Total: -3.93993

- SQN Score: -18.65280


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 226 | 1 | 100.00% | **-0.00012** |  |
| TREND_DOWN | 179 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 277 | 1 | 0.00% | **-0.00518** |  |
| CHOP_LOWVOL | 94121 | 1402 | 28.10% | **-0.00275** |  |
| PANIC | 1076 | 15 | 46.67% | **-0.00490** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00276

- Last 20% Median Exp: -0.00237

- Drop Ratio: 14.17%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
