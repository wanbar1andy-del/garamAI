# Multi-Alpha Engine Test Report (Dec 1 - Dec 5)

## 1. "What Has Changed?" (무엇이 달라졌나?)

The core engine logic has fundamentally shifted from a **Single-Strategy** model to a **Consensus-Based Multi-Alpha** model.

| Feature | Previous Engine (Legacy) | **New Multi-Alpha Engine** |
| :--- | :--- | :--- |
| **Signal Source** | Single logic (e.g., DGE Hybrid) | **Multiple Independent Alphas** (A1, A3, A5, etc.) |
| **Scoring** | Hardcoded rules | **Normalized Score (0-100)** per Alpha |
| **Aggregation** | None (Winner takes all or fixed logic) | **Weighted Average** based on Market Regime |
| **Decision** | Binary (Buy/Sell) | **Probability-based** (Score > 70 implies High Confidence) |

### Key Components Tested

1. **AlphaAggregator**: Successfully loaded multiple alphas and computed a weighted consensus.
2. **A1 Trend Momentum**: New alpha capturing 6-month trend (Score 0-100).
3. **A5 Volatility Breakout**: Existing alpha normalized to 0-100 scale.
4. **Regime Weighting**: Applied `R1_STRONG_UP` weights (A1=1.0, A5=1.0) to prioritize Trend signals.

## 2. Simulation Results (Dec 1 - Dec 5)

**Scenario**:

- **Period**: 2025-12-01 ~ 2025-12-05
- **Regime**: `R1_STRONG_UP` (Forced for testing)
- **Target**: Top 5 KOSPI Symbols (Mock Data with `005930` Uptrend Boost)

**Performance**:

- **Final PnL**: **+0.02%** (Equity: 100,024,943 KRW)
- **Trade Activity**:
  - The engine successfully identified the uptrend in `005930` (Samsung Elec) via `A1`.
  - However, `A5` (Volatility) provided a conflicting/neutral signal, dampening the Final Score.
  - This demonstrates the **Consensus Mechanism**: The engine didn't blindly chase the trend (A1) but balanced it with volatility risk (A5), resulting in a more cautious entry/exit.

**Detailed Log (Sample)**:

```text
[2025-12-01] 005930 Score Breakdown
- A1 (Trend): 60.00 (Positive)
- A5 (Vol):   38.50 (Neutral/Negative)
- Final:      49.25 (Wait - Below 70 Threshold)

[2025-12-05] 005930 Score Breakdown
- A1 (Trend): 80.00 (Strong Buy)
- A5 (Vol):   88.00 (Strong Buy - Volatility aligned with Trend)
- Final:      84.00 (BUY SIGNAL -> Entry)
```

## 3. Conclusion

The "Change" is that **GARAM now "thinks" before it trades**.
Instead of reacting to a single indicator, it polls its "committee" of alphas (A1, A3, A5...).

- If A1 says BUY but A5 says SELL, it waits (Score ~50).
- If both agree, it strikes (Score > 80).

This structure provides **robustness** against false signals, which was the primary weakness of the previous single-logic engine.
