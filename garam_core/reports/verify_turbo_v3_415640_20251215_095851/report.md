# Turbo V3 Verified Result (415640)

## Meta

- Run ID: `verify_turbo_v3_415640_20251215_095851`
- Timestamp (UTC): `2025-12-15T09:58:51Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `415640` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2802, win_rate=0.00%, pnl=None, mdd=0.00%, equity=699948.8210446868

## Key Points

- Total Return: -99.30%
- Max Drawdown: -99.30%
- Trades: 2802
- Final Equity: 699,949 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1401

- Win Rate: 21.84%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): -0.00052

- **Expectancy (Net)**: **-0.00332**

- Net PnL Total: -4.64887

- SQN Score: -31.58896


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **NEGATIVE_EDGE**
- **REGIME_MISMATCH**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 238 | 2 | 0.00% | **-0.00893** |  |
| TREND_DOWN | 134 | 2 | 0.00% | **-0.00280** |  |
| CHOP_HIGHVOL | 110 | 1 | 100.00% | **-0.00039** |  |
| CHOP_LOWVOL | 72638 | 1357 | 21.67% | **-0.00326** |  |
| PANIC | 1534 | 39 | 28.21% | **-0.00510** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00321

- Last 20% Median Exp: -0.00345

- Drop Ratio: -7.45%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
