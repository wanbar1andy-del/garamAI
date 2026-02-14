# SSOT Slot Operation & Switching Policy v1.0

## 1. Overview

This document defines the policy for Multi-Slot Operation and Hero Switching in the Garam System.
The goal is to solve the "Opportunity Cost" problem (e.g., missing Top-1 while holding a stagnant stock) observed in Policy v1.1.

## 2. Slot Operation Policy

- **Principle**: Minimize "All-in" risk and maximize "Winner Takes All" opportunities.
- **Max Slots**:
  - **Champion Profile**: Max **3 Slots** (Default).
  - **Dynamic**: Min 2 ~ Max 4 depending on Market Sensing Score (MSS).
- **Allocation**:
  - **Score-Based**: Higher weight to higher score ($w_i \propto Score_i^p$).
  - **Concentration**: Usually Top 1-2 stocks take 90% of equity (Winner Takes All).
  - **Risk Control**: Controlled by `risk_limits` (Max Gross Exposure).

## 3. Switching Logic (The "Swap" Rule)

When a new **Top-1 Hero** candidate appears while slots are full:

### A. Triggers (WHEN to Switch)

1. **Rank Inversion**: New Candidate Rank #1 > Existing Holding Rank #3.
2. **Score Gap**: New Score > Existing Low Score + **Gap Threshold** (e.g., +10%).
3. **Momentum Gap (FM/FS)**: New Hero's short-term momentum >> Existing Holding.
4. **PnL Decay**: Existing Holding is losing steam (PnL < 0 or Score drop) $\to$ Cut & Replace.

### B. Filters (WHEN NOT to Switch)

1. **Overheat**: New Candidate already risen > +10% today (Chasing risk).
2. **Market Fear (ABS)**: MSS indicates downtrend $\to$ Cash is King.

### C. Execution (HOW to Switch)

1. **Sell Weakest**: Force sell the lowest-ranked/lowest-PnL holding.
2. **Buy Strongest**: Immediately buy the new Top-1 Candidate.
3. **Rebalance**: (Optional) Adjust weights of remaining holdings.

## 4. Policy v2 Simulation Strategy (Comparison)

To validate this policy, we perform an A/B Test on **2025-12-15**:

- **Scenario A (Current v1.1)**: Max 1 Slot, No Switching.
  - Result: Held `139480`, Missed Top-1 `0009K0`.
- **Scenario B (Proposed v2.0)**: **Max 2~3 Slots**, Active Entry.
  - Expectation: Hold `139480` AND Buy `0009K0`.
  - Metric: Daily Return improvement.

## 5. Implementation Roadmap

- **Phase**: Phase 5 (Month-1 Expansion).
- **Engine**: Update `SignalMiner` or `AlphaAggregator` to emit Score/Rank.
- **Execution**: Implement `SlotManager` class in simulation script.
