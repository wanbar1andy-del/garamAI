# Turbo V3 Verified Result (450080)

## Meta

- Run ID: `verify_turbo_v3_450080_20251215_055642`
- Timestamp (UTC): `2025-12-15T05:56:42Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `450080` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2539, win_rate=0.00%, pnl=None, mdd=0.00%, equity=1251164.4370871503

## Key Points

- Total Return: -98.75%
- Max Drawdown: -98.77%
- Trades: 2539
- Final Equity: 1,251,164 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1269

- Win Rate: 24.43%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): -0.00040

- **Expectancy (Net)**: **-0.00320**

- Net PnL Total: -4.06088

- SQN Score: -11.11636


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 149 | 1 | 100.00% | **0.04498** |  |
| TREND_DOWN | 86 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 6711 | 56 | 28.57% | **-0.00215** |  |
| CHOP_LOWVOL | 87679 | 1190 | 24.12% | **-0.00322** |  |
| PANIC | 1178 | 22 | 27.27% | **-0.00702** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00342

- Last 20% Median Exp: -0.00242

- Drop Ratio: 29.18%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
