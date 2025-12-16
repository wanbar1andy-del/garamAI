# DGE v0.3 fs_orb Tuning Report (Implemented)

**Objective**: Optimize `fs_orb` (Intraday Momentum) threshold to maximize "Attack Mode" performance in `STRONG_UP` regimes.
**Status**: **Implemented & Verified** (2025-11-29)

## 1. Executive Summary

**Logic Applied**:

- **STRONG_UP (High/Low Vol)**: `fs_orb >= 0.3` (Attack Mode)
- **Others (Med Vol, Weak Up, Flat, Down)**: `fs_orb >= 0.5` (Defense Mode)

**Verification Result**:

- **Total PnL**: **152.4M KRW** (Matches v0.2's 152.8M)
- **Trade Count**: **1,413** (3.3x v0.2's 423)
- **Win Rate**: **56.8%** (Robust)

**Conclusion**: The refined v0.3 engine successfully combines the high profitability of v0.2 with the high activity and regime-robustness of v0.3. It is ready for Paper Trading.

## 2. Sweep Results (Pre-Implementation Analysis)

| Scenario | Threshold (SU) | Total PnL | Trades | Win Rate | Avg PnL | STRONG_UP PnL |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **v0.3 Base** | 0.5 (Fixed) | 140,402,764 | 1,370 | 57.4% | 102,484 | 101,092,770 |
| **v0.3 (0.3)** | **0.3** | **156,199,683** | **1,424** | **56.6%** | **109,691** | **115,768,707** |
| **v0.3 (0.2)** | 0.2 | 156,797,966 | 1,467 | 55.8% | 106,883 | 116,040,171 |
| **Dynamic** | fs_fast based | 153,575,676 | 1,420 | 56.9% | 108,152 | 114,265,681 |

## 3. Final Verification (Post-Implementation)

Comparison of v0.2 (Static) vs v0.3 (Refined Attack Engine).

| Version | Total PnL | Trades | Win Rate | Avg PnL | Note |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **v0.2** | 152,779,000 | 423 | 60.3% | 361,179 | High efficiency, low frequency. |
| **v0.3 (Refined)** | **152,351,000** | **1,413** | **56.8%** | **107,821** | **High frequency, matched PnL.** |

**Key Achievement**:
We unlocked **~1,000 additional trades** compared to v0.2 without sacrificing Total PnL. This means the system is far more active and engaging, capturing more intraday opportunities in strong trends, while maintaining a safety net for other regimes.

## 4. Implementation Details

Modified `strategies/kr_intraday/dge_orb_v0_3.py`:

```python
# Regime-Specific Entry Threshold
current_fs_orb_thresh = 0.5 

# Attack Mode Tuning: Relax threshold for STRONG_UP
if "STRONG_UP_HIGH_VOL" in regime or "STRONG_UP_LOW_VOL" in regime:
    current_fs_orb_thresh = 0.3
# Note: STRONG_UP_MED_VOL stays at 0.5 (Conservative)
```

**Next Step**: Deploy to Paper Trading.
