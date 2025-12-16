# Turbo V3 Verified Result (272210)

## Meta

- Run ID: `verify_turbo_v3_272210_20251215_045104`
- Timestamp (UTC): `2025-12-15T04:51:04Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `272210` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2582, win_rate=0.00%, pnl=None, mdd=0.00%, equity=2973580.5949775768

## Key Points

- Total Return: -97.03%
- Max Drawdown: -97.39%
- Trades: 2582
- Final Equity: 2,973,581 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1291

- Win Rate: 28.81%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00034

- **Expectancy (Net)**: **-0.00246**

- Net PnL Total: -3.17211

- SQN Score: -7.41630


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 204 | 2 | 50.00% | **-0.00467** |  |
| TREND_DOWN | 139 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 11030 | 83 | 33.73% | **-0.00295** |  |
| CHOP_LOWVOL | 83401 | 1186 | 28.16% | **-0.00239** |  |
| PANIC | 1110 | 20 | 45.00% | **-0.00389** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00229

- Last 20% Median Exp: -0.00302

- Drop Ratio: -31.91%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
