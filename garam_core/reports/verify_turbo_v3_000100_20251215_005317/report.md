# Turbo V3 Verified Result (000100)

## Meta

- Run ID: `verify_turbo_v3_000100_20251215_005317`
- Timestamp (UTC): `2025-12-15T00:53:17Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `000100` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2533, win_rate=0.00%, pnl=None, mdd=0.00%, equity=1594101.2865881077

## Key Points

- Total Return: -98.41%
- Max Drawdown: -98.43%
- Trades: 2533
- Final Equity: 1,594,101 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1266

- Win Rate: 26.62%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): -0.00013

- **Expectancy (Net)**: **-0.00293**

- Net PnL Total: -3.70387

- SQN Score: -14.19554


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 191 | 2 | 50.00% | **0.00825** |  |
| TREND_DOWN | 100 | 1 | 100.00% | **-0.00199** |  |
| CHOP_HIGHVOL | 641 | 2 | 100.00% | **0.00885** |  |
| CHOP_LOWVOL | 93573 | 1237 | 26.43% | **-0.00296** |  |
| PANIC | 1298 | 24 | 25.00% | **-0.00287** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00309

- Last 20% Median Exp: -0.00293

- Drop Ratio: 5.13%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
