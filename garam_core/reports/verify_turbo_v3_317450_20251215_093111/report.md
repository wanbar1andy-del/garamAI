# Turbo V3 Verified Result (317450)

## Meta

- Run ID: `verify_turbo_v3_317450_20251215_093111`
- Timestamp (UTC): `2025-12-15T09:31:11Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `317450` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=433, win_rate=0.00%, pnl=None, mdd=0.00%, equity=54505464.05960694

## Key Points

- Total Return: -45.49%
- Max Drawdown: -51.84%
- Trades: 433
- Final Equity: 54,505,464 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 216

- Win Rate: 24.54%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00010

- **Expectancy (Net)**: **-0.00270**

- Net PnL Total: -0.58370

- SQN Score: -3.21548


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 36 | 0 | 0.00% | **0.00000** |  |
| TREND_DOWN | 136 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 2259 | 13 | 30.77% | **0.00629** |  |
| CHOP_LOWVOL | 15491 | 198 | 23.74% | **-0.00329** |  |
| PANIC | 284 | 5 | 40.00% | **-0.00269** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00298

- Last 20% Median Exp: -0.00285

- Drop Ratio: 4.43%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
