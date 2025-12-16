# Turbo V3 Verified Result (036570)

## Meta

- Run ID: `verify_turbo_v3_036570_20251215_034023`
- Timestamp (UTC): `2025-12-15T03:40:23Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `036570` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2720, win_rate=0.00%, pnl=None, mdd=0.00%, equity=1628566.1565934597

## Key Points

- Total Return: -98.37%
- Max Drawdown: -98.37%
- Trades: 2720
- Final Equity: 1,628,566 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1360

- Win Rate: 29.12%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00008

- **Expectancy (Net)**: **-0.00272**

- Net PnL Total: -3.69707

- SQN Score: -11.74923


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**
- **REGIME_MISMATCH**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 153 | 0 | 0.00% | **0.00000** |  |
| TREND_DOWN | 411 | 2 | 0.00% | **-0.00596** |  |
| CHOP_HIGHVOL | 2704 | 27 | 29.63% | **-0.00195** |  |
| CHOP_LOWVOL | 91236 | 1298 | 28.66% | **-0.00280** |  |
| PANIC | 1244 | 33 | 48.48% | **0.00006** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00272

- Last 20% Median Exp: -0.00259

- Drop Ratio: 4.64%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
