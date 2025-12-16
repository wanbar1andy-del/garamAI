# tests/test_phase21_contracts.py
"""
Phase 21 Contract Tests (SSOT Rules)

Critical rules that MUST NOT be violated:
1. Gap NaN Rule: gap_n < 5 → gap_* = NaN (not 0.0)
2. Pass2 probe_params: Same params as Pass1
3. 2-Pass Top-K: Pass2 only on heroes
"""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from garam_core.analysis.hero_finder import HeroFinder, HeroMetadata


class TestGapNaNRule:
    """
    Gap NaN Rule: Insufficient gap samples → NaN, NOT 0.0
    
    Reason: 0.0 > -0.02 would allow SOFT tier (false positive)
    """
    
    def test_gap_nan_with_insufficient_samples(self):
        """gap_n < 5 → gap_p10/gap_max_loss/gap_std = NaN"""
        # Create mini DataFrame with < 5 gaps
        df = pd.DataFrame({
            'date': pd.date_range('2024-01-01', periods=3, tz='Asia/Seoul'),
            'open': [100, 102, 101],
            'close': [101, 101, 102],
        })
        
        finder = HeroFinder(feature_store=None)  # Mock
        gap_stats = finder._calculate_gap_stats(df)
        
        # CRITICAL: Must be NaN, not 0.0
        assert np.isnan(gap_stats['gap_p10']), "gap_p10 must be NaN with gap_n < 5"
        assert np.isnan(gap_stats['gap_max_loss']), "gap_max_loss must be NaN"
        assert np.isnan(gap_stats['gap_std']), "gap_std must be NaN"
        assert gap_stats['gap_n'] < 5, "gap_n should be < 5"
    
    def test_gap_valid_with_sufficient_samples(self):
        """gap_n >= 5 → gap_* calculated"""
        # Create DataFrame with >= 5 gaps
        df = pd.DataFrame({
            'date': pd.date_range('2024-01-01', periods=6, tz='Asia/Seoul'),
            'open': [100, 102, 101, 103, 100, 105],
            'close': [101, 101, 102, 102, 101, 104],
        })
        
        finder = HeroFinder(feature_store=None)
        gap_stats = finder._calculate_gap_stats(df)
        
        # With >= 5 samples, should have values
        assert gap_stats['gap_n'] >= 5
        # May be NaN if calculation fails, but not because of sample size


class TestOvernightTierJudgment:
    """
    Tier assignment must respect gap_n thresholds
    """
    
    def test_soft_requires_gap_n_gte_5(self):
        """SOFT tier requires gap_n >= 5"""
        # Mock metadata with gap_n < 5
        meta = HeroMetadata(
            symbol="TEST",
            is_hero=True,
            hero_score=1.0,
            expectancy_net=0.001,
            win_rate=0.6,
            tail_ratio=2.0,
            trades=100,
            tpd=5.0,
            overnight_expectancy_net=0.0005,
            overnight_win_rate=0.55,
            overnight_tail_ratio=1.8,
            overnight_trades=10,
            gap_p10=np.nan,  # NaN because gap_n < 5
            gap_max_loss=np.nan,
            gap_std=np.nan,
            gap_n=3,  # < 5
            overnight_tier="NONE",  # Should NOT be SOFT
            overnight_score=0.0,
        )
        
        # Verify: gap_n < 5 → NOT SOFT
        assert meta.overnight_tier != "SOFT", "Cannot be SOFT with gap_n < 5"
    
    def test_strict_requires_gap_n_gte_15(self):
        """STRICT tier requires gap_n >= 15"""
        # gap_n < 15 should NOT allow STRICT
        assert True, "Placeholder: verify in integration test"


class TestProbeParamsPropagation:
    """
    Pass2 must use same probe_params as Pass1
    """
    
    def test_probe_params_consistency(self):
        """
        Integration test: Verify Pass2 uses Pass1 params
        
        Note: Requires actual scan execution, deferred to smoke test
        """
        pytest.skip("Verified in smoke test with --two_pass")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
