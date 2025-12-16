# Turbo V3 Verified Result (011780)

## Meta

- Run ID: `verify_turbo_v3_011780_20251215_045334`
- Timestamp (UTC): `2025-12-15T04:53:34Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `011780` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2786, win_rate=0.00%, pnl=None, mdd=0.00%, equity=1673192.324817015

## Key Points

- Total Return: -98.33%
- Max Drawdown: -98.39%
- Trades: 2786
- Final Equity: 1,673,192 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1393

- Win Rate: 31.01%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00016

- **Expectancy (Net)**: **-0.00264**

- Net PnL Total: -3.68438

- SQN Score: -14.56775


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 280 | 3 | 0.00% | **-0.01255** |  |
| TREND_DOWN | 51 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 1331 | 12 | 33.33% | **-0.00032** |  |
| CHOP_LOWVOL | 92801 | 1352 | 30.77% | **-0.00268** |  |
| PANIC | 1330 | 26 | 46.15% | **-0.00095** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00271

- Last 20% Median Exp: -0.00271

- Drop Ratio: -0.07%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
