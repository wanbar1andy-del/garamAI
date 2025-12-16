# Turbo V3 Verified Result (064350)

## Meta

- Run ID: `verify_turbo_v3_064350_20251215_013521`
- Timestamp (UTC): `2025-12-15T01:35:21Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `064350` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2522, win_rate=0.00%, pnl=None, mdd=0.00%, equity=4498620.562521485

## Key Points

- Total Return: -95.50%
- Max Drawdown: -95.69%
- Trades: 2522
- Final Equity: 4,498,621 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1261

- Win Rate: 31.17%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00063

- **Expectancy (Net)**: **-0.00217**

- Net PnL Total: -2.73026

- SQN Score: -6.61528


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**
- **REGIME_MISMATCH**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 243 | 5 | 60.00% | **-0.00007** |  |
| TREND_DOWN | 128 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 5611 | 50 | 30.00% | **0.00101** |  |
| CHOP_LOWVOL | 88644 | 1184 | 30.57% | **-0.00232** |  |
| PANIC | 1267 | 22 | 59.09% | **-0.00143** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00203

- Last 20% Median Exp: -0.00229

- Drop Ratio: -12.88%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
