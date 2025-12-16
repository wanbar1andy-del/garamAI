# Turbo V3 Verified Result (088980)

## Meta

- Run ID: `verify_turbo_v3_088980_20251215_082250`
- Timestamp (UTC): `2025-12-15T08:22:50Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `088980` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=4166, win_rate=0.00%, pnl=None, mdd=0.00%, equity=169663.09622356153

## Key Points

- Total Return: -99.83%
- Max Drawdown: -99.83%
- Trades: 4166
- Final Equity: 169,663 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 2083

- Win Rate: 25.73%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00003

- **Expectancy (Net)**: **-0.00277**

- Net PnL Total: -5.76981

- SQN Score: -80.78349


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 0 | 0 | 0.00% | **0.00000** |  |
| TREND_DOWN | 172 | 2 | 50.00% | **-0.00307** |  |
| CHOP_HIGHVOL | 9 | 0 | 0.00% | **0.00000** |  |
| CHOP_LOWVOL | 95038 | 2063 | 25.69% | **-0.00277** |  |
| PANIC | 650 | 18 | 27.78% | **-0.00319** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00277

- Last 20% Median Exp: -0.00283

- Drop Ratio: -2.36%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
