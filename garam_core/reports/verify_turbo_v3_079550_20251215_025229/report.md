# Turbo V3 Verified Result (079550)

## Meta

- Run ID: `verify_turbo_v3_079550_20251215_025229`
- Timestamp (UTC): `2025-12-15T02:52:29Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `079550` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2715, win_rate=0.00%, pnl=None, mdd=0.00%, equity=2852594.60496348

## Key Points

- Total Return: -97.15%
- Max Drawdown: -97.33%
- Trades: 2715
- Final Equity: 2,852,595 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1357

- Win Rate: 27.56%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00056

- **Expectancy (Net)**: **-0.00224**

- Net PnL Total: -3.04065

- SQN Score: -7.18780


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**
- **REGIME_MISMATCH**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 255 | 1 | 100.00% | **0.01844** |  |
| TREND_DOWN | 566 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 5976 | 53 | 35.85% | **0.00248** |  |
| CHOP_LOWVOL | 87971 | 1284 | 27.41% | **-0.00234** |  |
| PANIC | 1114 | 19 | 10.53% | **-0.00952** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00229

- Last 20% Median Exp: -0.00270

- Drop Ratio: -17.89%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
