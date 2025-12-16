# Turbo V3 Verified Result (000815)

## Meta

- Run ID: `verify_turbo_v3_000815_20251215_100301`
- Timestamp (UTC): `2025-12-15T10:03:01Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `000815` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=3408, win_rate=0.00%, pnl=None, mdd=0.00%, equity=462327.9252764876

## Key Points

- Total Return: -99.54%
- Max Drawdown: -99.55%
- Trades: 3408
- Final Equity: 462,328 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1704

- Win Rate: 28.17%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): -0.00005

- **Expectancy (Net)**: **-0.00285**

- Net PnL Total: -4.85954

- SQN Score: -26.66869


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 10 | 0 | 0.00% | **0.00000** |  |
| TREND_DOWN | 19 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 144 | 1 | 100.00% | **-0.00113** |  |
| CHOP_LOWVOL | 84404 | 1674 | 28.08% | **-0.00284** |  |
| PANIC | 1084 | 29 | 31.03% | **-0.00342** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00280

- Last 20% Median Exp: -0.00284

- Drop Ratio: -1.54%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
