# Turbo V3 Verified Result (042700)

## Meta

- Run ID: `verify_turbo_v3_042700_20251215_013335`
- Timestamp (UTC): `2025-12-15T01:33:35Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `042700` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2387, win_rate=0.00%, pnl=None, mdd=0.00%, equity=5122705.487317735

## Key Points

- Total Return: -94.88%
- Max Drawdown: -94.95%
- Trades: 2387
- Final Equity: 5,122,705 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1193

- Win Rate: 26.82%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00053

- **Expectancy (Net)**: **-0.00227**

- Net PnL Total: -2.71135

- SQN Score: -6.56794


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 268 | 3 | 66.67% | **0.01379** |  |
| TREND_DOWN | 716 | 1 | 0.00% | **-0.00280** |  |
| CHOP_HIGHVOL | 2884 | 16 | 25.00% | **-0.00118** |  |
| CHOP_LOWVOL | 90828 | 1154 | 26.69% | **-0.00228** |  |
| PANIC | 1181 | 19 | 31.58% | **-0.00530** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00247

- Last 20% Median Exp: -0.00187

- Drop Ratio: 24.38%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
