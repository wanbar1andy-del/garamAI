# Turbo V3 Verified Result (029780)

## Meta

- Run ID: `verify_turbo_v3_029780_20251215_031928`
- Timestamp (UTC): `2025-12-15T03:19:28Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `029780` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=3726, win_rate=0.00%, pnl=None, mdd=0.00%, equity=215703.99101566226

## Key Points

- Total Return: -99.78%
- Max Drawdown: -99.79%
- Trades: 3726
- Final Equity: 215,704 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1863

- Win Rate: 26.84%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): -0.00018

- **Expectancy (Net)**: **-0.00298**

- Net PnL Total: -5.55550

- SQN Score: -33.32911


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 82 | 0 | 0.00% | **0.00000** |  |
| TREND_DOWN | 164 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 919 | 15 | 40.00% | **-0.00391** |  |
| CHOP_LOWVOL | 92407 | 1827 | 26.49% | **-0.00302** |  |
| PANIC | 1094 | 21 | 47.62% | **0.00118** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00304

- Last 20% Median Exp: -0.00311

- Drop Ratio: -2.27%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
