# GARAM Engine 1 (Legacy/DGE) & Champion Rule v2.1 Specification

**Document Version:** v2.1 (Restored)
**Date:** 2025-12-06
**Context:** Dual Engine Optimization

---

## 1. Capital Allocation: The Golden 5% Rule [Engine 1]

* **Rule:** Fixed **5%** of critical capital is allocated to Engine 1 (Legacy DGE).
* **Remaining 95%**: Allocated to Engine 2 (Advanced Macro/HMM/Champion Engine).
* **Purpose:**
  * **Independent Sensor:** Detects microstructure changes Engine 2 might miss.
  * **Structural Hedge:** Continues purely technical trend-following even when Engine 2 is defensive.
  * **Bear Market:** Never shuts down completely; maintains 5% allocation to sense bottom reversals.

---

## 2. Engine 1 Strategy: DGE_ORB_Aggressive

**Role:** Intraday Sensor & Hedge
**Allocation:** 5% Fixed

### 2.1 Core Logic: Dual Horizon

* **Short Horizon (fs, "Timing")**:
  * **Indicator:** 15-min ORB (Opening Range Breakout).
  * **Logic:**
    * Range = 09:00~09:30 High/Low.
    * `fs > 0`: Price > Range High + Buffer (0.2%).
    * `fs < 0`: Price < Range Low - Buffer (0.2%).
* **Mid Horizon (fm, "Direction")**:
  * **Indicator:** Daily 20 EMA Slope.
  * **Logic:**
    * `fm > 0`: 20 EMA Rising.
    * `fm < 0`: 20 EMA Falling.

### 2.2 Trading Rules

* **Long Entry:** `fs >= 0.3` (Strong Breakout) AND `fm >= -0.1` (Trend not crashing).
* **Short Entry:** `fs <= -0.3` (Strong Breakdown) AND `fm <= 0.0`. (Cash/Inverse).
* **Exit:**
  * **Target:** +2.5R.
  * **Trailing Stop:** At +1.5R gain, move stop to Breakeven+.
  * **Stop Loss:** -1.0R (1.5% of allocated capital).
  * **Time Cut:** 16 bars (~4 hours) with no profit.

### 2.3 Risk Management (Independent)

* **Risk Per Trade:** 1.5% of *Allocated Capital (5%)*.
* **Daily Loss Cap:** Stop trading if daily loss hits -5% of *Allocated Capital*.
* **Max Exposure:** 50% of *Allocated Capital* (Always keep 50% cash in this engine).

---

## 3. Engine 2 Strategy: Champion Rule v2.1 Optimized

**Role:** Main Profit Driver
**Allocation:** 95%
**Universe:** Top 50-100 Liquid Stocks (Reference to 400 Universe in operations).
**Style:** Winner Takes All (Concentrated).

### 3.1 Selection Logic

* **Regime + Edge Scoring**: Select top assets based on combined score.
* **Concentration**: Operate **2 to 5** Champion stocks.

### 3.2 Regime Guardrails

* **R1 (Strong Up):** Aggressive sizing.
* **R2 (Grind Up):** Trend following.
* **R3 (Chop):** Swing trading, aggressive profit taking.
* **R4 (Down):** Defensive, high cash.
* **R5 (Crash):** 100% Cash.

### 3.3 Performance Reference (Research)

* **Regression Test (1Y):**
  * CAGR: ~222% - 275%
  * MDD: -14% - -16%
* **Real Sim (1Y, Top 50):**
  * Return: +92.12%
  * MDD: -17.97%

---

## 4. Operational Directives (User Instruction)

1. **Universe:** Use **400 stock** universe for scanning.
2. **Concentration:** Select and operate **2 to 5** Champions.
3. **Overnight Rule:** Maintain the **5% Golden Rule** for Engine 1 (DGE) overnight holds capability.
