# Turbo V3 Verified Result (375500)

## Meta

- Run ID: `verify_turbo_v3_375500_20251215_090134`
- Timestamp (UTC): `2025-12-15T09:01:34Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `375500` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2808, win_rate=0.00%, pnl=None, mdd=0.00%, equity=1335809.5729633532

## Key Points

- Total Return: -98.66%
- Max Drawdown: -98.69%
- Trades: 2808
- Final Equity: 1,335,810 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1404

- Win Rate: 26.85%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00008

- **Expectancy (Net)**: **-0.00272**

- Net PnL Total: -3.82059

- SQN Score: -12.63118


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 270 | 3 | 33.33% | **0.02036** |  |
| TREND_DOWN | 139 | 1 | 0.00% | **-0.00280** |  |
| CHOP_HIGHVOL | 2950 | 34 | 23.53% | **-0.00408** |  |
| CHOP_LOWVOL | 91182 | 1337 | 26.70% | **-0.00277** |  |
| PANIC | 1171 | 29 | 37.93% | **-0.00138** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00265

- Last 20% Median Exp: -0.00300

- Drop Ratio: -12.98%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
