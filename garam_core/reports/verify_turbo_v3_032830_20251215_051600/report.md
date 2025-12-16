# Turbo V3 Verified Result (032830)

## Meta

- Run ID: `verify_turbo_v3_032830_20251215_051600`
- Timestamp (UTC): `2025-12-15T05:16:00Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `032830` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2737, win_rate=0.00%, pnl=None, mdd=0.00%, equity=2088232.9148176797

## Key Points

- Total Return: -97.91%
- Max Drawdown: -97.91%
- Trades: 2737
- Final Equity: 2,088,233 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1368

- Win Rate: 28.00%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00019

- **Expectancy (Net)**: **-0.00261**

- Net PnL Total: -3.57677

- SQN Score: -13.40500


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**
- **REGIME_MISMATCH**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 382 | 2 | 50.00% | **0.00858** |  |
| TREND_DOWN | 238 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 653 | 1 | 100.00% | **-0.00197** |  |
| CHOP_LOWVOL | 93117 | 1335 | 27.49% | **-0.00260** |  |
| PANIC | 1453 | 30 | 46.67% | **-0.00420** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00264

- Last 20% Median Exp: -0.00225

- Drop Ratio: 14.68%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
