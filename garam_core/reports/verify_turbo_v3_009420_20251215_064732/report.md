# Turbo V3 Verified Result (009420)

## Meta

- Run ID: `verify_turbo_v3_009420_20251215_064732`
- Timestamp (UTC): `2025-12-15T06:47:32Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `009420` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2764, win_rate=0.00%, pnl=None, mdd=0.00%, equity=1008324.9968147314

## Key Points

- Total Return: -98.99%
- Max Drawdown: -99.05%
- Trades: 2764
- Final Equity: 1,008,325 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1382

- Win Rate: 25.90%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): -0.00021

- **Expectancy (Net)**: **-0.00301**

- Net PnL Total: -4.16198

- SQN Score: -11.78701


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **NEGATIVE_EDGE**
- **REGIME_MISMATCH**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 167 | 1 | 100.00% | **0.02142** |  |
| TREND_DOWN | 46 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 4937 | 52 | 30.77% | **-0.00044** |  |
| CHOP_LOWVOL | 89269 | 1304 | 25.54% | **-0.00312** |  |
| PANIC | 1087 | 25 | 32.00% | **-0.00359** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00313

- Last 20% Median Exp: -0.00273

- Drop Ratio: 12.98%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
