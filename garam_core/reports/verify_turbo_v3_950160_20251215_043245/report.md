# Turbo V3 Verified Result (950160)

## Meta

- Run ID: `verify_turbo_v3_950160_20251215_043245`
- Timestamp (UTC): `2025-12-15T04:32:45Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `950160` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2442, win_rate=0.00%, pnl=None, mdd=0.00%, equity=4535839.252853794

## Key Points

- Total Return: -95.46%
- Max Drawdown: -95.88%
- Trades: 2442
- Final Equity: 4,535,839 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1221

- Win Rate: 29.07%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00064

- **Expectancy (Net)**: **-0.00216**

- Net PnL Total: -2.63928

- SQN Score: -4.97043


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**
- **REGIME_MISMATCH**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 101 | 0 | 0.00% | **0.00000** |  |
| TREND_DOWN | 3 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 15888 | 169 | 26.63% | **-0.00409** |  |
| CHOP_LOWVOL | 77173 | 1030 | 29.42% | **-0.00191** |  |
| PANIC | 1649 | 22 | 31.82% | **0.00077** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00237

- Last 20% Median Exp: -0.00179

- Drop Ratio: 24.55%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
