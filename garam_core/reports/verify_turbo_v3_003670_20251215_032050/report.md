# Turbo V3 Verified Result (003670)

## Meta

- Run ID: `verify_turbo_v3_003670_20251215_032050`
- Timestamp (UTC): `2025-12-15T03:20:50Z`
- Mode: `verification`
- Git: `None` (None) dirty=None
- Data: `003670` / `minute`
- Units: `decimal / decimal / KRW`
- Regime: `micro_regime_v1 (minute)`

## Summary

- Status: **PASS**
- KPIs: trades=2333, win_rate=0.00%, pnl=None, mdd=0.00%, equity=2534995.88020138

## Key Points

- Total Return: -97.47%
- Max Drawdown: -97.55%
- Trades: 2333
- Final Equity: 2,534,996 KRW

## Edge Analysis (EdgeMatrix)


### Overall Expectancy (Net of Costs)

- Trades: 1166

- Win Rate: 27.10%

- Cost/Trade: 0.00280 (est)

- Expectancy (Gross): 0.00000

- **Expectancy (Net)**: **-0.00280**

- Net PnL Total: -3.26084

- SQN Score: -9.03316


### Collapse Tags (Automated)

- **CRASH_COLLAPSE**
- **COST_DOMINATED**
- **NEGATIVE_EDGE**
- **REGIME_MISMATCH**


### Edge Map (Micro-Regime)

| Regime | Bars | Trades | Win% | Net Exp | Tags |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TREND_UP | 448 | 4 | 25.00% | **0.01348** |  |
| TREND_DOWN | 737 | 1 | 0.00% | **-0.01004** |  |
| CHOP_HIGHVOL | 3935 | 37 | 16.22% | **-0.00777** |  |
| CHOP_LOWVOL | 89286 | 1101 | 27.43% | **-0.00268** |  |
| PANIC | 1474 | 23 | 30.43% | **-0.00296** |  |
| UNCERTAIN | 0 | 0 | 0.00% | **0.00000** |  |


### Structural Break Analysis

- First 80% Median Exp: -0.00277

- Last 20% Median Exp: -0.00234

- Drop Ratio: 15.62%

- **Structural Break**: NO

## Checks

### B-6-LOCK — Cost Model Locked

- Status: **PASS** (severity=high)

**Metrics**

- `slippage`: 2.5bp
- `tax`: 0.23%

**Notes**

- Confirmed B-6 cost model application.
