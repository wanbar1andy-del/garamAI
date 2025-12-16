# Turbo V3 Verified Result (377300)

## Meta

- Run ID: `verify_turbo_v3_377300_20251215_004325`
- Timestamp (UTC): `2025-12-15T00:43:25Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `377300` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2901, win_rate=0.00%, pnl=None, mdd=0.00%, equity=982219.398290086

## Key Points

- Total Return: -99.02%
- Max Drawdown: -99.10%
- Trades: 2901
- Final Equity: 982,219 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1450

- Win Rate: 25.38%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00016

- **Expectancy (Net)**: **-0.00264**

- Net PnL Total: -3.82165

- SQN Score: -5.04393


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**
- **REGIME_MISMATCH**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 240 | 0 | 0.00% | **0.00000** |  |
| TREND_DOWN | 153 | 1 | 0.00% | **-0.00775** |  |
| CHOP_HIGHVOL | 10342 | 102 | 31.37% | **-0.00451** |  |
| CHOP_LOWVOL | 83068 | 1324 | 24.70% | **-0.00279** |  |
| PANIC | 1091 | 23 | 39.13% | **0.01501** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00268

- Last 20% Median Exp: -0.00354

- Drop Ratio: -32.15%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
