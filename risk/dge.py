"""
Daily Growth Engine (DGE)
Core module for Risk Management and Position Sizing.
Implements Kelly-based sizing, global risk constraints, and portfolio optimization.
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from enum import Enum

# Use string enum for easier serialization if needed, or just standard Enum
class MarketRegime(str, Enum):
    GREEN = "GREEN"
    YELLOW = "YELLOW"
    RED = "RED"

@dataclass
class RiskConfig:
    # Global Constraints
    max_daily_loss_pct: float = 0.03       # e.g. 3% hard stop
    max_gross_exposure_pct: float = 1.0    # e.g. 100% (no leverage)
    
    # Per-Trade Constraints
    max_risk_per_trade_pct: float = 0.01   # e.g. 1% risk of equity per trade
    max_position_size_pct: float = 0.10    # e.g. Max 10% allocation per symbol
    
    # Kelly Settings
    use_kelly: bool = True
    kelly_fraction: float = 0.25           # "Quarter Kelly" is standard conservative
    
    # Growth Target (for reference/optimization)
    target_daily_growth: float = 0.004     # 0.4% per day
    
    @classmethod
    def create_aggressive(cls):
        """Create aggressive DGE config for testing (DGE Aggressive v0.1)"""
        return cls(
            max_daily_loss_pct=0.05,         # 5% max daily loss
            max_risk_per_trade_pct=0.015,    # 1.5% per trade
            max_gross_exposure_pct=0.5,      # 50% max deployed
            max_position_size_pct=0.15,       # Max 15% per symbol
            use_kelly=True,
            kelly_fraction=0.25,
            target_daily_growth=0.004
        )
    
    @classmethod
    def create_conservative(cls):
        """Create conservative DGE config"""
        return cls(
            max_daily_loss_pct=0.02,
            max_risk_per_trade_pct=0.005,
            max_gross_exposure_pct=0.8,
            use_kelly=True,
            kelly_fraction=0.15,            # Fractional Kelly
            target_daily_growth=0.002
        )

class KellySizer:
    """
    Calculates optimal position fraction (f*) based on Kelly Criterion.
    """
    
    @staticmethod
    def calculate_f_star(win_rate: float, payoff_ratio: float) -> float:
        """
        Classic Kelly: f* = p - q/b
        p: win rate, q: 1-p, b: payoff ratio (avg_win / avg_loss)
        """
        if payoff_ratio <= 0: return 0.0
        return win_rate - (1 - win_rate) / payoff_ratio

    @staticmethod
    def calculate_f_star_log(mu: float, sigma: float) -> float:
        """
        Continuous approximation: f* = mu / sigma^2
        mu: expected excess return, sigma: volatility
        """
        if sigma <= 0: return 0.0
        return mu / (sigma ** 2)

class RiskManager:
    """
    Enforces global risk limits (Daily Loss, Exposure).
    """
    def __init__(self, config: RiskConfig):
        self.config = config
        self.daily_realized_pnl = 0.0
        self.current_gross_exposure = 0.0
        self.is_kill_switch_active = False

    def reset_daily(self):
        self.daily_realized_pnl = 0.0
        self.is_kill_switch_active = False

    def update_pnl(self, pnl_amount: float, capital: float):
        self.daily_realized_pnl += pnl_amount
        
        # Check Kill Switch
        current_dd_pct = self.daily_realized_pnl / capital
        if current_dd_pct <= -self.config.max_daily_loss_pct:
            self.is_kill_switch_active = True

    def check_can_trade(self) -> bool:
        return not self.is_kill_switch_active

class DailyGrowthEngine:
    """
    Orchestrates Sizing and Risk Management.
    """
    def __init__(self, risk_config: RiskConfig):
        self.config = risk_config
        self.sizer = KellySizer()
        self.risk_manager = RiskManager(risk_config)
        
        # Regime Multipliers (Default)
        self.regime_multipliers = {
            MarketRegime.GREEN: 1.0,
            MarketRegime.YELLOW: 0.5,
            MarketRegime.RED: 0.0
        }

    def set_regime_multiplier(self, regime: MarketRegime, multiplier: float):
        self.regime_multipliers[regime] = multiplier

    def calculate_position_size(self, 
                                capital: float, 
                                price: float,
                                stop_loss_price: Optional[float],
                                strategy_stats: Dict[str, float] = None,
                                regime: str = "GREEN") -> float:
        """
        Returns position size (Notional Value) based on Risk & Kelly.
        
        Args:
            capital: Current account equity
            price: Current asset price
            stop_loss_price: Stop loss level (required for risk-based sizing)
            strategy_stats: Dict with 'win_rate', 'payoff_ratio' or 'mu', 'sigma'
            regime: Current market regime (GREEN, YELLOW, RED)
            
        Returns:
            float: Target position value (Price * Qty)
        """
        # 0. Pre-check: Kill Switch
        if not self.risk_manager.check_can_trade():
            return 0.0
            
        # 0.1 Regime Check
        # Convert string to Enum if needed, default to GREEN if unknown
        try:
            regime_enum = MarketRegime(regime)
        except ValueError:
            regime_enum = MarketRegime.GREEN
            
        regime_mult = self.regime_multipliers.get(regime_enum, 1.0)
        if regime_mult <= 0:
            return 0.0

        # 1. Base Sizing: Risk-Based (Fixed Fractional Risk)
        # Risk Amount = Capital * max_risk_per_trade_pct
        # Position Size = Risk Amount / (Entry - SL) * Entry
        
        risk_amt = capital * self.config.max_risk_per_trade_pct
        
        if stop_loss_price and price > 0:
            sl_dist_pct = abs(price - stop_loss_price) / price
            if sl_dist_pct > 0:
                risk_based_size = risk_amt / sl_dist_pct
            else:
                risk_based_size = 0.0 # Invalid SL
        else:
            # Fallback if no SL: Use a conservative fixed allocation (e.g. 5%)
            # Or treat volatility as SL proxy
            risk_based_size = capital * 0.05 

        # 2. Kelly Adjustment (Optional)
        kelly_size = float('inf')
        if self.config.use_kelly and strategy_stats:
            f_star = 0.0
            if 'win_rate' in strategy_stats and 'payoff_ratio' in strategy_stats:
                f_star = self.sizer.calculate_f_star(
                    strategy_stats['win_rate'], 
                    strategy_stats['payoff_ratio']
                )
            elif 'mu' in strategy_stats and 'sigma' in strategy_stats:
                f_star = self.sizer.calculate_f_star_log(
                    strategy_stats['mu'], 
                    strategy_stats['sigma']
                )
            
            # Apply Fraction
            f_used = f_star * self.config.kelly_fraction
            
            # If f_used is negative, don't trade
            if f_used <= 0:
                return 0.0
                
            # Kelly suggests allocating f_used % of capital
            kelly_size = capital * f_used
            
        # 3. Combine Logic: Min(Risk_Based, Kelly, Max_Cap)
        # We take the MIN of Risk-Based and Kelly-Based to be safe.
        
        base_size = min(risk_based_size, kelly_size)

        # 4. Apply Hard Caps
        max_size = capital * self.config.max_position_size_pct
        final_size = min(base_size, max_size)
        
        # 5. Apply Regime Multiplier
        final_size *= regime_mult
        
        return final_size

    def update_daily_status(self, pnl: float, capital: float):
        self.risk_manager.update_pnl(pnl, capital)
        
    def reset_daily(self):
        self.risk_manager.reset_daily()
