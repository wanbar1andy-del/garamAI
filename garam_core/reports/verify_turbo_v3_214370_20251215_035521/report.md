# Turbo V3 Verified Result (214370)

## Meta

- Run ID: `verify_turbo_v3_214370_20251215_035521`
- Timestamp (UTC): `2025-12-15T03:55:21Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `214370` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2374, win_rate=0.00%, pnl=None, mdd=0.00%, equity=2647393.1959580067

## Key Points

- Total Return: -97.35%
- Max Drawdown: -97.43%
- Trades: 2374
- Final Equity: 2,647,393 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1187

- Win Rate: 28.90%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00039

- **Expectancy (Net)**: **-0.00241**

- Net PnL Total: -2.86538

- SQN Score: -5.80844


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**
- **REGIME_MISMATCH**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 166 | 1 | 100.00% | **0.01060** |  |
| TREND_DOWN | 19 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 13001 | 162 | 25.31% | **-0.00443** |  |
| CHOP_LOWVOL | 72885 | 996 | 29.42% | **-0.00199** |  |
| PANIC | 1495 | 28 | 28.57% | **-0.00630** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00251

- Last 20% Median Exp: -0.00237

- Drop Ratio: 5.44%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
