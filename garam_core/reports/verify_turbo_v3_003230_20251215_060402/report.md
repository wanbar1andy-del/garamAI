# Turbo V3 Verified Result (003230)

## Meta

- Run ID: `verify_turbo_v3_003230_20251215_060402`
- Timestamp (UTC): `2025-12-15T06:04:02Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `003230` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2404, win_rate=0.00%, pnl=None, mdd=0.00%, equity=3620717.215129115

## Key Points

- Total Return: -96.38%
- Max Drawdown: -96.66%
- Trades: 2404
- Final Equity: 3,620,717 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1202

- Win Rate: 31.28%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00041

- **Expectancy (Net)**: **-0.00239**

- Net PnL Total: -2.86875

- SQN Score: -9.21456


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**
- **REGIME_MISMATCH**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 473 | 4 | 50.00% | **0.01557** |  |
| TREND_DOWN | 189 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 1183 | 10 | 40.00% | **0.00071** |  |
| CHOP_LOWVOL | 92533 | 1158 | 31.00% | **-0.00254** |  |
| PANIC | 1483 | 30 | 36.67% | **-0.00005** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00227

- Last 20% Median Exp: -0.00276

- Drop Ratio: -21.82%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
