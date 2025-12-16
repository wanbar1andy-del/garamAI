# Turbo V3 Verified Result (000660)

## Meta

- Run ID: `verify_turbo_v3_000660_20251215_005309`
- Timestamp (UTC): `2025-12-15T00:53:09Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `000660` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2741, win_rate=0.00%, pnl=None, mdd=0.00%, equity=1801760.6917718272

## Key Points

- Total Return: -98.20%
- Max Drawdown: -98.23%
- Trades: 2741
- Final Equity: 1,801,761 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1370

- Win Rate: 29.71%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00015

- **Expectancy (Net)**: **-0.00265**

- Net PnL Total: -3.62665

- SQN Score: -10.49408


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 732 | 5 | 20.00% | **-0.00100** |  |
| TREND_DOWN | 472 | 1 | 0.00% | **-0.00280** |  |
| CHOP_HIGHVOL | 1121 | 13 | 30.77% | **0.00062** |  |
| CHOP_LOWVOL | 92543 | 1331 | 29.83% | **-0.00270** |  |
| PANIC | 940 | 20 | 25.00% | **-0.00153** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00303

- Last 20% Median Exp: -0.00168

- Drop Ratio: 44.36%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
