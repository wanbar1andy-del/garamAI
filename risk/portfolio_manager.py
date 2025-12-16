"""
Portfolio Manager for GARAM DGE

Responsibilities:
1. Manage capital allocation between Core and Overlay books.
2. Manage multiple DailyGrowthEngine instances (one per symbol).
3. Apply HeatScore-based dynamic risk adjustment.
4. Track portfolio-level exposure and risk limits.
"""

import logging
from typing import Dict, List, Optional
import pandas as pd
import numpy as np

from garam.risk.dge import DailyGrowthEngine, RiskConfig
from garam.risk.acceleration_engine import AccelerationEngine

logger = logging.getLogger("PortfolioManager")

class PortfolioManager:
    def __init__(self, initial_capital: float, risk_config: Dict = None):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.risk_config = risk_config or {}
        
        # Books
        self.core_allocation = 0.5  # Default 50%
        self.overlay_allocation = 0.3 # Default 30% (Dynamic)
        self.cash_buffer = 0.2      # Default 20%
        
        # Engines
        self.engines: Dict[str, DailyGrowthEngine] = {}
        self.positions: Dict[str, Dict] = {} # {symbol: {qty, avg_price, current_price}}
        self.accel_engine = AccelerationEngine() # Acceleration Engine
        
        # State
        self.heat_score = 0.0
        self.daily_pnl = 0.0
        self.max_portfolio_exposure = self.risk_config.get('max_portfolio_exposure', 0.8) # 80% Hard cap
        
        # Diagnostics
        self.rejection_stats = {
            'symbol_not_registered': 0,
            'dge_zero_size': 0,
            'overlay_limit_hit': 0,
            'small_wave_filter': 0,
            'heat_score_cut': 0
        }

    # ... (update_heat_score, _adjust_allocation, register_symbol, on_day_start omitted) ...

    def calculate_position_size(self, symbol: str, price: float, stop_loss_price: float, 
                              strategy_stats: Optional[Dict] = None, regime: str = 'GREEN',
                              market_data: Optional[pd.DataFrame] = None,
                              sector_data: Optional[Dict] = None) -> float:
        """
        Calculate position size for a symbol, considering:
        1. Symbol-specific DGE logic (Kelly, Risk%)
        2. Portfolio-level Overlay allocation limit
        3. HeatScore multiplier
        4. Acceleration Factor (Physics of Profit)
        """
        if symbol not in self.engines:
            self.rejection_stats['symbol_not_registered'] += 1
            return 0.0
            
        engine = self.engines[symbol]
        
        # 1. Base DGE Size (Notional)
        # Apply HeatScore multiplier to DGE
        # Bull (>0.7) -> 1.2x, Bear (<-0.7) -> 0.5x
        heat_mult = 1.0
        if self.heat_score > 0.7: heat_mult = 1.2
        elif self.heat_score < -0.7: heat_mult = 0.5
        
        # [AGGRESSIVE UPDATE] Boost multiplier in aggressive mode
        if self.risk_config.get('aggressive_mode', False):
            heat_mult *= 1.5
            
        # [ACCELERATION UPDATE] Apply Acceleration Factor
        accel_factor = 1.0
        if market_data is not None:
            accel_res = self.accel_engine.calculate_acceleration(symbol, market_data, sector_data)
            accel_factor = accel_res['factor']
            if accel_res['is_accelerated']:
                # logger.info(f"🚀 Acceleration Active for {symbol}: {accel_factor:.2f}x (Scores: {accel_res['scores']})")
                pass
        
        # Combine multipliers
        total_mult = heat_mult * accel_factor
        
        # Cap total multiplier to avoid recklessness (e.g. max 2.5x base risk)
        total_mult = min(2.5, total_mult)
        
        base_size = engine.calculate_position_size(
            capital=self.current_capital, 
            price=price,
            stop_loss_price=stop_loss_price,
            strategy_stats=strategy_stats,
            regime=regime
        )
        
        if base_size <= 0:
            self.rejection_stats['dge_zero_size'] += 1
            return 0.0
        
        adjusted_size = base_size * total_mult
        
        # 2. Portfolio Limits
        # Check available overlay capital
        overlay_capital = self.current_capital * self.overlay_allocation
        current_overlay_used = self.get_current_overlay_exposure()
        
        available_overlay = overlay_capital - current_overlay_used
        
        if available_overlay <= 0:
            self.rejection_stats['overlay_limit_hit'] += 1
            return 0.0
            
        final_size = min(adjusted_size, available_overlay)
        
        # 3. Small Wave Filter (Cost Efficiency)
        if not self.risk_config.get('disable_filters', False):
            risk_amt = abs(price - stop_loss_price) / price
            if risk_amt < 0.0075: # If risk < 0.75%
                 self.rejection_stats['small_wave_filter'] += 1
                 pass 

        return final_size
        
    def update_heat_score(self, heat_score: float):
        """
        Update HeatScore and adjust allocation
        HeatScore: -2.0 (Bear) to +2.0 (Bull)
        """
        self.heat_score = max(-2.0, min(2.0, heat_score))
        self._adjust_allocation()
        
    def _adjust_allocation(self):
        """
        Adjust Overlay allocation based on HeatScore
        Base 30% + (Score * 10%) -> Range 10% ~ 50%
        
        [AGGRESSIVE UPDATE]
        If risk_config['aggressive_mode'] is True:
        Base 60% + (Score * 20%) -> Range 20% ~ 100%
        """
        is_aggressive = self.risk_config.get('aggressive_mode', False)
        
        if is_aggressive:
            base_ratio = 0.60
            adjustment = self.heat_score * 0.20
            self.overlay_allocation = max(0.20, min(1.00, base_ratio + adjustment))
        else:
            base_ratio = 0.30
            adjustment = self.heat_score * 0.10
            self.overlay_allocation = max(0.10, min(0.50, base_ratio + adjustment))
        
        # logger.info(f"HeatScore: {self.heat_score:.2f} -> Overlay Alloc: {self.overlay_allocation:.1%}")

    def register_symbol(self, symbol: str, config: RiskConfig):
        """Register a symbol with its own DGE instance"""
        self.engines[symbol] = DailyGrowthEngine(config)
        
    def on_day_start(self):
        """Reset daily stats for all engines"""
        self.daily_pnl = 0.0
        for engine in self.engines.values():
            engine.risk_manager.reset_daily()
            
    def calculate_position_size(self, symbol: str, price: float, stop_loss_price: float, 
                              strategy_stats: Optional[Dict] = None, regime: str = 'GREEN',
                              market_data: Optional[pd.DataFrame] = None,
                              sector_data: Optional[Dict] = None) -> float:
        """
        Calculate position size for a symbol, considering:
        1. Symbol-specific DGE logic (Kelly, Risk%)
        2. Portfolio-level Overlay allocation limit
        3. HeatScore multiplier
        """
        if symbol not in self.engines:
            self.rejection_stats['symbol_not_registered'] += 1
            return 0.0
            
        engine = self.engines[symbol]
        
        # 1. Base DGE Size (Notional)
        # Apply HeatScore multiplier to DGE
        # Bull (>0.7) -> 1.2x, Bear (<-0.7) -> 0.5x
        heat_mult = 1.0
        if self.heat_score > 0.7: heat_mult = 1.2
        elif self.heat_score < -0.7: heat_mult = 0.5
        
        # [AGGRESSIVE UPDATE] Boost multiplier in aggressive mode
        if self.risk_config.get('aggressive_mode', False):
            heat_mult *= 1.5
            
        # [ACCELERATION UPDATE] Apply Acceleration Factor
        accel_factor = 1.0
        if market_data is not None:
            accel_res = self.accel_engine.calculate_acceleration(symbol, market_data, sector_data)
            accel_factor = accel_res['factor']
            if accel_res['is_accelerated']:
                # logger.info(f"🚀 Acceleration Active for {symbol}: {accel_factor:.2f}x (Scores: {accel_res['scores']})")
                pass
        
        # Combine multipliers
        total_mult = heat_mult * accel_factor
        
        # Cap total multiplier to avoid recklessness (e.g. max 2.5x base risk)
        total_mult = min(2.5, total_mult)
        
        base_size = engine.calculate_position_size(
            capital=self.current_capital, 
            price=price,
            stop_loss_price=stop_loss_price,
            strategy_stats=strategy_stats,
            regime=regime
        )
        
        if base_size <= 0:
            self.rejection_stats['dge_zero_size'] += 1
            return 0.0
        
        adjusted_size = base_size * total_mult
        
        # 2. Portfolio Limits
        # Check available overlay capital
        overlay_capital = self.current_capital * self.overlay_allocation
        current_overlay_used = self.get_current_overlay_exposure()
        
        available_overlay = overlay_capital - current_overlay_used
        
        if available_overlay <= 0:
            # logger.warning(f"Overlay capital exhausted. Used: {current_overlay_used:,.0f} / {overlay_capital:,.0f}")
            self.rejection_stats['overlay_limit_hit'] += 1
            return 0.0
            
        final_size = min(adjusted_size, available_overlay)
        
        # 3. Small Wave Filter (Cost Efficiency)
        # Expected Profit = |Price - SL| * R_Multiple (assume 2R target)
        # Cost = 0.25% of Notional
        # [AGGRESSIVE UPDATE] Disable filter if aggressive
        if not self.risk_config.get('disable_filters', False):
            risk_amt = abs(price - stop_loss_price) / price
            if risk_amt < 0.0075: # If risk < 0.75%
                 self.rejection_stats['small_wave_filter'] += 1
                 # return 0.0 # Temporarily disable to see impact, or keep enabled
                 pass 

        return final_size

    def get_current_overlay_exposure(self) -> float:
        """Calculate total gross exposure of overlay book"""
        exposure = 0.0
        for symbol, pos in self.positions.items():
            # Assume all registered symbols are Overlay
            # In future, distinguish Core vs Overlay symbols
            exposure += pos['qty'] * pos['current_price']
        return exposure

    def update_position(self, symbol: str, qty: int, price: float):
        """Update position state (called after execution)"""
        if qty == 0:
            if symbol in self.positions:
                del self.positions[symbol]
        else:
            if symbol not in self.positions:
                self.positions[symbol] = {'qty': 0, 'avg_price': 0.0, 'current_price': price}
            
            pos = self.positions[symbol]
            pos['qty'] = qty
            pos['current_price'] = price # Update current
            # Avg price logic handled by broker, here we just track exposure
            
    def update_pnl(self, pnl: float):
        """Update capital with realized PnL"""
        self.current_capital += pnl
        self.daily_pnl += pnl
        
        # Update daily loss for all engines? 
        # Currently DGE tracks symbol-specific daily loss.
        # Portfolio level daily loss check could be added here.
