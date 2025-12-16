# Turbo V3 Verified Result (051910)

## Meta

- Run ID: `verify_turbo_v3_051910_20251215_082732`
- Timestamp (UTC): `2025-12-15T08:27:32Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `051910` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2858, win_rate=0.00%, pnl=None, mdd=0.00%, equity=1052664.5111588533

## Key Points

- Total Return: -98.95%
- Max Drawdown: -98.96%
- Trades: 2858
- Final Equity: 1,052,665 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1429

- Win Rate: 26.03%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): -0.00005

- **Expectancy (Net)**: **-0.00285**

- Net PnL Total: -4.07971

- SQN Score: -13.25956


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 128 | 1 | 100.00% | **0.02963** |  |
| TREND_DOWN | 175 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 1642 | 12 | 33.33% | **-0.00477** |  |
| CHOP_LOWVOL | 93046 | 1397 | 25.84% | **-0.00290** |  |
| PANIC | 899 | 19 | 31.58% | **-0.00006** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00263

- Last 20% Median Exp: -0.00265

- Drop Ratio: -0.99%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
