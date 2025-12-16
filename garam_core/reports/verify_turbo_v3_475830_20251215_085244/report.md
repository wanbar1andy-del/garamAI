# Turbo V3 Verified Result (475830)

## Meta

- Run ID: `verify_turbo_v3_475830_20251215_085244`
- Timestamp (UTC): `2025-12-15T08:52:44Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `475830` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2000, win_rate=0.00%, pnl=None, mdd=0.00%, equity=3082619.0515344404

## Key Points

- Total Return: -96.92%
- Max Drawdown: -97.76%
- Trades: 2000
- Final Equity: 3,082,619 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1000

- Win Rate: 27.50%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): -0.00035

- **Expectancy (Net)**: **-0.00315**

- Net PnL Total: -3.14838

- SQN Score: -6.50571


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 140 | 0 | 0.00% | **0.00000** |  |
| TREND_DOWN | 203 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 17535 | 195 | 27.18% | **-0.00260** |  |
| CHOP_LOWVOL | 56181 | 779 | 27.21% | **-0.00343** |  |
| PANIC | 1240 | 26 | 38.46% | **0.00110** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00301

- Last 20% Median Exp: -0.00327

- Drop Ratio: -8.38%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
