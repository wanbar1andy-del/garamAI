# Turbo V3 Verified Result (017670)

## Meta

- Run ID: `verify_turbo_v3_017670_20251215_012333`
- Timestamp (UTC): `2025-12-15T01:23:33Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `017670` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=4274, win_rate=0.00%, pnl=None, mdd=0.00%, equity=107692.07099874373

## Key Points

- Total Return: -99.89%
- Max Drawdown: -99.89%
- Trades: 4274
- Final Equity: 107,692 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 2137

- Win Rate: 24.52%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): -0.00013

- **Expectancy (Net)**: **-0.00293**

- Net PnL Total: -6.25400

- SQN Score: -60.26193


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 0 | 0 | 0.00% | **0.00000** |  |
| TREND_DOWN | 51 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 173 | 1 | 0.00% | **-0.00465** |  |
| CHOP_LOWVOL | 95227 | 2126 | 24.46% | **-0.00293** |  |
| PANIC | 436 | 10 | 40.00% | **-0.00164** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00293

- Last 20% Median Exp: -0.00291

- Drop Ratio: 0.53%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
