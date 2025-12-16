# Turbo V3 Verified Result (039490)

## Meta

- Run ID: `verify_turbo_v3_039490_20251215_005322`
- Timestamp (UTC): `2025-12-15T00:53:22Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `039490` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2972, win_rate=0.00%, pnl=None, mdd=0.00%, equity=1658907.902491033

## Key Points

- Total Return: -98.34%
- Max Drawdown: -98.37%
- Trades: 2972
- Final Equity: 1,658,908 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1486

- Win Rate: 30.28%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00041

- **Expectancy (Net)**: **-0.00239**

- Net PnL Total: -3.55548

- SQN Score: -10.99024


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**
- **REGIME_MISMATCH**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 292 | 0 | 0.00% | **0.00000** |  |
| TREND_DOWN | 307 | 1 | 0.00% | **-0.00364** |  |
| CHOP_HIGHVOL | 7462 | 102 | 28.43% | **-0.00427** |  |
| CHOP_LOWVOL | 86508 | 1361 | 30.12% | **-0.00228** |  |
| PANIC | 1152 | 22 | 50.00% | **-0.00039** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00230

- Last 20% Median Exp: -0.00169

- Drop Ratio: 26.68%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
