# Turbo V3 Verified Result (004800)

## Meta

- Run ID: `verify_turbo_v3_004800_20251215_072001`
- Timestamp (UTC): `2025-12-15T07:20:01Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `004800` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2545, win_rate=0.00%, pnl=None, mdd=0.00%, equity=2745674.414974981

## Key Points

- Total Return: -97.25%
- Max Drawdown: -97.36%
- Trades: 2545
- Final Equity: 2,745,674 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1272

- Win Rate: 29.40%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00031

- **Expectancy (Net)**: **-0.00249**

- Net PnL Total: -3.16800

- SQN Score: -9.78346


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 294 | 3 | 0.00% | **-0.02095** |  |
| TREND_DOWN | 325 | 1 | 0.00% | **-0.00651** |  |
| CHOP_HIGHVOL | 2093 | 15 | 33.33% | **-0.00361** |  |
| CHOP_LOWVOL | 82995 | 1230 | 29.19% | **-0.00246** |  |
| PANIC | 1485 | 23 | 43.48% | **-0.00073** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00291

- Last 20% Median Exp: -0.00156

- Drop Ratio: 46.55%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
