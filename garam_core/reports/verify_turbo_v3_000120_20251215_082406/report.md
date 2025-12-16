# Turbo V3 Verified Result (000120)

## Meta

- Run ID: `verify_turbo_v3_000120_20251215_082406`
- Timestamp (UTC): `2025-12-15T08:24:06Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `000120` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=3118, win_rate=0.00%, pnl=None, mdd=0.00%, equity=852226.71468965

## Key Points

- Total Return: -99.15%
- Max Drawdown: -99.16%
- Trades: 3118
- Final Equity: 852,227 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1559

- Win Rate: 26.62%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00000

- **Expectancy (Net)**: **-0.00280**

- Net PnL Total: -4.36436

- SQN Score: -24.34203


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 163 | 1 | 100.00% | **0.03156** |  |
| TREND_DOWN | 5 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 519 | 5 | 40.00% | **-0.00349** |  |
| CHOP_LOWVOL | 93615 | 1528 | 26.44% | **-0.00282** |  |
| PANIC | 1111 | 25 | 32.00% | **-0.00273** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00288

- Last 20% Median Exp: -0.00269

- Drop Ratio: 6.77%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
