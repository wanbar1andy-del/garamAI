# Turbo V3 Verified Result (214150)

## Meta

- Run ID: `verify_turbo_v3_214150_20251215_025245`
- Timestamp (UTC): `2025-12-15T02:52:45Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `214150` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2999, win_rate=0.00%, pnl=None, mdd=0.00%, equity=730897.1567092753

## Key Points

- Total Return: -99.27%
- Max Drawdown: -99.27%
- Trades: 2999
- Final Equity: 730,897 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1499

- Win Rate: 25.48%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): -0.00018

- **Expectancy (Net)**: **-0.00298**

- Net PnL Total: -4.46618

- SQN Score: -14.98098


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 143 | 2 | 0.00% | **-0.05109** |  |
| TREND_DOWN | 66 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 3569 | 41 | 21.95% | **-0.00434** |  |
| CHOP_LOWVOL | 90941 | 1427 | 25.44% | **-0.00286** |  |
| PANIC | 972 | 29 | 34.48% | **-0.00365** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00330

- Last 20% Median Exp: -0.00243

- Drop Ratio: 26.50%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
