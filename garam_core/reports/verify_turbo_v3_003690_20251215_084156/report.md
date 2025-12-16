# Turbo V3 Verified Result (003690)

## Meta

- Run ID: `verify_turbo_v3_003690_20251215_084156`
- Timestamp (UTC): `2025-12-15T08:41:56Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `003690` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=3362, win_rate=0.00%, pnl=None, mdd=0.00%, equity=474465.8158910429

## Key Points

- Total Return: -99.53%
- Max Drawdown: -99.53%
- Trades: 3362
- Final Equity: 474,466 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1681

- Win Rate: 25.52%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): -0.00006

- **Expectancy (Net)**: **-0.00286**

- Net PnL Total: -4.81395

- SQN Score: -30.20073


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 48 | 1 | 100.00% | **0.01659** |  |
| TREND_DOWN | 62 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 222 | 5 | 20.00% | **-0.00426** |  |
| CHOP_LOWVOL | 93339 | 1657 | 25.47% | **-0.00287** |  |
| PANIC | 1332 | 18 | 27.78% | **-0.00313** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00299

- Last 20% Median Exp: -0.00273

- Drop Ratio: 8.41%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
