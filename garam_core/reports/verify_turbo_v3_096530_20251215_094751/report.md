# Turbo V3 Verified Result (096530)

## Meta

- Run ID: `verify_turbo_v3_096530_20251215_094751`
- Timestamp (UTC): `2025-12-15T09:47:51Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `096530` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=3198, win_rate=0.00%, pnl=None, mdd=0.00%, equity=591964.1322183665

## Key Points

- Total Return: -99.41%
- Max Drawdown: -99.42%
- Trades: 3198
- Final Equity: 591,964 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1599

- Win Rate: 24.64%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): -0.00010

- **Expectancy (Net)**: **-0.00290**

- Net PnL Total: -4.64361

- SQN Score: -17.53044


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 3 | 0 | 0.00% | **0.00000** |  |
| TREND_DOWN | 1 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 3545 | 40 | 30.00% | **-0.00381** |  |
| CHOP_LOWVOL | 89408 | 1541 | 24.08% | **-0.00304** |  |
| PANIC | 873 | 18 | 61.11% | **0.01077** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00319

- Last 20% Median Exp: -0.00256

- Drop Ratio: 19.72%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
