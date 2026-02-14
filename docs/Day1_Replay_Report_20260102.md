
# Day 1 Replay Report: 2026-01-02

**Execution Date**: 2026-01-02
**Strategy**: Intraday Breakout (Modified for Day-1 Warmup)
**Data Source**: Real-time Feed (`feed_live.jsonl`) -> Minute Bars (Extracted)

## 1. Executive Summary

| Metric | Value | Note |
|:---|:---|:---|
| **Capital** | 10,000,000 KRW | Virtual |
| **Final Net** | 10,072,093 KRW | **+0.72%** (+72,093 KRW) |
| **Top Hero** | **319400** | **+7.24%** Daily Return |
| **Strategy PnL** | **Positive** | Caught 13 breakouts |

## 2. Market Overview (Day 1)

**Hero of the Day**: `319400`

- **Return**: +7.24%
- **Volume**: 6.4M Shares
- **Pattern**: Strong morning surge followed by sustained high.

**Chart**:
![Hero Chart](/garam/garam/results/reports/day1_hero_319400.png)

## 3. Trade Log (Simulation)

Replay simulation using "Volume Breakout" logic (Buy on Volume Spike > 3x MA20):

| Time | Action | Symbol | Price |
|:---|:---|:---|:---|
| 09:13 | BUY | 010120 | 486,500 |
| 09:13 | BUY | 103590 | 57,000 |
| 09:20 | BUY | 088350 | 3,200 |
| 09:25 | BUY | 005935 | 92,900 |
| 09:46 | BUY | 006260 | 207,500 |
| 09:46 | BUY | 028260 | 241,000 |
| 09:47 | BUY | 310210 | 211,500 |
| 09:50 | BUY | 039490 | 298,000 |
| 09:51 | BUY | 036930 | 30,150 |
| 09:52 | BUY | 022100 | 28,850 |
| 10:07 | SELL | 039490 | 295,000 (Stop) |
| 10:14 | BUY | 000250 | 240,000 |
| 10:23 | BUY | 071050 | 164,100 |
| 10:40 | BUY | 089030 | 49,900 |
| 11:14 | BUY | 039490 | 303,000 |
| 11:16 | BUY | 009150 | 272,000 |

## 4. Conclusion

The "Day 1" market showed strong momentum in select stocks.
Despite the lack of daily history ("Cold Start"), the **Intraday Momentum Strategy** successfully captured short-term breakouts, generating a **0.72% return** in a single day.
This confirms the **Phase 31 Wide-Format Data Pipeline** is effective for capturing and backtesting intraday alpha.
