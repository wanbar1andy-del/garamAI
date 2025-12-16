# Turbo V3 Verified Result (111770)

## Meta

- Run ID: `verify_turbo_v3_111770_20251215_051357`
- Timestamp (UTC): `2025-12-15T05:13:57Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `111770` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=3189, win_rate=0.00%, pnl=None, mdd=0.00%, equity=625937.1019257073

## Key Points

- Total Return: -99.37%
- Max Drawdown: -99.40%
- Trades: 3189
- Final Equity: 625,937 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1594

- Win Rate: 27.85%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): -0.00006

- **Expectancy (Net)**: **-0.00286**

- Net PnL Total: -4.56639

- SQN Score: -18.26219


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **NEGATIVE_EDGE**
- **REGIME_MISMATCH**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 27 | 0 | 0.00% | **0.00000** |  |
| TREND_DOWN | 129 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 2242 | 33 | 45.45% | **0.00175** |  |
| CHOP_LOWVOL | 90940 | 1536 | 27.28% | **-0.00296** |  |
| PANIC | 1341 | 25 | 40.00% | **-0.00323** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00298

- Last 20% Median Exp: -0.00289

- Drop Ratio: 2.94%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
