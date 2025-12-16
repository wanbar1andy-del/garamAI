# Turbo V3 Verified Result (326030)

## Meta

- Run ID: `verify_turbo_v3_326030_20251215_032205`
- Timestamp (UTC): `2025-12-15T03:22:05Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `326030` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2711, win_rate=0.00%, pnl=None, mdd=0.00%, equity=1565483.1987638075

## Key Points

- Total Return: -98.43%
- Max Drawdown: -98.45%
- Trades: 2711
- Final Equity: 1,565,483 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1355

- Win Rate: 28.19%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00001

- **Expectancy (Net)**: **-0.00279**

- Net PnL Total: -3.78535

- SQN Score: -13.78866


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 194 | 1 | 100.00% | **-0.00001** |  |
| TREND_DOWN | 133 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 748 | 7 | 14.29% | **-0.01456** |  |
| CHOP_LOWVOL | 93601 | 1316 | 27.89% | **-0.00274** |  |
| PANIC | 1193 | 31 | 41.94% | **-0.00268** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00261

- Last 20% Median Exp: -0.00330

- Drop Ratio: -26.30%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
