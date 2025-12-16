# Turbo V3 Verified Result (247540)

## Meta

- Run ID: `verify_turbo_v3_247540_20251215_005312`
- Timestamp (UTC): `2025-12-15T00:53:12Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `247540` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2307, win_rate=0.00%, pnl=None, mdd=0.00%, equity=3100772.487335597

## Key Points

- Total Return: -96.90%
- Max Drawdown: -96.96%
- Trades: 2307
- Final Equity: 3,100,772 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1153

- Win Rate: 25.41%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00020

- **Expectancy (Net)**: **-0.00260**

- Net PnL Total: -2.99408

- SQN Score: -8.11719


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 350 | 7 | 28.57% | **-0.00945** |  |
| TREND_DOWN | 409 | 2 | 0.00% | **-0.00713** |  |
| CHOP_HIGHVOL | 2124 | 12 | 8.33% | **-0.00039** |  |
| CHOP_LOWVOL | 91458 | 1095 | 25.21% | **-0.00255** |  |
| PANIC | 1452 | 37 | 37.84% | **-0.00313** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00269

- Last 20% Median Exp: -0.00220

- Drop Ratio: 18.07%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
