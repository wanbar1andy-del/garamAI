# Turbo V3 Verified Result (060370)

## Meta

- Run ID: `verify_turbo_v3_060370_20251215_082307`
- Timestamp (UTC): `2025-12-15T08:23:07Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `060370` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2727, win_rate=0.00%, pnl=None, mdd=0.00%, equity=1398999.3519539793

## Key Points

- Total Return: -98.60%
- Max Drawdown: -98.74%
- Trades: 2727
- Final Equity: 1,398,999 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1363

- Win Rate: 28.91%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): -0.00017

- **Expectancy (Net)**: **-0.00297**

- Net PnL Total: -4.04965

- SQN Score: -10.04997


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **NEGATIVE_EDGE**
- **REGIME_MISMATCH**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 123 | 4 | 25.00% | **-0.00692** |  |
| TREND_DOWN | 86 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 7787 | 95 | 28.42% | **-0.00083** |  |
| CHOP_LOWVOL | 81573 | 1236 | 28.56% | **-0.00311** |  |
| PANIC | 1361 | 28 | 46.43% | **-0.00358** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00330

- Last 20% Median Exp: -0.00309

- Drop Ratio: 6.62%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
