# Turbo V3 Verified Result (065350)

## Meta

- Run ID: `verify_turbo_v3_065350_20251215_084309`
- Timestamp (UTC): `2025-12-15T08:43:09Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `065350` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2467, win_rate=0.00%, pnl=None, mdd=0.00%, equity=1883116.6916525727

## Key Points

- Total Return: -98.12%
- Max Drawdown: -98.45%
- Trades: 2467
- Final Equity: 1,883,117 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1233

- Win Rate: 22.63%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): -0.00003

- **Expectancy (Net)**: **-0.00283**

- Net PnL Total: -3.49151

- SQN Score: -7.36037


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **NEGATIVE_EDGE**
- **REGIME_MISMATCH**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 198 | 1 | 0.00% | **-0.02307** |  |
| TREND_DOWN | 9 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 7369 | 76 | 31.58% | **-0.00518** |  |
| CHOP_LOWVOL | 84295 | 1135 | 21.76% | **-0.00265** |  |
| PANIC | 1286 | 21 | 38.10% | **-0.00347** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00346

- Last 20% Median Exp: -0.00216

- Drop Ratio: 37.42%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
