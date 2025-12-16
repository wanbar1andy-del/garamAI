# Turbo V3 Verified Result (020560)

## Meta

- Run ID: `verify_turbo_v3_020560_20251215_095528`
- Timestamp (UTC): `2025-12-15T09:55:28Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `020560` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=3185, win_rate=0.00%, pnl=None, mdd=0.00%, equity=663022.6918025563

## Key Points

- Total Return: -99.34%
- Max Drawdown: -99.37%
- Trades: 3185
- Final Equity: 663,023 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1592

- Win Rate: 24.69%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): -0.00012

- **Expectancy (Net)**: **-0.00292**

- Net PnL Total: -4.65547

- SQN Score: -39.92269


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 175 | 3 | 66.67% | **0.00043** |  |
| TREND_DOWN | 9 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 159 | 0 | 0.00% | **0.00000** |  |
| CHOP_LOWVOL | 84818 | 1546 | 24.39% | **-0.00295** |  |
| PANIC | 1465 | 43 | 32.56% | **-0.00231** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00289

- Last 20% Median Exp: -0.00310

- Drop Ratio: -7.24%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
