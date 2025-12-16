# Turbo V3 Verified Result (445680)

## Meta

- Run ID: `verify_turbo_v3_445680_20251215_074852`
- Timestamp (UTC): `2025-12-15T07:48:52Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `445680` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2274, win_rate=0.00%, pnl=None, mdd=0.00%, equity=4466700.970657307

## Key Points

- Total Return: -95.53%
- Max Drawdown: -95.68%
- Trades: 2274
- Final Equity: 4,466,701 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1137

- Win Rate: 31.40%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00077

- **Expectancy (Net)**: **-0.00203**

- Net PnL Total: -2.31059

- SQN Score: -4.32614


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**
- **REGIME_MISMATCH**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 236 | 3 | 33.33% | **-0.01518** |  |
| TREND_DOWN | 142 | 1 | 0.00% | **-0.00397** |  |
| CHOP_HIGHVOL | 9345 | 87 | 20.69% | **-0.00491** |  |
| CHOP_LOWVOL | 75751 | 1018 | 31.34% | **-0.00198** |  |
| PANIC | 1478 | 28 | 67.86% | **0.00644** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00187

- Last 20% Median Exp: -0.00162

- Drop Ratio: 13.36%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
