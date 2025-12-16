# Turbo V3 Verified Result (000990)

## Meta

- Run ID: `verify_turbo_v3_000990_20251215_045846`
- Timestamp (UTC): `2025-12-15T04:58:46Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `000990` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2792, win_rate=0.00%, pnl=None, mdd=0.00%, equity=1245590.4524276308

## Key Points

- Total Return: -98.75%
- Max Drawdown: -98.79%
- Trades: 2792
- Final Equity: 1,245,590 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1396

- Win Rate: 27.22%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): -0.00006

- **Expectancy (Net)**: **-0.00286**

- Net PnL Total: -3.99316

- SQN Score: -10.80387


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **NEGATIVE_EDGE**
- **REGIME_MISMATCH**
- **STRUCTURAL_BREAK**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 195 | 1 | 0.00% | **-0.01846** |  |
| TREND_DOWN | 42 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 3397 | 39 | 35.90% | **-0.00264** |  |
| CHOP_LOWVOL | 90500 | 1325 | 26.94% | **-0.00279** |  |
| PANIC | 1212 | 31 | 29.03% | **-0.00558** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00252

- Last 20% Median Exp: -0.00384

- Drop Ratio: -52.47%

- **Structural Break**: **YES**

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
