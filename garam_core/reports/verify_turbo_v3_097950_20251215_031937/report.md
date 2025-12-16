# Turbo V3 Verified Result (097950)

## Meta

- Run ID: `verify_turbo_v3_097950_20251215_031937`
- Timestamp (UTC): `2025-12-15T03:19:37Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `097950` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=3706, win_rate=0.00%, pnl=None, mdd=0.00%, equity=278638.74640666094

## Key Points

- Total Return: -99.72%
- Max Drawdown: -99.72%
- Trades: 3706
- Final Equity: 278,639 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1853

- Win Rate: 25.96%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): -0.00005

- **Expectancy (Net)**: **-0.00285**

- Net PnL Total: -5.27772

- SQN Score: -34.12847


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 3 | 0 | 0.00% | **0.00000** |  |
| TREND_DOWN | 107 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 53 | 1 | 0.00% | **-0.01737** |  |
| CHOP_LOWVOL | 94864 | 1841 | 25.91% | **-0.00284** |  |
| PANIC | 514 | 11 | 36.36% | **-0.00320** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00285

- Last 20% Median Exp: -0.00290

- Drop Ratio: -1.91%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
