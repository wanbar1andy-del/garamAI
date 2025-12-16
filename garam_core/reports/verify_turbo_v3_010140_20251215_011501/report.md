# Turbo V3 Verified Result (010140)

## Meta

- Run ID: `verify_turbo_v3_010140_20251215_011501`
- Timestamp (UTC): `2025-12-15T01:15:01Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `010140` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2533, win_rate=0.00%, pnl=None, mdd=0.00%, equity=2432213.35096635

## Key Points

- Total Return: -97.57%
- Max Drawdown: -97.59%
- Trades: 2533
- Final Equity: 2,432,213 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1266

- Win Rate: 27.96%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00019

- **Expectancy (Net)**: **-0.00261**

- Net PnL Total: -3.29797

- SQN Score: -10.56316


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 384 | 3 | 100.00% | **0.03545** |  |
| TREND_DOWN | 105 | 0 | 0.00% | **0.00000** |  |
| CHOP_HIGHVOL | 2231 | 19 | 26.32% | **-0.00424** |  |
| CHOP_LOWVOL | 91899 | 1226 | 27.65% | **-0.00267** |  |
| PANIC | 1193 | 18 | 38.89% | **-0.00251** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00243

- Last 20% Median Exp: -0.00299

- Drop Ratio: -23.07%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
