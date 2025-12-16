# Turbo V3 Verified Result (160190)

## Meta

- Run ID: `verify_turbo_v3_160190_20251215_080351`
- Timestamp (UTC): `2025-12-15T08:03:51Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `160190` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2401, win_rate=0.00%, pnl=None, mdd=0.00%, equity=1631941.8728707256

## Key Points

- Total Return: -98.37%
- Max Drawdown: -98.45%
- Trades: 2401
- Final Equity: 1,631,942 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1200

- Win Rate: 26.50%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): -0.00020

- **Expectancy (Net)**: **-0.00300**

- Net PnL Total: -3.60158

- SQN Score: -6.07532


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 349 | 3 | 0.00% | **-0.01075** |  |
| TREND_DOWN | 171 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 20351 | 226 | 24.34% | **-0.00368** |  |
| CHOP_LOWVOL | 71084 | 945 | 26.35% | **-0.00332** |  |
| PANIC | 1490 | 26 | 53.85% | **0.01528** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00327

- Last 20% Median Exp: -0.00180

- Drop Ratio: 45.05%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
