# Turbo V3 Verified Result (251270)

## Meta

- Run ID: `verify_turbo_v3_251270_20251215_060913`
- Timestamp (UTC): `2025-12-15T06:09:13Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `251270` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2930, win_rate=0.00%, pnl=None, mdd=0.00%, equity=842069.2292244125

## Key Points

- Total Return: -99.16%
- Max Drawdown: -99.17%
- Trades: 2930
- Final Equity: 842,069 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1465

- Win Rate: 26.89%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): -0.00026

- **Expectancy (Net)**: **-0.00306**

- Net PnL Total: -4.48809

- SQN Score: -19.84187


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 21 | 1 | 100.00% | **0.02498** |  |
| TREND_DOWN | 37 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 3181 | 34 | 47.06% | **-0.00211** |  |
| CHOP_LOWVOL | 91144 | 1410 | 26.38% | **-0.00308** |  |
| PANIC | 977 | 20 | 25.00% | **-0.00485** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00296

- Last 20% Median Exp: -0.00309

- Drop Ratio: -4.40%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
