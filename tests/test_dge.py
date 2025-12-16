"""
DGE (Daily Growth Engine) Unit Tests

Tests for position sizing, Kelly Criterion, regime multipliers, and kill switch logic.
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from risk.dge import (
    DailyGrowthEngine, RiskConfig, KellySizer, MarketRegime
)


class TestKellySizer:
    """Test Kelly Criterion calculations"""
    
    def test_calculate_f_star_basic(self):
        """Test basic Kelly formula: f* = p - q/b"""
        # Example: 60% win rate, 2:1 payoff ratio
        # f* = 0.6 - 0.4/2 = 0.6 - 0.2 = 0.4 (40%)
        result = KellySizer.calculate_f_star(win_rate=0.6, payoff_ratio=2.0)
        assert abs(result - 0.4) < 0.001
    
    def test_calculate_f_star_edge_case(self):
        """Test Kelly with no edge (50% win rate, even money)"""
        # f* = 0.5 - 0.5/1 = 0
        result = KellySizer.calculate_f_star(win_rate=0.5, payoff_ratio=1.0)
        assert abs(result) < 0.001
    
    def test_calculate_f_star_log(self):
        """Test continuous Kelly: f* = mu / sigma^2"""
        result = KellySizer.calculate_f_star_log(mu=0.1, sigma=0.3)
        expected = 0.1 / (0.3 ** 2)  # ≈ 1.11
        assert abs(result - expected) < 0.001


class TestRiskConfig:
    """Test RiskConfig presets"""
    
    def test_aggressive_config(self):
        """Test aggressive configuration"""
        config = RiskConfig.create_aggressive()
        assert config.max_daily_loss_pct == 0.05
        assert config.max_risk_per_trade_pct == 0.015
        assert config.max_gross_exposure_pct == 0.5
        assert config.use_kelly == True
        assert config.kelly_fraction == 0.25
    
    def test_conservative_config(self):
        """Test conservative configuration"""
        config = RiskConfig.create_conservative()
        assert config.max_daily_loss_pct == 0.02
        assert config.max_risk_per_trade_pct == 0.005
        assert config.kelly_fraction == 0.15


class TestDailyGrowthEngine:
    """Test DGE position sizing and risk management"""
    
    @pytest.fixture
    def dge(self):
        """Create DGE instance with aggressive config"""
        config = RiskConfig.create_aggressive()
        return DailyGrowthEngine(config)
    
    def test_position_sizing_fixed_risk(self, dge):
        """Test position sizing with fixed fractional risk (no Kelly)"""
        # Disable Kelly
        dge.config.use_kelly = False
        
        capital = 10_000_000  # 10M KRW
        price = 100_000
        stop_loss = 95_000  # 5% stop
        
        size = dge.calculate_position_size(
            capital=capital,
            price=price,
            stop_loss_price=stop_loss,
            regime="GREEN"
        )
        
        # Expected: 1.5% of 10M = 150K risk
        # SL distance = 5% = 0.05
        # Position = 150K / 0.05 = 3M
        expected_size = (capital * 0.015) / 0.05
        assert abs(size - expected_size) < 1000
    
    def test_position_sizing_with_kelly(self, dge):
        """Test position sizing with Kelly adjustment"""
        dge.config.use_kelly = True
        
        capital = 10_000_000
        price = 100_000
        stop_loss = 95_000
        
        # Good strategy: 60% win rate, 2:1 payoff
        strategy_stats = {
            'win_rate': 0.6,
            'payoff_ratio': 2.0
        }
        
        size = dge.calculate_position_size(
            capital=capital,
            price=price,
            stop_loss_price=stop_loss,
            strategy_stats=strategy_stats,
            regime="GREEN"
        )
        
        # Kelly f* = 0.4, quarter-Kelly = 0.1
        # Kelly size = 10M * 0.1 = 1M
        # Risk-based = 3M (from previous test)
        # Final = min(1M, 3M) = 1M
        # Max cap = 10M * 0.15 = 1.5M
        # Result = min(1M, 1.5M) = 1M
        assert size > 0
        assert size <= capital * 0.15  # Max position size
    
    def test_regime_multiplier_green(self, dge):
        """Test regime multiplier for GREEN market"""
        capital = 10_000_000
        price = 100_000
        stop_loss = 95_000
        
        size_green = dge.calculate_position_size(
            capital=capital,
            price=price,
            stop_loss_price=stop_loss,
            regime="GREEN"
        )
        
        assert size_green > 0
    
    def test_regime_multiplier_yellow(self, dge):
        """Test regime multiplier for YELLOW market (reduced size)"""
        capital = 10_000_000
        price = 100_000
        stop_loss = 95_000
        
        size_green = dge.calculate_position_size(
            capital=capital, price=price, stop_loss_price=stop_loss, regime="GREEN"
        )
        size_yellow = dge.calculate_position_size(
            capital=capital, price=price, stop_loss_price=stop_loss, regime="YELLOW"
        )
        
        # Yellow should be 50% of green (default multiplier)
        assert abs(size_yellow - size_green * 0.5) < 1000
    
    def test_regime_multiplier_red(self, dge):
        """Test regime multiplier for RED market (no trading)"""
        capital = 10_000_000
        price = 100_000
        stop_loss = 95_000
        
        size_red = dge.calculate_position_size(
            capital=capital, price=price, stop_loss_price=stop_loss, regime="RED"
        )
        
        # Red should return 0 (no trading)
        assert size_red == 0
    
    def test_kill_switch_activation(self, dge):
        """Test kill switch activates on daily loss limit"""
        capital = 10_000_000
        max_loss = capital * dge.config.max_daily_loss_pct  # 5% = 500K
        
        # Simulate losses
        dge.risk_manager.update_pnl(-max_loss, capital)
        
        # Kill switch should be active
        assert dge.risk_manager.is_kill_switch_active == True
        
        # Position sizing should return 0
        size = dge.calculate_position_size(
            capital=capital,
            price=100_000,
            stop_loss_price=95_000,
            regime="GREEN"
        )
        assert size == 0
    
    def test_kill_switch_reset(self, dge):
        """Test kill switch resets daily"""
        capital = 10_000_000
        
        # Activate kill switch
        dge.risk_manager.update_pnl(-capital * 0.05, capital)
        assert dge.risk_manager.is_kill_switch_active == True
        
        # Reset
        dge.reset_daily()
        assert dge.risk_manager.is_kill_switch_active == False
        assert dge.risk_manager.daily_realized_pnl == 0


class TestEdgeCases:
    """Test edge cases and error handling"""
    
    def test_zero_capital(self):
        """Test with zero capital"""
        config = RiskConfig()
        dge = DailyGrowthEngine(config)
        
        size = dge.calculate_position_size(
            capital=0,
            price=100_000,
            stop_loss_price=95_000
        )
        # Should handle gracefully
        assert size >= 0
    
    def test_invalid_stop_loss(self):
        """Test with invalid stop loss (above entry price for long)"""
        config = RiskConfig()
        dge = DailyGrowthEngine(config)
        
        # Stop loss above entry price
        size = dge.calculate_position_size(
            capital=10_000_000,
            price=100_000,
            stop_loss_price=105_000
        )
        # Should return conservative default or 0
        assert size >= 0
    
    def test_unknown_regime(self):
        """Test with unknown regime string"""
        config = RiskConfig()
        dge = DailyGrowthEngine(config)
        
        size = dge.calculate_position_size(
            capital=10_000_000,
            price=100_000,
            stop_loss_price=95_000,
            regime="UNKNOWN"
        )
        # Should default to GREEN behavior
        assert size > 0


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
