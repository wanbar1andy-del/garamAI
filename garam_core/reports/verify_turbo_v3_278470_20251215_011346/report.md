# Turbo V3 Verified Result (278470)

## Meta

- Run ID: `verify_turbo_v3_278470_20251215_011346`
- Timestamp (UTC): `2025-12-15T01:13:46Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `278470` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2750, win_rate=0.00%, pnl=None, mdd=0.00%, equity=1514319.1822185155

## Key Points

- Total Return: -98.49%
- Max Drawdown: -98.59%
- Trades: 2750
- Final Equity: 1,514,319 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1375

- Win Rate: 28.07%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00020

- **Expectancy (Net)**: **-0.00260**

- Net PnL Total: -3.57138

- SQN Score: -8.78205


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 134 | 1 | 100.00% | **0.02090** |  |
| TREND_DOWN | 224 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 11193 | 121 | 29.75% | **-0.00369** |  |
| CHOP_LOWVOL | 83028 | 1228 | 27.44% | **-0.00249** |  |
| PANIC | 1213 | 25 | 48.00% | **-0.00348** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00276

- Last 20% Median Exp: -0.00219

- Drop Ratio: 20.73%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
