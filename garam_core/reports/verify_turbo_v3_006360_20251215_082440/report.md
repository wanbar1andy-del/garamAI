# Turbo V3 Verified Result (006360)

## Meta

- Run ID: `verify_turbo_v3_006360_20251215_082440`
- Timestamp (UTC): `2025-12-15T08:24:40Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `006360` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2616, win_rate=0.00%, pnl=None, mdd=0.00%, equity=1920466.8675983085

## Key Points

- Total Return: -98.08%
- Max Drawdown: -98.14%
- Trades: 2616
- Final Equity: 1,920,467 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1308

- Win Rate: 29.82%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00013

- **Expectancy (Net)**: **-0.00267**

- Net PnL Total: -3.49559

- SQN Score: -17.73188


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 321 | 2 | 100.00% | **0.00733** |  |
| TREND_DOWN | 115 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 2327 | 30 | 16.67% | **-0.00223** |  |
| CHOP_LOWVOL | 91521 | 1243 | 29.77% | **-0.00272** |  |
| PANIC | 1467 | 33 | 39.39% | **-0.00181** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00286

- Last 20% Median Exp: -0.00269

- Drop Ratio: 5.73%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
