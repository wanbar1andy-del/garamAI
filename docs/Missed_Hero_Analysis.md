
# 5-Day Missed Hero Analysis

**Conclusion**: The user's suspicion is correct. **Heroes existed** every day, but the current algorithm failed to profit from them.

## 1. Daily Hero Identification (What We Missed)

| Date | Top Hero | Return | Volume | Did We Trade? |
|:---|:---|:---|:---|:---|
| **12/09** | **457190** | **+16.92%** | 3.1M | Missed / Stopped |
| **12/10** | **001430** | **+12.74%** | 0.5M | Missed (Low Vol?) |
| **12/11** | **424870** | **+20.43%** | **25M** | **CRITICAL MISS (See Forensic)** |
| **12/12** | **466100** | **+23.33%** | 8.4M | **CRITICAL MISS** |
| **01/02** | **319400** | **+7.24%** | 6.4M | **CAPTURED (+0.72%)** |

## 2. Forensic Analysis: Why did we miss 424870?

We ran a tick-by-tick replay of the strategy on `424870` (Dec 11).

![Forensic Chart](/garam/garam/results/reports/forensic_424870.png)

**Sequence of Events**:

1. **Entry**: 12:44 @ 14,280 KRW (Correctly identified breakout).
2. **Stop Loss**: 13:04 @ 14,130 KRW (Price dipped -1.05%, hitting the 1% Trailing Stop).
3. **The Miss**: After 13:04, the stock rallied significantly to +20%.
4. **System Flaw**: The strategy has a **"One Trade Per Day"** limit. It never re-entered.

## 3. Corrective Action Plan (Next Phase)

1. **Loosen Stop Loss**: Optimization showed 1% is safer overall, BUT...
2. **Re-entry Logic (Crucial)**: We MUST implement **"Re-Entry on New High"**.
    - If stopped out, but price breaks the previous High again, **BUY AGAIN**.
    - This would have caught the rally after 13:04.
3. **Parameter Optimization**: (Done in Phase 32: Result TP=10%, Vol=2.0).

**Verdict**: The Strategy Logic needs **Re-Entry Capability** to truly capture Heroes that "shake out" weak hands before mooning.
