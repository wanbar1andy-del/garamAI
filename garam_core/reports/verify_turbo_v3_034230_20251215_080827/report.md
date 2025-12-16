# Turbo V3 Verified Result (034230)

## Meta

- Run ID: `verify_turbo_v3_034230_20251215_080827`
- Timestamp (UTC): `2025-12-15T08:08:27Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `034230` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2642, win_rate=0.00%, pnl=None, mdd=0.00%, equity=2401636.188407022

## Key Points

- Total Return: -97.60%
- Max Drawdown: -97.62%
- Trades: 2642
- Final Equity: 2,401,636 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1321

- Win Rate: 29.30%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00026

- **Expectancy (Net)**: **-0.00254**

- Net PnL Total: -3.34981

- SQN Score: -11.67325


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**
- **REGIME_MISMATCH**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 193 | 1 | 100.00% | **0.01123** |  |
| TREND_DOWN | 228 | 1 | 0.00% | **-0.00625** |  |
| CHOP_HIGHVOL | 4379 | 54 | 27.78% | **-0.00510** |  |
| CHOP_LOWVOL | 88392 | 1243 | 28.96% | **-0.00245** |  |
| PANIC | 1527 | 22 | 50.00% | **-0.00183** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00220

- Last 20% Median Exp: -0.00301

- Drop Ratio: -37.25%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
