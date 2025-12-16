# Turbo V3 Verified Result (012750)

## Meta

- Run ID: `verify_turbo_v3_012750_20251215_043532`
- Timestamp (UTC): `2025-12-15T04:35:32Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `012750` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=3392, win_rate=0.00%, pnl=None, mdd=0.00%, equity=262699.1079310912

## Key Points

- Total Return: -99.74%
- Max Drawdown: -99.74%
- Trades: 3392
- Final Equity: 262,699 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1696

- Win Rate: 25.41%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): -0.00043

- **Expectancy (Net)**: **-0.00323**

- Net PnL Total: -5.47236

- SQN Score: -35.67322


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **NEGATIVE_EDGE**
- **REGIME_MISMATCH**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 17 | 0 | 0.00% | **0.00000** |  |
| TREND_DOWN | 108 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 418 | 4 | 0.00% | **-0.00526** |  |
| CHOP_LOWVOL | 88747 | 1654 | 25.33% | **-0.00318** |  |
| PANIC | 1340 | 38 | 31.58% | **-0.00495** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00313

- Last 20% Median Exp: -0.00346

- Drop Ratio: -10.41%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
