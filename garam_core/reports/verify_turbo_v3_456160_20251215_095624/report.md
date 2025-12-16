# Turbo V3 Verified Result (456160)

## Meta

- Run ID: `verify_turbo_v3_456160_20251215_095624`
- Timestamp (UTC): `2025-12-15T09:56:24Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `456160` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=722, win_rate=0.00%, pnl=None, mdd=0.00%, equity=38589644.39747878

## Key Points

- Total Return: -61.41%
- Max Drawdown: -77.21%
- Trades: 722
- Final Equity: 38,589,644 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 361

- Win Rate: 26.87%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00072

- **Expectancy (Net)**: **-0.00208**

- Net PnL Total: -0.75268

- SQN Score: -1.61737


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**
- **REGIME_MISMATCH**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 144 | 0 | 0.00% | **0.00000** |  |
| TREND_DOWN | 51 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 15598 | 172 | 30.81% | **0.00010** |  |
| CHOP_LOWVOL | 14509 | 176 | 21.02% | **-0.00431** |  |
| PANIC | 576 | 13 | 53.85% | **-0.00094** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00374

- Last 20% Median Exp: -0.00361

- Drop Ratio: 3.39%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
