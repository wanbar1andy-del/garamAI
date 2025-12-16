# Turbo V3 Verified Result (030200)

## Meta

- Run ID: `verify_turbo_v3_030200_20251215_025158`
- Timestamp (UTC): `2025-12-15T02:51:58Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `030200` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=3658, win_rate=0.00%, pnl=None, mdd=0.00%, equity=290422.80760307086

## Key Points

- Total Return: -99.71%
- Max Drawdown: -99.71%
- Trades: 3658
- Final Equity: 290,423 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1829

- Win Rate: 24.17%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): -0.00020

- **Expectancy (Net)**: **-0.00300**

- Net PnL Total: -5.48115

- SQN Score: -38.55131


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 6 | 0 | 0.00% | **0.00000** |  |
| TREND_DOWN | 12 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 89 | 0 | 0.00% | **0.00000** |  |
| CHOP_LOWVOL | 94986 | 1810 | 23.81% | **-0.00301** |  |
| PANIC | 778 | 19 | 57.89% | **-0.00154** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00300

- Last 20% Median Exp: -0.00294

- Drop Ratio: 2.07%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
