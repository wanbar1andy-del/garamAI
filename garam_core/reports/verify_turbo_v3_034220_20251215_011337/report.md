# Turbo V3 Verified Result (034220)

## Meta

- Run ID: `verify_turbo_v3_034220_20251215_011337`
- Timestamp (UTC): `2025-12-15T01:13:37Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `034220` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2633, win_rate=0.00%, pnl=None, mdd=0.00%, equity=2548946.3371479292

## Key Points

- Total Return: -97.45%
- Max Drawdown: -97.56%
- Trades: 2633
- Final Equity: 2,548,946 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1316

- Win Rate: 26.44%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00036

- **Expectancy (Net)**: **-0.00244**

- Net PnL Total: -3.21005

- SQN Score: -10.28492


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 465 | 3 | 0.00% | **-0.01045** |  |
| TREND_DOWN | 193 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 502 | 2 | 50.00% | **0.00558** |  |
| CHOP_LOWVOL | 93487 | 1286 | 26.36% | **-0.00243** |  |
| PANIC | 1089 | 25 | 32.00% | **-0.00271** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00250

- Last 20% Median Exp: -0.00206

- Drop Ratio: 17.70%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
