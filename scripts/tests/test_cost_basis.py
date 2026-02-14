"""
[X-7f] Unit Tests for Cost Basis Fix (P0)
- These tests MUST PASS before Paper Trading can be unblocked.
"""
import pandas as pd
import sys
from pathlib import Path

PROJECT_ROOT = Path("C:/garam/garam")
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.core.antigravity_x7_core import (
    Position, Stage, apply_fill_add, pnl_from_avg, mfe_from_signal
)


def make_pos():
    """Create a test position with known values."""
    return Position(
        ticker="TEST",
        entry_ts=pd.Timestamp("2025-01-01 09:00"),
        signal_px=100.0,
        signal_high_px=100.0,
        avg_px=100.0,
        qty=10,
        last_ts=pd.Timestamp("2025-01-01 09:00"),
        last_px=100.0,
        low_px=100.0,
        score_entry=10.0,
        stage=Stage.CANDIDATE,
        weight=0.06,
        max_weight=0.06
    )


def test_apply_fill_add():
    """
    Test that apply_fill_add correctly updates avg_px using weighted average.
    - Start: qty=10, avg_px=100
    - Add: qty=10, fill_px=110
    - Expected: qty=20, avg_px=105 (weighted avg)
    """
    p = make_pos()
    apply_fill_add(p, add_qty=10, fill_px=110.0)
    
    assert p.qty == 20, f"Expected qty=20, got {p.qty}"
    assert abs(p.avg_px - 105.0) < 1e-9, f"Expected avg_px=105, got {p.avg_px}"
    # signal_px should NOT change
    assert p.signal_px == 100.0, f"signal_px should not change, got {p.signal_px}"
    print("✅ test_apply_fill_add PASSED")


def test_apply_fill_add_multiple():
    """
    Test multiple pyramid adds.
    - Start: qty=10, avg_px=100
    - Add 1: qty=10, fill_px=110 -> qty=20, avg_px=105
    - Add 2: qty=20, fill_px=120 -> qty=40, avg_px=112.5
    """
    p = make_pos()
    apply_fill_add(p, add_qty=10, fill_px=110.0)
    apply_fill_add(p, add_qty=20, fill_px=120.0)
    
    # (100*10 + 110*10 + 120*20) / 40 = (1000 + 1100 + 2400) / 40 = 4500/40 = 112.5
    assert p.qty == 40, f"Expected qty=40, got {p.qty}"
    assert abs(p.avg_px - 112.5) < 1e-9, f"Expected avg_px=112.5, got {p.avg_px}"
    print("✅ test_apply_fill_add_multiple PASSED")


def test_pnl_from_avg():
    """
    Test that pnl_from_avg uses avg_px, not signal_px.
    - avg_px=105, px=100 => pnl = (100/105) - 1 = -4.76%
    """
    p = make_pos()
    p.avg_px = 105.0
    
    pnl = pnl_from_avg(p, 100.0)
    expected = (100.0 / 105.0) - 1.0  # -0.047619...
    
    assert abs(pnl - expected) < 1e-9, f"Expected pnl={expected}, got {pnl}"
    print("✅ test_pnl_from_avg PASSED")


def test_mfe_from_signal():
    """
    Test that mfe_from_signal uses signal_px/signal_high_px, not avg_px.
    - signal_px=100, signal_high_px=112 => mfe = 12%
    """
    p = make_pos()
    p.signal_px = 100.0
    p.signal_high_px = 112.0
    p.avg_px = 105.0  # Should be ignored
    
    mfe = mfe_from_signal(p)
    expected = 0.12
    
    assert abs(mfe - expected) < 1e-9, f"Expected mfe={expected}, got {mfe}"
    print("✅ test_mfe_from_signal PASSED")


def test_signal_avg_independence():
    """
    Critical test: Verify that signal_px and avg_px are truly independent.
    After pyramiding, signal_px should remain unchanged.
    """
    p = make_pos()
    original_signal = p.signal_px
    
    # Pyramid multiple times
    apply_fill_add(p, 10, 110.0)
    apply_fill_add(p, 20, 120.0)
    apply_fill_add(p, 30, 130.0)
    
    # Signal should be unchanged
    assert p.signal_px == original_signal, \
        f"signal_px changed from {original_signal} to {p.signal_px}"
    
    # avg_px should be weighted average
    # (100*10 + 110*10 + 120*20 + 130*30) / 70 = 8400/70 = 120
    assert abs(p.avg_px - 120.0) < 1e-9, f"Expected avg_px=120, got {p.avg_px}"
    print("✅ test_signal_avg_independence PASSED")


def run_all_tests():
    print("=" * 50)
    print("[X-7f] Cost Basis Unit Tests")
    print("=" * 50)
    
    test_apply_fill_add()
    test_apply_fill_add_multiple()
    test_pnl_from_avg()
    test_mfe_from_signal()
    test_signal_avg_independence()
    
    print("=" * 50)
    print("ALL TESTS PASSED ✅")
    print("Paper Trading block can be considered for removal.")
    print("=" * 50)


if __name__ == "__main__":
    run_all_tests()
