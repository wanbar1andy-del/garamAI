# Turbo V3 Verified Result (005070)

## Meta

- Run ID: `verify_turbo_v3_005070_20251215_071608`
- Timestamp (UTC): `2025-12-15T07:16:08Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `005070` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2412, win_rate=0.00%, pnl=None, mdd=0.00%, equity=2163569.965271221

## Key Points

- Total Return: -97.84%
- Max Drawdown: -97.88%
- Trades: 2412
- Final Equity: 2,163,570 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1206

- Win Rate: 25.12%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00000

- **Expectancy (Net)**: **-0.00280**

- Net PnL Total: -3.37319

- SQN Score: -7.94202


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**
- **REGIME_MISMATCH**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 241 | 1 | 0.00% | **-0.00560** |  |
| TREND_DOWN | 319 | 1 | 0.00% | **-0.00919** |  |
| CHOP_HIGHVOL | 5756 | 53 | 30.19% | **-0.00564** |  |
| CHOP_LOWVOL | 87981 | 1124 | 24.91% | **-0.00269** |  |
| PANIC | 1199 | 27 | 25.93% | **-0.00126** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00272

- Last 20% Median Exp: -0.00301

- Drop Ratio: -10.43%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
