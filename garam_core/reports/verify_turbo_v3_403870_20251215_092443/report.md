# Turbo V3 Verified Result (403870)

## Meta

- Run ID: `verify_turbo_v3_403870_20251215_092443`
- Timestamp (UTC): `2025-12-15T09:24:43Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `403870` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2894, win_rate=0.00%, pnl=None, mdd=0.00%, equity=771275.3976210688

## Key Points

- Total Return: -99.23%
- Max Drawdown: -99.24%
- Trades: 2894
- Final Equity: 771,275 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1447

- Win Rate: 24.95%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): -0.00029

- **Expectancy (Net)**: **-0.00309**

- Net PnL Total: -4.47563

- SQN Score: -14.40931


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 80 | 1 | 0.00% | **-0.03366** |  |
| TREND_DOWN | 155 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 2724 | 19 | 31.58% | **-0.00145** |  |
| CHOP_LOWVOL | 91853 | 1406 | 24.68% | **-0.00315** |  |
| PANIC | 833 | 21 | 38.10% | **0.00067** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00313

- Last 20% Median Exp: -0.00354

- Drop Ratio: -13.30%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
