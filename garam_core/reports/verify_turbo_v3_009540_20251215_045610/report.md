# Turbo V3 Verified Result (009540)

## Meta

- Run ID: `verify_turbo_v3_009540_20251215_045610`
- Timestamp (UTC): `2025-12-15T04:56:10Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `009540` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2926, win_rate=0.00%, pnl=None, mdd=0.00%, equity=929926.6130730862

## Key Points

- Total Return: -99.07%
- Max Drawdown: -99.08%
- Trades: 2926
- Final Equity: 929,927 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1463

- Win Rate: 27.55%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): -0.00010

- **Expectancy (Net)**: **-0.00290**

- Net PnL Total: -4.23786

- SQN Score: -15.82417


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 59 | 1 | 0.00% | **-0.01063** |  |
| TREND_DOWN | 102 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 3134 | 23 | 34.78% | **0.00038** |  |
| CHOP_LOWVOL | 91618 | 1415 | 27.35% | **-0.00296** |  |
| PANIC | 981 | 24 | 33.33% | **-0.00207** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00283

- Last 20% Median Exp: -0.00320

- Drop Ratio: -12.94%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
