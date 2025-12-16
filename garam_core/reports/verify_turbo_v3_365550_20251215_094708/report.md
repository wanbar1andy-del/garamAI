# Turbo V3 Verified Result (365550)

## Meta

- Run ID: `verify_turbo_v3_365550_20251215_094708`
- Timestamp (UTC): `2025-12-15T09:47:08Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `365550` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=3312, win_rate=0.00%, pnl=None, mdd=0.00%, equity=425717.0751037361

## Key Points

- Total Return: -99.57%
- Max Drawdown: -99.59%
- Trades: 3312
- Final Equity: 425,717 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1656

- Win Rate: 26.33%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): -0.00026

- **Expectancy (Net)**: **-0.00306**

- Net PnL Total: -5.06426

- SQN Score: -35.64700


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 47 | 0 | 0.00% | **0.00000** |  |
| TREND_DOWN | 5 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 229 | 4 | 50.00% | **-0.00190** |  |
| CHOP_LOWVOL | 89633 | 1625 | 26.15% | **-0.00304** |  |
| PANIC | 1652 | 27 | 33.33% | **-0.00445** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00304

- Last 20% Median Exp: -0.00317

- Drop Ratio: -4.31%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
