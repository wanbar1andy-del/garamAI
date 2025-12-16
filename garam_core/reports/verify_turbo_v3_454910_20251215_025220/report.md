# Turbo V3 Verified Result (454910)

## Meta

- Run ID: `verify_turbo_v3_454910_20251215_025220`
- Timestamp (UTC): `2025-12-15T02:52:20Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `454910` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2768, win_rate=0.00%, pnl=None, mdd=0.00%, equity=1441073.3547683298

## Key Points

- Total Return: -98.56%
- Max Drawdown: -98.61%
- Trades: 2768
- Final Equity: 1,441,073 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1384

- Win Rate: 23.27%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00007

- **Expectancy (Net)**: **-0.00273**

- Net PnL Total: -3.77536

- SQN Score: -8.89771


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 239 | 0 | 0.00% | **0.00000** |  |
| TREND_DOWN | 312 | 1 | 0.00% | **-0.00487** |  |
| CHOP_HIGHVOL | 3340 | 27 | 22.22% | **-0.00242** |  |
| CHOP_LOWVOL | 90856 | 1342 | 23.25% | **-0.00274** |  |
| PANIC | 929 | 14 | 28.57% | **-0.00220** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00271

- Last 20% Median Exp: -0.00261

- Drop Ratio: 3.78%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
