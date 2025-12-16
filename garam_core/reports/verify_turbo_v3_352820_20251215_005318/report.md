# Turbo V3 Verified Result (352820)

## Meta

- Run ID: `verify_turbo_v3_352820_20251215_005318`
- Timestamp (UTC): `2025-12-15T00:53:18Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `352820` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=3242, win_rate=0.00%, pnl=None, mdd=0.00%, equity=675274.2626759233

## Key Points

- Total Return: -99.32%
- Max Drawdown: -99.32%
- Trades: 3242
- Final Equity: 675,274 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1621

- Win Rate: 26.77%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): -0.00000

- **Expectancy (Net)**: **-0.00280**

- Net PnL Total: -4.53976

- SQN Score: -18.52415


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 185 | 3 | 33.33% | **-0.00861** |  |
| TREND_DOWN | 11 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 1824 | 15 | 40.00% | **-0.00198** |  |
| CHOP_LOWVOL | 92958 | 1586 | 26.67% | **-0.00279** |  |
| PANIC | 827 | 17 | 23.53% | **-0.00384** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00282

- Last 20% Median Exp: -0.00309

- Drop Ratio: -9.63%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
