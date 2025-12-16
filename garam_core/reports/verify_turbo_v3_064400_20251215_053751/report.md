# Turbo V3 Verified Result (064400)

## Meta

- Run ID: `verify_turbo_v3_064400_20251215_053751`
- Timestamp (UTC): `2025-12-15T05:37:51Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `064400` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2400, win_rate=0.00%, pnl=None, mdd=0.00%, equity=1676576.91889204

## Key Points

- Total Return: -98.32%
- Max Drawdown: -98.32%
- Trades: 2400
- Final Equity: 1,676,577 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1200

- Win Rate: 27.67%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): -0.00033

- **Expectancy (Net)**: **-0.00313**

- Net PnL Total: -3.75578

- SQN Score: -14.98144


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **NEGATIVE_EDGE**
- **REGIME_MISMATCH**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 17 | 1 | 100.00% | **-0.00179** |  |
| TREND_DOWN | 194 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 3593 | 34 | 41.18% | **-0.00101** |  |
| CHOP_LOWVOL | 73937 | 1145 | 27.07% | **-0.00313** |  |
| PANIC | 722 | 20 | 35.00% | **-0.00675** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00302

- Last 20% Median Exp: -0.00317

- Drop Ratio: -4.83%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
