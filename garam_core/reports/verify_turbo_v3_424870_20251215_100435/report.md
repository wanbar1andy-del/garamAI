# Turbo V3 Verified Result (424870)

## Meta

- Run ID: `verify_turbo_v3_424870_20251215_100435`
- Timestamp (UTC): `2025-12-15T10:04:35Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `424870` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=1492, win_rate=0.00%, pnl=None, mdd=0.00%, equity=12194563.094680846

## Key Points

- Total Return: -87.81%
- Max Drawdown: -91.26%
- Trades: 1492
- Final Equity: 12,194,563 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 746

- Win Rate: 26.01%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00047

- **Expectancy (Net)**: **-0.00233**

- Net PnL Total: -1.73661

- SQN Score: -3.10283


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**
- **REGIME_MISMATCH**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 56 | 0 | 0.00% | **0.00000** |  |
| TREND_DOWN | 45 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 12072 | 128 | 21.09% | **-0.00536** |  |
| CHOP_LOWVOL | 40265 | 604 | 27.32% | **-0.00148** |  |
| PANIC | 756 | 14 | 14.29% | **-0.01120** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00298

- Last 20% Median Exp: -0.00191

- Drop Ratio: 35.73%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
