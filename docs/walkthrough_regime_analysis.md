# DGE v0.2 Regime Analysis Report

**Date**: 2025-11-29 11:04
**Strategy**: DGE_ORB v0.2 (fs_fast)
**Regime Definition**: 20-day Simple Return (UP > 3%, DOWN < -3%)

## 1. Performance by Regime

| regime   |   Count |   Total PnL |    Avg R |   Win Rate |
|:---------|--------:|------------:|---------:|-----------:|
| DOWN     |      21 | 1.00371e+07 | 0.318678 |   0.571429 |
| SIDEWAYS |     108 | 5.78149e+07 | 0.35708  |   0.731481 |
| UP       |     294 | 8.49267e+07 | 0.192649 |   0.557823 |

## 2. Profitable Trades in Sideways/Down Markets

Top 10 profitable trades when market was NOT trending up:

|   symbol | entry_time          | regime   |         pnl |   realized_R | exit_reason             |
|---------:|:--------------------|:---------|------------:|-------------:|:------------------------|
|   005490 | 2025-09-29 13:55:00 | SIDEWAYS | 7.54172e+06 |      5.03071 | Target                  |
|   005490 | 2025-09-29 13:56:00 | SIDEWAYS | 7.52245e+06 |      5.01834 | Target                  |
|   005490 | 2025-09-29 13:57:00 | SIDEWAYS | 7.49915e+06 |      5.00246 | Target                  |
|   035420 | 2025-11-03 12:34:00 | SIDEWAYS | 4.86816e+06 |      3.24633 | Trend Reversal fm=-1.11 |
|   005380 | 2025-10-13 13:49:00 | SIDEWAYS | 4.48813e+06 |      2.99352 | Trend Reversal fm=0.97  |
|   005380 | 2025-10-13 13:48:00 | SIDEWAYS | 4.48652e+06 |      2.99251 | Trend Reversal fm=0.97  |
|   005380 | 2025-10-13 13:52:00 | SIDEWAYS | 4.39272e+06 |      2.92855 | Trend Reversal fm=0.97  |
|   005490 | 2025-11-25 09:47:00 | DOWN     | 2.49074e+06 |      1.66156 | End of backtest         |
|   005490 | 2025-11-25 09:49:00 | DOWN     | 2.47899e+06 |      1.6528  | End of backtest         |
|   005490 | 2025-11-25 09:48:00 | DOWN     | 2.42946e+06 |      1.6197  | End of backtest         |

## 3. Losing Trades in Uptrend Markets

Top 10 losing trades when market WAS trending up:

|   symbol | entry_time          | regime   |          pnl |   realized_R | exit_reason   |
|---------:|:--------------------|:---------|-------------:|-------------:|:--------------|
|   035420 | 2025-10-01 11:07:00 | UP       | -1.60192e+06 |     -1.06861 | Stop          |
|   005380 | 2025-10-20 09:49:00 | UP       | -1.59603e+06 |     -1.06491 | Stop          |
|   005490 | 2025-10-30 10:37:00 | UP       | -1.58264e+06 |     -1.05586 | Stop          |
|   005490 | 2025-10-30 10:38:00 | UP       | -1.57501e+06 |     -1.0501  | Stop          |
|   005490 | 2025-11-18 12:59:00 | UP       | -1.55713e+06 |     -1.03856 | Stop          |
|   005930 | 2025-09-26 13:01:00 | UP       | -1.55078e+06 |     -1.03404 | Stop          |
|   005930 | 2025-09-26 13:02:00 | UP       | -1.54906e+06 |     -1.03291 | Stop          |
|   005490 | 2025-10-30 10:35:00 | UP       | -1.54667e+06 |     -1.0316  | Stop          |
|   005490 | 2025-11-18 12:57:00 | UP       | -1.54649e+06 |     -1.03119 | Stop          |
|   005380 | 2025-10-27 10:09:00 | UP       | -1.54518e+06 |     -1.03069 | Stop          |

## 4. Key Insights

- **Sideways Dominance**: The strategy performs exceptionally well in **SIDEWAYS** markets, achieving a **73% Win Rate** and high Avg R (0.35). This confirms that `fs_fast` is effective at picking up mean-reversion or short-term momentum in choppy ranges.
- **Uptrend Volume**: While **UP** markets generate the most total PnL (+84.9M) due to high trade frequency (294 trades), the Win Rate (55.8%) is lower than in sideways markets. This suggests the strategy might be over-trading or getting whipsawed during strong trends (possibly entering late).
- **Down Market Resilience**: Surprisingly, the strategy remains profitable in **DOWN** markets (+10M PnL, 57% Win Rate), although trade frequency is low (21 trades). This indicates the `fs_fast` signal is robust enough to find counter-trend bounces or short opportunities (if enabled) even in bearish regimes.
- **Actionable Item**: Consider increasing position size or aggressiveness in **SIDEWAYS** regimes, as the edge is strongest there. For **UP** regimes, filtering for higher quality setups might improve the Win Rate.
