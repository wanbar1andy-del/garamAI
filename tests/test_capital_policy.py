# tests/test_capital_policy.py
"""
Phase 21-C Contract Tests: capital_policy allocation rules
"""
import numpy as np
import pandas as pd
import pytest

from garam_core.analysis.capital_policy import CapitalPolicy
from garam_core.analysis.hero_finder import HeroMetadata


def _hero(
    symbol="005930",
    is_hero=True,
    overnight_tier="NONE",
    gap_n=0,
    overnight_score=0.1,
    hero_score=0.1,
):
    """Create test HeroMetadata"""
    return HeroMetadata(
        symbol=symbol,
        probe_name="TEST",
        expectancy_net=0.001,
        win_rate=0.55,
        tail_ratio=0.20,
        trades=30,
        tpd=1.0,
        total_return=0.0,
        p10_return=0.0,
        p90_return=0.0,
        max_loss_trade=0.0,
        open_window_expectancy=0.0,
        open_window_win_rate=0.0,
        open_window_trades=0,
        overnight_expectancy_net=0.0,
        overnight_win_rate=0.0,
        overnight_tail_ratio=0.0,
        overnight_trades=5,
        overnight_p10_return=0.0,
        overnight_max_loss=0.0,
        overnight_score=overnight_score,
        gap_p10=np.nan,
        gap_max_loss=np.nan,
        gap_std=np.nan,
        gap_n=gap_n,
        overnight_tier=overnight_tier,
        is_hero=is_hero,
        hero_score=hero_score,
        reason_tags=[],
    )


def test_no_hero_no_alpha():
    """SSOT: No Hero = No Trade -> Alpha allocation = 0"""
    policy = CapitalPolicy()
    allocation = policy.plan(aum=10_000_000, heroes=[])
    
    alpha_total = allocation[allocation["sleeve"] == "ALPHA"]["weight"].sum()
    assert float(alpha_total) == 0.0, "Alpha allocation must be 0 when no heroes"
    
    # Weight sum = 1.0
    assert abs(float(allocation["weight"].sum()) - 1.0) < 1e-9
    
    # Only CASH/RESERVE
    assert len(allocation) == 1
    assert allocation.iloc[0]["symbol"] == "CASH"
    assert allocation.iloc[0]["sleeve"] == "RESERVE"


def test_soft_requires_gap_n_gte_5():
    """SOFT tier must have gap_n >= 5"""
    hero_soft_invalid = _hero(
        symbol="111111", 
        overnight_tier="SOFT", 
        gap_n=3,  # Invalid
        overnight_score=0.9
    )
    
    policy = CapitalPolicy()
    allocation = policy.plan(aum=1_000_000, heroes=[hero_soft_invalid])
    
    # No SOFT tier rows (downgraded to INTRADAY)
    soft_rows = allocation[allocation["tier"] == "SOFT"]
    assert len(soft_rows) == 0, "SOFT with gap_n<5 should not appear in SOFT tier"
    
    # Weight sum = 1.0
    assert abs(float(allocation["weight"].sum()) - 1.0) < 1e-6


def test_allocation_weights_sum_to_one():
    """Weights must sum to 1.0"""
    heroes = [
        _hero("005930", overnight_tier="STRICT", gap_n=20, overnight_score=0.9),
        _hero("000660", overnight_tier="SOFT", gap_n=10, overnight_score=0.7),
        _hero("035420", overnight_tier="NONE", hero_score=0.5),
    ]
    
    policy = CapitalPolicy()
    allocation = policy.plan(aum=10_000_000, heroes=heroes)
    
    total_weight = float(allocation["weight"].sum())
    assert abs(total_weight - 1.0) < 1e-9, f"Weights must sum to 1.0, got {total_weight}"


def test_strict_requires_gap_n_gte_15():
    """STRICT tier must have gap_n >= 15"""
    hero_strict_invalid = _hero(
        symbol="222222",
        overnight_tier="STRICT",
        gap_n=10,  # Invalid (< 15)
        overnight_score=0.95
    )
    
    policy = CapitalPolicy()
    allocation = policy.plan(aum=1_000_000, heroes=[hero_strict_invalid])
    
    # No STRICT tier rows
    strict_rows = allocation[allocation["tier"] == "STRICT"]
    assert len(strict_rows) == 0, "STRICT with gap_n<15 should be downgraded"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
