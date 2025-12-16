# Turbo V3 Verified Result (051900)

## Meta

- Run ID: `verify_turbo_v3_051900_20251215_045752`
- Timestamp (UTC): `2025-12-15T04:57:52Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `051900` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=3598, win_rate=0.00%, pnl=None, mdd=0.00%, equity=264879.665314821

## Key Points

- Total Return: -99.74%
- Max Drawdown: -99.74%
- Trades: 3598
- Final Equity: 264,880 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1799

- Win Rate: 22.57%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): -0.00024

- **Expectancy (Net)**: **-0.00304**

- Net PnL Total: -5.46141

- SQN Score: -34.59369


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 48 | 1 | 100.00% | **0.04797** |  |
| TREND_DOWN | 91 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 55 | 0 | 0.00% | **0.00000** |  |
| CHOP_LOWVOL | 94029 | 1777 | 22.40% | **-0.00307** |  |
| PANIC | 729 | 21 | 33.33% | **-0.00276** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00314

- Last 20% Median Exp: -0.00276

- Drop Ratio: 12.20%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
