# 1-Month Backtest Report (Multi-Alpha Engine)

## 1. Overview

- **Period**: 2025-11-05 ~ 2025-12-05
- **Engine**: Integrated LiveTradingEngine (Multi-Alpha)
- **Data**: Real Data (G: Drive)
- **Risk Mode**: MONITOR_ONLY (No trades blocked)

## 2. Performance Summary

| Metric | Result |
| :--- | :--- |
| **Initial Equity** | 100,000,000 KRW |
| **Final Equity** | **90,661,705 KRW** |
| **PnL** | **-9,338,295 KRW (-9.34%)** |
| **MDD** | (Requires detailed analysis, likely > 10%) |

## 3. Observations

- **Significant Loss**: The engine lost ~9.3% in one month. This is a critical underperformance.
- **Regime**: Detected as `R3_UP_BOX` in the final days.
- **Alpha Behavior**: Scores were high (>80) for some assets, implying aggressive entry, but the market likely reversed or chopped, leading to losses.
- **Risk Monitor**: Since it was in Monitor Mode, it didn't stop the losses. If `daily_loss_limit` (-3%) was ACTIVE, it might have halted trading on bad days, preserving capital.

## 4. Recommendations

1. **Analyze the Loss**: We need to see *which* trades caused this. Was it a few big hits or a slow bleed?
2. **Activate Risk Engine**: A -9% month confirms the need for the "Airbag". If the -3% daily limit was active, the damage would have been capped.
3. **Review Alphas**: The `A1` (Trend) and `A8` (Mean Rev) combination might be fighting each other or misfiring in this specific regime.

**Next Step**:

- Shall I generate a detailed trade log analysis to pinpoint the cause of the loss?
- Or should we activate the Risk Engine to `ACTIVE` mode immediately to prevent this in live trading?
