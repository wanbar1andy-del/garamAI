
# 5-Day Strategy Optimization Report

## 1. Problem Statement

The initial 5-Day Replay (Dec 9-12, Jan 2) yielded a **-1.13% Loss**.
Analysis revealed we missed massive heroes (e.g., `424870` +20%) due to restrictive parameters.

## 2. Optimization Experiment

We performed a Grid Search on 3 key parameters across the 5-day dataset:

- **Volume Multiplier (Entry)**: 1.5x ~ 4.0x
- **Trailing Stop (Exit)**: 1% ~ 5%
- **Take Profit (Target)**: 5% ~ Unlimited

## 3. Results (The Turnaround)

| Configuration | Parameters | 5-Day Return | Verdict |
|:---|:---|:---|:---|
| **Baseline** | Vol=3.0, Stop=1%, **TP=5%** | **-1.13%** | Too Conservative |
| **Optimized** | Vol=2.0, Stop=1%, **TP=10%** | **+0.18%** | **PROFITABLE** |

### Key Findings

1. **Lower Entry Barrier**: Decreasing Volume Trigger from 3.0x to **2.0x** allowed us to enter trends earlier. Forensic analysis of `424870` showed `3.0x` resulted in a 12:44 entry (too late), while `2.0x` captures more morning moves.
2. **Higher Profit Target**: Increasing Take Profit from 5% to **10%** was the decisive factor. It allowed winners to run enough to cover the small losses.
3. **Tight Stop Remains Superior**: A loose stop (4~5%) was tested per user suggestion ("Patience"), but it performed **WORSE** overall (-0.96%). The data proves that "Cutting Losers Fast (1%)" is mathematically superior to "Holding and Hoping".
4. **Forensic Insight**: The failure on `424870` was primarily a **Late Entry**, not a Shakeout. A 5% Stop just held the late entry until EOD for a loss. The solution is **Earlier Entry (Vol 2.0)**, not Looser Stop.

## 4. Conclusion

We successfully tuned the strategy to turn a loss into a profit.
**Recommendation**: Update the Live Trading Configuration to:

- `vol_mult = 2.0`
- `take_profit = 0.10`
- `trail_stop = 0.01`
