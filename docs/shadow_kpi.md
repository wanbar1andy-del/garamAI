# Shadow Pilot KPI (Key Performance Indicators)

## 1. Stability Metrics (System Health)

* **Uptime**: 99.9% during market hours (09:00 - 15:30).
* **Data Gaps**: < 1% missing bars in 1-minute data.
* **Latency**: Signal generation to "Shadow Execution" < 100ms.

## 2. Strategy Performance Metrics (SurfingBrain)

These metrics determine if a strategy is ready for Live Trading promotion.

| Metric | Target (Daily) | Stop Condition (Daily) | Notes |
| :--- | :--- | :--- | :--- |
| **Trade Count** | 5 - 20 | < 3 (Too passive) | Ensure statistical significance. |
| **Win Rate** | > 45% | < 30% | Trend following can have lower WR. |
| **Avg R-Multiple**| > 0.2R | < -0.5R | Expectancy per trade. |
| **Max Drawdown** | < 1.0% | > 2.0% | Shadow equity drawdown. |

## 3. Execution Metrics (Shadow vs Theory)

* **Slippage Proxy**: Difference between `Signal Price` and `Next Tick Open`. Target < 0.05%.
* **Fill Rate**: % of signals that would have been filled (considering volume). Target > 95%.

## 4. Promotion Criteria (To Live)

A strategy configuration (e.g., `SB-2.5-rules-opt`) is eligible for Live Trading if:

1. Run in Shadow Mode for **10 consecutive trading days**.
2. Cumulative **Net Profit > 0**.
3. **Max Drawdown < 5%** over the period.
4. **Trade Count > 50**.
