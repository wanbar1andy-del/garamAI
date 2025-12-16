# Turbo V3 Verified Result (000150)

## Meta

- Run ID: `verify_turbo_v3_000150_20251215_051557`
- Timestamp (UTC): `2025-12-15T05:15:57Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `000150` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2635, win_rate=0.00%, pnl=None, mdd=0.00%, equity=4307931.424166061

## Key Points

- Total Return: -95.69%
- Max Drawdown: -95.94%
- Trades: 2635
- Final Equity: 4,307,931 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1317

- Win Rate: 30.75%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00068

- **Expectancy (Net)**: **-0.00212**

- Net PnL Total: -2.78738

- SQN Score: -6.20835


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 261 | 2 | 50.00% | **-0.00755** |  |
| TREND_DOWN | 245 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 17478 | 184 | 41.85% | **-0.00163** |  |
| CHOP_LOWVOL | 76790 | 1105 | 29.32% | **-0.00197** |  |
| PANIC | 1083 | 26 | 11.54% | **-0.01123** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00250

- Last 20% Median Exp: -0.00181

- Drop Ratio: 27.87%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
