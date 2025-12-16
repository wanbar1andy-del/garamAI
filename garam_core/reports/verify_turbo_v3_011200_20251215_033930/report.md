# Turbo V3 Verified Result (011200)

## Meta

- Run ID: `verify_turbo_v3_011200_20251215_033930`
- Timestamp (UTC): `2025-12-15T03:39:30Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `011200` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2942, win_rate=0.00%, pnl=None, mdd=0.00%, equity=1134501.6951352346

## Key Points

- Total Return: -98.87%
- Max Drawdown: -98.90%
- Trades: 2942
- Final Equity: 1,134,502 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1471

- Win Rate: 26.65%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00001

- **Expectancy (Net)**: **-0.00279**

- Net PnL Total: -4.10417

- SQN Score: -17.05570


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 421 | 6 | 66.67% | **0.01063** |  |
| TREND_DOWN | 53 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 3026 | 33 | 24.24% | **-0.00362** |  |
| CHOP_LOWVOL | 91448 | 1408 | 26.35% | **-0.00285** |  |
| PANIC | 945 | 24 | 37.50% | **-0.00156** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00299

- Last 20% Median Exp: -0.00260

- Drop Ratio: 12.89%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
