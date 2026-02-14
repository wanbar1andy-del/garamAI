# Hero Model v3 (Redesign Specification)

**Source**: User Request (Hero Redesign Proposal)
**Date**: 2026-01-02

---

## 1. Philosophy: The "Hero" Concept

- **Definition**: A "Hero" is a rare stock that drives the majority of portfolio returns (Fat Tail / Positive Skew).
- **Core Principle**: "Small losses on many, Huge gains on a few." (Convex Payoff).
- **Architecture**:
  - **Discovery**: Real-time scanning of 400-stock universe.
  - **Selection**: Relative Strength (Rank) + Absolute Quality (Net Profit > 0).
  - **Management**: Quick Cut (Switch) on weakness, Let Winners Run.

## 2. Scoring & Metrics

| Component | Metric | Description |
| :--- | :--- | :--- |
| **fs** (Fast Signal) | 15m Breakout / Momentum | Buying pressure strength (Immediate). |
| **fm** (Mid Signal) | Daily Trend / MA Slope | Structural uptrend confirmation. |
| **Vol** (Volume) | Vol Z-Score | Liquidity and attention concentration. |
| **Heat** (Context) | Market HeatScore | Market aggression level (-2 to +2). |

- **Ranking**: Composite Score = $w_1 \cdot fs + w_2 \cdot fm + w_3 \cdot Vol$.
- **Gate**: Absolute Threshold (e.g., Score > 0.15) AND Net Relative Return > 0.

## 3. Dynamic Portfolio Sizing (Slots)

Adjust number of Hero Slots based on Market Regime (Regime-Adaptive Exposure).

| Regime | Behavior | Slot Count | Strategy |
| :--- | :--- | :--- | :--- |
| **R1 (Strong Bull)** | Winner Takes All | **1-2** | Concentrate on Top 1. |
| **R2 (Moderate)** | Distribution | **2-3** | Spread risk across leaders. |
| **R3 (Choppy)** | Defensive | **0-2** | Quick swing / Cash heavy. |
| **R4 (Bear)** | Survival | **3-5** | Defensive dispersion (if trading). |
| **R5 (Crash)** | Shutdown | **0** | **Hold Cash (No Trade).** |

## 4. Execution Logic: The "SWITCH"

- **Trigger (Death)**:
    1. **Rank Exit**: Falls out of Top-K.
    2. **Edge Break**: Net Relative Return turns negative ($\le 0$).
    3. **Decay**: Sustained drop in momentum.
- **Trigger (Swap)**:
  - New Candidate Rank #1 >> Weakest Holding Rank.
  - Condition: New Candidate is NOT Overheated (e.g., >10% intraday already).
  - Action: Sell Weakest -> Buy New Candidate immediately.

## 5. Regime Filter (Safety Valve)

- **Concept**: If Market Breadth is broken ("No Hero"), Stop Trading.
- **Conditions**:
    1. Universe Max Score < Threshold.
    2. Top-N avg Net Return $\le 0$.
    3. MSS (Market Sensing Score) < Critical Level (e.g. -0.5).
- **Action**: **Cash Out / Pause Strategy.** (Currently implemented as "Hero Count < 3" in `run_live_paper.py`).

## 6. System Integration

- **DGE (Engine 1)**: Always On (5% Capital). Acts as "Sensor" during Hero Pause.
- **Champion (Engine 2)**: Main Engine adopting Hero v3 logic.
- **MSS**: Provides the Regime signal to control Slot Count and Safety Valve.

---

## Validated Implementation Plan

1. **Phase 30-5 (Current)**:
    - **Regime Filter**: Implemented "Hero Count" Check (Section 5).
    - **Action**: Proceed with Micro Live using this Safety Component.
2. **Phase 31 (Target)**:
    - **Logic Upgrade**: Implement Composite Scoring & Dynamic Slots.
    - **Execution**: Implement sophisticated "SWITCH" logic.
