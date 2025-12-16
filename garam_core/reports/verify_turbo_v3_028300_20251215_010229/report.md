# Turbo V3 Verified Result (028300)

## Meta

- Run ID: `verify_turbo_v3_028300_20251215_010229`
- Timestamp (UTC): `2025-12-15T01:02:29Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `028300` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2448, win_rate=0.00%, pnl=None, mdd=0.00%, equity=1791349.672692158

## Key Points

- Total Return: -98.21%
- Max Drawdown: -98.22%
- Trades: 2448
- Final Equity: 1,791,350 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1224

- Win Rate: 27.78%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): -0.00010

- **Expectancy (Net)**: **-0.00290**

- Net PnL Total: -3.54682

- SQN Score: -12.49820


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **NEGATIVE_EDGE**
- **REGIME_MISMATCH**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 108 | 2 | 50.00% | **0.00782** |  |
| TREND_DOWN | 168 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 2895 | 30 | 33.33% | **-0.00481** |  |
| CHOP_LOWVOL | 91205 | 1169 | 27.20% | **-0.00292** |  |
| PANIC | 1317 | 23 | 47.83% | **-0.00012** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00280

- Last 20% Median Exp: -0.00262

- Drop Ratio: 6.69%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
