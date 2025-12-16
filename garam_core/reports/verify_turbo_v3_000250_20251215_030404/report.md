# Turbo V3 Verified Result (000250)

## Meta

- Run ID: `verify_turbo_v3_000250_20251215_030404`
- Timestamp (UTC): `2025-12-15T03:04:04Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `000250` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2301, win_rate=0.00%, pnl=None, mdd=0.00%, equity=6162642.310843296

## Key Points

- Total Return: -93.84%
- Max Drawdown: -94.55%
- Trades: 2301
- Final Equity: 6,162,642 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1150

- Win Rate: 28.35%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00094

- **Expectancy (Net)**: **-0.00186**

- Net PnL Total: -2.13855

- SQN Score: -3.44138


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**
- **REGIME_MISMATCH**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 488 | 1 | 0.00% | **-0.01748** |  |
| TREND_DOWN | 189 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 6773 | 52 | 30.77% | **-0.00255** |  |
| CHOP_LOWVOL | 86507 | 1065 | 27.61% | **-0.00192** |  |
| PANIC | 1564 | 32 | 50.00% | **0.00163** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00236

- Last 20% Median Exp: -0.00225

- Drop Ratio: 4.69%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
