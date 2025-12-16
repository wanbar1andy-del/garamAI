"""
Surfing Brain Module
The central intelligence unit that orchestrates Market Regime, Risk Management, and Strategy Execution.
"""

import sys
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Dict, Any
import pandas as pd

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from alpha_lab.regime.market_regime import MarketRegimeDetector, MarketState, RegimeMetrics
from alpha_lab.risk.exit_engine import ExitEngine, ExitParams
from alpha_lab.risk.position_sizer import PositionSizer

@dataclass
class TradeInstructions:
    """Complete instructions for a trade execution"""
    action: str             # 'BUY', 'SELL', 'HOLD', 'EXIT'
    quantity: int           # Number of shares
    entry_price: float      # Planned entry price
    stop_price: float       # Initial stop loss
    target_price: float     # Initial take profit
    regime: MarketState     # Current market regime
    reason: str             # Explanation for the decision

class SurfingBrain:
    """
    Strategy Supervisor that tells strategies HOW to trade based on WHERE the market is.
    """
    
    def __init__(self):
        self.regime_detector = MarketRegimeDetector()
        self.exit_engine = ExitEngine()
        self.position_sizer = PositionSizer()
        self.current_regime_metrics: Optional[RegimeMetrics] = None

    def assess_market(self, prices: pd.Series, high: pd.Series = None, low: pd.Series = None, close: pd.Series = None) -> MarketState:
        """
        Update and return the current market regime.
        """
        self.current_regime_metrics = self.regime_detector.get_current_state(prices, high, low, close)
        if self.current_regime_metrics:
            return self.current_regime_metrics.state
        return MarketState.YELLOW # Default to caution if unknown

    def get_trade_instructions(self, 
                             symbol: str, 
                             entry_price: float, 
                             equity: float, 
                             risk_pct: float = 0.01, 
                             atr: float = None,
                             direction: str = 'long') -> TradeInstructions:
        """
        Generate complete trade instructions based on current regime and risk parameters.
        """
        # 1. Get Regime
        regime = self.current_regime_metrics.state if self.current_regime_metrics else MarketState.YELLOW
        
        # 2. Check if we should trade at all
        if regime == MarketState.RED and direction == 'long':
            return TradeInstructions(
                action='HOLD',
                quantity=0,
                entry_price=entry_price,
                stop_price=0.0,
                target_price=0.0,
                regime=regime,
                reason="RED Regime: No new long entries allowed"
            )
            
        # 3. Calculate Exit Levels
        # If ATR not provided, we can't calculate stops properly. 
        # In a real scenario, we might calculate it here, but for now assume it's passed or use a fallback.
        if atr is None:
            # Fallback: 2% of price as ATR proxy if missing (dangerous, but prevents crash)
            atr = entry_price * 0.02 
            
        exit_params = self.exit_engine.calculate_initial_levels(entry_price, atr, regime, direction)
        
        # 4. Calculate Position Size
        quantity = self.position_sizer.calculate_quantity(
            equity=equity,
            risk_per_trade_pct=risk_pct,
            entry_price=entry_price,
            stop_price=exit_params.stop_price,
            regime=regime
        )
        
        if quantity == 0:
             return TradeInstructions(
                action='HOLD',
                quantity=0,
                entry_price=entry_price,
                stop_price=0.0,
                target_price=0.0,
                regime=regime,
                reason="Calculated quantity is zero (Risk too high or Regime restriction)"
            )

        return TradeInstructions(
            action='BUY' if direction == 'long' else 'SELL',
            quantity=quantity,
            entry_price=entry_price,
            stop_price=exit_params.stop_price,
            target_price=exit_params.target_price,
            regime=regime,
            reason=f"Approved in {regime.value} regime"
        )

    def should_trade(self, strategy_name: str) -> bool:
        """
        Check if a specific strategy is allowed in the current regime.
        (Can be expanded with strategy-specific rules)
        """
        if not self.current_regime_metrics:
            return True # Default allow if no data
            
        regime = self.current_regime_metrics.state
        
        # Example Rules:
        if strategy_name == 'MOMENTUM' and regime == MarketState.RED:
            return False # Don't trade momentum in bear market
            
        if strategy_name == 'MEAN_REVERSION' and regime == MarketState.GREEN:
            # Maybe allow, but be careful
            return True
            
        return True
