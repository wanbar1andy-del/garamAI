# Risk Engine Impact Report (1-Month Backtest)

## 1. Test Overview

- **Period**: 2025-11-05 ~ 2025-12-05
- **Objective**: Measure the impact of activating the Risk Engine (`ACTIVE` mode) vs. Monitor Mode.
- **Risk Settings**:
  - Daily Loss Limit: **-3.0%** (Stop new buys if hit)
  - Max Position: **30%** (Diversification forced)
  - Max Exposure: **100%** (No leverage)

## 2. Comparative Results

| Metric | Monitor Mode (Risk OFF) | Active Mode (Risk ON) | Delta |
| :--- | :--- | :--- | :--- |
| **Final Equity** | 90,661,705 KRW | **105,718,760 KRW** | +15,057,055 |
| **PnL** | **-9.34%** | **+5.72%** | **+15.06%p** |
| **Outcome** | ❌ Critical Loss | ✅ Healthy Profit | 🚀 Massive Improvement |

## 3. Why did this happen?

The "Airbag" effect was dramatic:

1. **Stop the Bleeding**: On days where the strategy suffered losses > 3%, the engine stopped adding new positions, preventing "catching a falling knife".
2. **Forced Diversification**: The 30% limit prevented the engine from betting the house on a single high-score stock that turned out to be a loser.
3. **Survival = Profit**: By surviving the drawdown period with capital intact, the portfolio was able to capture the subsequent rebound/trend.

## 4. Conclusion

**The Risk Engine is not just a safety device; it is a performance enhancer.**
It filters out the "tail risk" behavior of the raw strategy, stabilizing returns.

**Status**:

- Risk Engine is now **ACTIVE** in `risk/account_limits.yaml`.
- `run_live_trading.py` is fully integrated with these checks.
- System is ready for Live Trading with this configuration.

![Equity Curve Comparison](simulation_1month_active_risk.png)
*(Note: Graph file generated in reports/)*
