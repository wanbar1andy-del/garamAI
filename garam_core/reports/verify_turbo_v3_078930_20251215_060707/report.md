# Turbo V3 Verified Result (078930)

## Meta

- Run ID: `verify_turbo_v3_078930_20251215_060707`
- Timestamp (UTC): `2025-12-15T06:07:07Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `078930` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=3295, win_rate=0.00%, pnl=None, mdd=0.00%, equity=778519.2259606719

## Key Points

- Total Return: -99.22%
- Max Drawdown: -99.23%
- Trades: 3295
- Final Equity: 778,519 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1647

- Win Rate: 26.17%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00013

- **Expectancy (Net)**: **-0.00267**

- Net PnL Total: -4.39292

- SQN Score: -18.42659


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 258 | 1 | 100.00% | **0.02048** |  |
| TREND_DOWN | 126 | 1 | 0.00% | **-0.00541** |  |
| CHOP_HIGHVOL | 905 | 11 | 36.36% | **-0.00227** |  |
| CHOP_LOWVOL | 93567 | 1613 | 25.98% | **-0.00270** |  |
| PANIC | 836 | 21 | 33.33% | **-0.00150** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00281

- Last 20% Median Exp: -0.00230

- Drop Ratio: 18.17%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
