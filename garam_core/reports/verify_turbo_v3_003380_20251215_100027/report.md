# Turbo V3 Verified Result (003380)

## Meta

- Run ID: `verify_turbo_v3_003380_20251215_100027`
- Timestamp (UTC): `2025-12-15T10:00:27Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `003380` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2620, win_rate=0.00%, pnl=None, mdd=0.00%, equity=2317040.9801819394

## Key Points

- Total Return: -97.68%
- Max Drawdown: -98.38%
- Trades: 2620
- Final Equity: 2,317,041 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1310

- Win Rate: 25.73%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00033

- **Expectancy (Net)**: **-0.00247**

- Net PnL Total: -3.23819

- SQN Score: -5.92179


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 332 | 2 | 50.00% | **-0.00340** |  |
| TREND_DOWN | 0 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 1269 | 11 | 9.09% | **-0.01117** |  |
| CHOP_LOWVOL | 83217 | 1275 | 25.65% | **-0.00235** |  |
| PANIC | 1212 | 22 | 36.36% | **-0.00481** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00273

- Last 20% Median Exp: -0.00279

- Drop Ratio: -2.04%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
