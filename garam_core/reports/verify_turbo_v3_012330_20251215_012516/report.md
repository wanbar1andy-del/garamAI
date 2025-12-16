# Turbo V3 Verified Result (012330)

## Meta

- Run ID: `verify_turbo_v3_012330_20251215_012516`
- Timestamp (UTC): `2025-12-15T01:25:16Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `012330` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=3219, win_rate=0.00%, pnl=None, mdd=0.00%, equity=751405.4235230795

## Key Points

- Total Return: -99.25%
- Max Drawdown: -99.26%
- Trades: 3219
- Final Equity: 751,405 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1609

- Win Rate: 26.60%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): -0.00000

- **Expectancy (Net)**: **-0.00280**

- Net PnL Total: -4.51255

- SQN Score: -19.88121


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 175 | 0 | 0.00% | **0.00000** |  |
| TREND_DOWN | 3 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 309 | 1 | 100.00% | **0.00146** |  |
| CHOP_LOWVOL | 94634 | 1582 | 26.11% | **-0.00289** |  |
| PANIC | 758 | 26 | 53.85% | **0.00221** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00281

- Last 20% Median Exp: -0.00301

- Drop Ratio: -6.78%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
