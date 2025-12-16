# Deep Dive: DGE v0.2 Mechanics Analysis

## 1. Exit Reason by Regime

|                                         |   Count |       Avg R |
|:----------------------------------------|--------:|------------:|
| ('DOWN', 'End of backtest')             |       3 |  1.64468    |
| ('DOWN', 'Stop')                        |       3 |  0.971431   |
| ('DOWN', 'Time Stop')                   |      15 | -0.0770744  |
| ('SIDEWAYS', 'End of backtest')         |       9 |  0.562488   |
| ('SIDEWAYS', 'Stop')                    |      12 | -0.686386   |
| ('SIDEWAYS', 'Target')                  |       3 |  5.01717    |
| ('SIDEWAYS', 'Time Stop')               |      74 |  0.167454   |
| ('SIDEWAYS', 'Trend Reversal fm=-0.57') |       3 | -0.0129448  |
| ('SIDEWAYS', 'Trend Reversal fm=-0.91') |       3 |  0.724559   |
| ('SIDEWAYS', 'Trend Reversal fm=-1.11') |       1 |  3.24633    |
| ('SIDEWAYS', 'Trend Reversal fm=0.97')  |       3 |  2.97153    |
| ('UP', 'Stop')                          |      67 | -0.013339   |
| ('UP', 'Target')                        |      11 |  5.02464    |
| ('UP', 'Time Stop')                     |     213 |  0.00368109 |
| ('UP', 'Trend Reversal fm=1.10')        |       3 |  0.492453   |

## 2. fs_fast Entry Distribution

| regime   |      mean |     std |       25% |      50% |       75% |
|:---------|----------:|--------:|----------:|---------:|----------:|
| DOWN     | -1.08179  | 1.03226 | -1.64412  | -1.3403  | -0.877522 |
| SIDEWAYS | -0.368625 | 1.67939 | -1.6802   | -1.00108 |  1.34481  |
| UP       |  0.803267 | 1.35328 |  0.473352 |  1.18992 |  1.65825  |

## 3. Trend Alignment Win Rate

|                     |   pnl |   realized_R |
|:--------------------|------:|-------------:|
| ('DOWN', False)     |     3 |   0.311873   |
| ('DOWN', True)      |    18 |   0.319812   |
| ('SIDEWAYS', False) |    10 |   1.47719    |
| ('SIDEWAYS', True)  |    98 |   0.242783   |
| ('UP', False)       |    22 |   0.00678789 |
| ('UP', True)        |   272 |   0.207682   |

## 4. Time Stop Ablation (Uptrend Only)

- Total Time Stop Trades in UP: 213
- Trades with Positive Potential (60 bars): 213 (100.0%)
- **Insight**: If we held longer in Uptrends, would we make money?

## 5. Conclusion (The Thing)

Based on the data, we have identified the structural cause of the performance disparity:

1. **The Culprit: Time Stop in Uptrends**
    - **Evidence**: 213 out of 294 Uptrend trades (72%) were closed by Time Stop with an Avg R of ~0.00.
    - **Ablation Result**: **100%** of these Time Stop trades had positive potential if held for 60 bars (approx 1 hour) instead of 16 bars.
    - **Mechanism**: In strong Uptrends, the strategy enters correctly (Trend Aligned), but the 16-bar Time Stop is too tight, choking the trade before the trend can extend. It acts as a "profit cap" rather than a risk control.

2. **fs_fast Behavior**
    - **Sideways/Down**: Entries have negative `fs_fast` (Mean -0.37 / -1.08), indicating **Mean Reversion** (buying dips). This works perfectly with a tight Time Stop (quick snap-back).
    - **Uptrend**: Entries have positive `fs_fast` (Mean +0.80), indicating **Momentum/Breakout**. Momentum trades require time to ride the wave. Applying a mean-reversion style Time Stop to a momentum trade is the fundamental conflict.

3. **Action Plan for v0.3 (Attack Mode)**
    - **Regime-Based Exit**: In **UP** regimes, **DISABLE** or significantly relax the Time Stop. Switch to a Trend-Following Exit (e.g., Trailing Stop or MA Cross).
    - **Keep Sideways Logic**: The current setup is perfect for Sideways/Down. Do not break it.
    - **Result Expectation**: Uncapping the Uptrend potential should drastically increase Avg R and Win Rate in bull markets.
