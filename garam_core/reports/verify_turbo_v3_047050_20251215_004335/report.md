# Turbo V3 Verified Result (047050)

## Meta

- Run ID: `verify_turbo_v3_047050_20251215_004335`
- Timestamp (UTC): `2025-12-15T00:43:35Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `047050` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2705, win_rate=0.00%, pnl=None, mdd=0.00%, equity=1758156.0162681737

## Key Points

- Total Return: -98.24%
- Max Drawdown: -98.26%
- Trades: 2705
- Final Equity: 1,758,156 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1352

- Win Rate: 26.70%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00005

- **Expectancy (Net)**: **-0.00275**

- Net PnL Total: -3.71275

- SQN Score: -12.14534


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**
- **REGIME_MISMATCH**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 77 | 2 | 50.00% | **0.00063** |  |
| TREND_DOWN | 203 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 4904 | 49 | 38.78% | **-0.00061** |  |
| CHOP_LOWVOL | 89657 | 1286 | 26.21% | **-0.00280** |  |
| PANIC | 947 | 15 | 26.67% | **-0.00516** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00267

- Last 20% Median Exp: -0.00258

- Drop Ratio: 3.59%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
