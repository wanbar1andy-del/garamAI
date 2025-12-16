# Turbo V3 Verified Result (010120)

## Meta

- Run ID: `verify_turbo_v3_010120_20251215_045602`
- Timestamp (UTC): `2025-12-15T04:56:02Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `010120` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2601, win_rate=0.00%, pnl=None, mdd=0.00%, equity=2749468.837976719

## Key Points

- Total Return: -97.25%
- Max Drawdown: -97.40%
- Trades: 2601
- Final Equity: 2,749,469 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1300

- Win Rate: 26.92%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00029

- **Expectancy (Net)**: **-0.00251**

- Net PnL Total: -3.25825

- SQN Score: -7.76302


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 308 | 3 | 33.33% | **-0.01092** |  |
| TREND_DOWN | 321 | 1 | 0.00% | **-0.00724** |  |
| CHOP_HIGHVOL | 8137 | 73 | 31.51% | **-0.00368** |  |
| CHOP_LOWVOL | 86031 | 1202 | 26.87% | **-0.00235** |  |
| PANIC | 1089 | 21 | 14.29% | **-0.00574** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00268

- Last 20% Median Exp: -0.00133

- Drop Ratio: 50.47%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
