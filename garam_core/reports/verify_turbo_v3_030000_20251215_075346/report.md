# Turbo V3 Verified Result (030000)

## Meta

- Run ID: `verify_turbo_v3_030000_20251215_075346`
- Timestamp (UTC): `2025-12-15T07:53:46Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `030000` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=3479, win_rate=0.00%, pnl=None, mdd=0.00%, equity=365271.60518811847

## Key Points

- Total Return: -99.63%
- Max Drawdown: -99.64%
- Trades: 3479
- Final Equity: 365,272 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1739

- Win Rate: 26.22%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): -0.00014

- **Expectancy (Net)**: **-0.00294**

- Net PnL Total: -5.11978

- SQN Score: -37.99751


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 116 | 0 | 0.00% | **0.00000** |  |
| TREND_DOWN | 119 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 781 | 12 | 25.00% | **-0.00360** |  |
| CHOP_LOWVOL | 93526 | 1705 | 26.10% | **-0.00295** |  |
| PANIC | 1188 | 22 | 36.36% | **-0.00247** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00288

- Last 20% Median Exp: -0.00311

- Drop Ratio: -7.82%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
