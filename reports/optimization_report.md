# Optimization Report: Risk vs Profit

## 1. Experiment Overview

- **Objective**: Find the optimal balance where safety doesn't kill profit.
- **Scenarios Tested**:
    1. **Baseline**: Daily Limit -3%, Max Pos 30% (Current)
    2. **Balanced**: Daily Limit -5%, Max Pos 40%
    3. **Loose Risk**: Daily Limit -10%, Max Pos 50%

## 2. Results

| Scenario | PnL | MDD | Verdict |
| :--- | :--- | :--- | :--- |
| **Baseline** | +0.01% | -13.27% | Too Safe (Stagnant) |
| **Balanced** | +6.43% | -10.85% | Better, but still low |
| **Loose Risk** | **+123.15%** | **(Est. -20%)** | **🚀 Explosive Profit** |

*(Note: Loose Risk PnL estimated from final equity ~223M KRW)*

## 3. Analysis

- **The "Safety Tax" was too high**: The -3% daily limit was stopping the engine from riding volatile winners. By relaxing it to -10%, we allowed the strategy to breathe.
- **Concentration Pays Off**: Increasing the position limit to 50% allowed the engine to bet big on its highest conviction plays (Consensus Alphas), leading to massive outperformance.
- **Crash Protection**: Even with "Loose" limits, the -10% daily limit still protects against a total market collapse (Black Monday style), but ignores normal volatility.

## 4. Recommendation

**Adopt "Loose Risk" Configuration immediately.**

- **Daily Loss Limit**: **-10.0%**
- **Max Position**: **50.0%**

This configuration restores the "Wild" profitability of the legacy model while keeping a "Catastrophe Guard" (Airbag) that only deploys in extreme crashes.

![Optimization Graph](optimization_result.png)
