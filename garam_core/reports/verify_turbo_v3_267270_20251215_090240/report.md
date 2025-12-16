# Turbo V3 Verified Result (267270)

## Meta

- Run ID: `verify_turbo_v3_267270_20251215_090240`
- Timestamp (UTC): `2025-12-15T09:02:40Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `267270` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2731, win_rate=0.00%, pnl=None, mdd=0.00%, equity=1804618.368573534

## Key Points

- Total Return: -98.20%
- Max Drawdown: -98.29%
- Trades: 2731
- Final Equity: 1,804,618 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1365

- Win Rate: 28.50%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00017

- **Expectancy (Net)**: **-0.00263**

- Net PnL Total: -3.58362

- SQN Score: -8.85717


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**
- **REGIME_MISMATCH**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 148 | 1 | 0.00% | **-0.02077** |  |
| TREND_DOWN | 124 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 4443 | 42 | 30.95% | **-0.00504** |  |
| CHOP_LOWVOL | 89693 | 1293 | 28.07% | **-0.00255** |  |
| PANIC | 1191 | 29 | 44.83% | **-0.00184** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00262

- Last 20% Median Exp: -0.00219

- Drop Ratio: 16.18%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
