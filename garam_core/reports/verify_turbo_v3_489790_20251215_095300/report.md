# Turbo V3 Verified Result (489790)

## Meta

- Run ID: `verify_turbo_v3_489790_20251215_095300`
- Timestamp (UTC): `2025-12-15T09:53:00Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `489790` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2674, win_rate=0.00%, pnl=None, mdd=0.00%, equity=2201587.120569508

## Key Points

- Total Return: -97.80%
- Max Drawdown: -97.91%
- Trades: 2674
- Final Equity: 2,201,587 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1337

- Win Rate: 26.85%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00026

- **Expectancy (Net)**: **-0.00254**

- Net PnL Total: -3.39788

- SQN Score: -6.87169


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**
- **REGIME_MISMATCH**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 119 | 0 | 0.00% | **0.00000** |  |
| TREND_DOWN | 217 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 13296 | 133 | 31.58% | **-0.00465** |  |
| CHOP_LOWVOL | 81113 | 1177 | 26.42% | **-0.00218** |  |
| PANIC | 1117 | 27 | 22.22% | **-0.00801** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00260

- Last 20% Median Exp: -0.00321

- Drop Ratio: -23.76%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
