# Turbo V3 Verified Result (090430)

## Meta

- Run ID: `verify_turbo_v3_090430_20251215_061708`
- Timestamp (UTC): `2025-12-15T06:17:08Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `090430` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2672, win_rate=0.00%, pnl=None, mdd=0.00%, equity=1287059.7091736181

## Key Points

- Total Return: -98.71%
- Max Drawdown: -98.75%
- Trades: 2672
- Final Equity: 1,287,060 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1336

- Win Rate: 28.52%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): -0.00015

- **Expectancy (Net)**: **-0.00295**

- Net PnL Total: -3.93612

- SQN Score: -20.03454


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 312 | 5 | 100.00% | **0.01255** |  |
| TREND_DOWN | 157 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 158 | 0 | 0.00% | **0.00000** |  |
| CHOP_LOWVOL | 94028 | 1301 | 27.98% | **-0.00302** |  |
| PANIC | 1229 | 30 | 40.00% | **-0.00248** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00301

- Last 20% Median Exp: -0.00278

- Drop Ratio: 7.65%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
