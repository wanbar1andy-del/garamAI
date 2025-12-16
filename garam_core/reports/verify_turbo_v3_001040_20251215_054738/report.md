# Turbo V3 Verified Result (001040)

## Meta

- Run ID: `verify_turbo_v3_001040_20251215_054738`
- Timestamp (UTC): `2025-12-15T05:47:38Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `001040` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2487, win_rate=0.00%, pnl=None, mdd=0.00%, equity=3531444.1275630053

## Key Points

- Total Return: -96.47%
- Max Drawdown: -96.47%
- Trades: 2487
- Final Equity: 3,531,444 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1243

- Win Rate: 32.34%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00060

- **Expectancy (Net)**: **-0.00220**

- Net PnL Total: -2.73303

- SQN Score: -7.20867


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**
- **REGIME_MISMATCH**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 335 | 2 | 50.00% | **-0.00031** |  |
| TREND_DOWN | 86 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 4928 | 53 | 37.74% | **-0.00302** |  |
| CHOP_LOWVOL | 89017 | 1155 | 31.86% | **-0.00221** |  |
| PANIC | 1464 | 33 | 39.39% | **-0.00077** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00202

- Last 20% Median Exp: -0.00278

- Drop Ratio: -37.50%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
