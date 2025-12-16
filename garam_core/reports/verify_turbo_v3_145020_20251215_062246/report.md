# Turbo V3 Verified Result (145020)

## Meta

- Run ID: `verify_turbo_v3_145020_20251215_062246`
- Timestamp (UTC): `2025-12-15T06:22:46Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `145020` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2940, win_rate=0.00%, pnl=None, mdd=0.00%, equity=976190.4120280435

## Key Points

- Total Return: -99.02%
- Max Drawdown: -99.08%
- Trades: 2940
- Final Equity: 976,190 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1470

- Win Rate: 26.39%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): -0.00007

- **Expectancy (Net)**: **-0.00287**

- Net PnL Total: -4.22530

- SQN Score: -15.96540


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 16 | 0 | 0.00% | **0.00000** |  |
| TREND_DOWN | 63 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 3488 | 33 | 36.36% | **-0.00306** |  |
| CHOP_LOWVOL | 90879 | 1413 | 25.83% | **-0.00290** |  |
| PANIC | 1147 | 24 | 45.83% | **-0.00085** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00279

- Last 20% Median Exp: -0.00318

- Drop Ratio: -14.05%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
