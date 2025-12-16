# Turbo V3 Verified Result (003490)

## Meta

- Run ID: `verify_turbo_v3_003490_20251215_055730`
- Timestamp (UTC): `2025-12-15T05:57:30Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `003490` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=3895, win_rate=0.00%, pnl=None, mdd=0.00%, equity=173157.74957783232

## Key Points

- Total Return: -99.83%
- Max Drawdown: -99.83%
- Trades: 3895
- Final Equity: 173,158 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1947

- Win Rate: 24.45%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): -0.00016

- **Expectancy (Net)**: **-0.00296**

- Net PnL Total: -5.76245

- SQN Score: -37.70137


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 60 | 1 | 100.00% | **0.00607** |  |
| TREND_DOWN | 0 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 328 | 0 | 0.00% | **0.00000** |  |
| CHOP_LOWVOL | 95070 | 1933 | 24.42% | **-0.00296** |  |
| PANIC | 435 | 13 | 23.08% | **-0.00433** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00296

- Last 20% Median Exp: -0.00304

- Drop Ratio: -2.78%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
