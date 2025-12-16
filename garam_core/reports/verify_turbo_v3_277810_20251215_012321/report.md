# Turbo V3 Verified Result (277810)

## Meta

- Run ID: `verify_turbo_v3_277810_20251215_012321`
- Timestamp (UTC): `2025-12-15T01:23:21Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `277810` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2690, win_rate=0.00%, pnl=None, mdd=0.00%, equity=2821738.389074214

## Key Points

- Total Return: -97.18%
- Max Drawdown: -97.47%
- Trades: 2690
- Final Equity: 2,821,738 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1345

- Win Rate: 26.77%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00050

- **Expectancy (Net)**: **-0.00230**

- Net PnL Total: -3.09587

- SQN Score: -6.37493


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 332 | 2 | 0.00% | **-0.02838** |  |
| TREND_DOWN | 118 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 7776 | 75 | 32.00% | **-0.00141** |  |
| CHOP_LOWVOL | 86247 | 1248 | 26.20% | **-0.00242** |  |
| PANIC | 1164 | 20 | 45.00% | **0.00457** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00284

- Last 20% Median Exp: -0.00173

- Drop Ratio: 39.15%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
