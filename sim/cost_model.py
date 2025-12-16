"""
Cost Model
Realistic transaction cost modeling for backtesting.
"""

import yaml
from pathlib import Path
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

class Trade:
    """Simple trade representation for cost calculation"""
    def __init__(self, 
                 notional: float,
                 volatility: float = 0.02,
                 volume_pct: float = 0.001):
        """
        Args:
            notional: Trade size in currency units
            volatility: Asset volatility (annualized)
            volume_pct: Trade size as % of daily volume
        """
        self.notional = abs(notional)
        self.volatility = volatility
        self.volume_pct = volume_pct

class CostModel:
    """
    Transaction cost model for realistic backtesting.
    
    Includes:
    - Commission costs
    - Bid-ask spread slippage
    - Market impact (volume-based)
    - Volatility-adjusted slippage
    """
    
    def __init__(self, market: str = "kr_intraday", config_path: Optional[Path] = None):
        """
        Initialize cost model.
        
        Args:
            market: Market type ('kr_intraday', 'kr_swing', 'us_intraday', 'us_swing')
            config_path: Path to cost_config.yaml (optional)
        """
        self.market = market
        
        # Load configuration
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "cost_config.yaml"
        
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Get market-specific config
        if market not in self.config:
            logger.warning(f"Market '{market}' not in config, using kr_intraday defaults")
            market = "kr_intraday"
        
        self.market_config = self.config[market]
        self.slippage_config = self.config.get('slippage_model', {})
        
        logger.info(f"CostModel initialized for {market}")
        
    def calculate_commission(self, notional: float) -> float:
        """
        Calculate commission cost.
        
        Args:
            notional: Trade size in currency units
            
        Returns:
            Commission cost
        """
        commission_rate = self.market_config['commission_rate']
        min_commission = self.market_config['min_commission']
        
        commission = abs(notional) * commission_rate
        return max(commission, min_commission)
    
    def calculate_slippage(self, 
                          notional: float, 
                          volatility: float = 0.02,
                          volume_pct: float = 0.001) -> float:
        """
        Calculate slippage cost with volatility and volume adjustments.
        
        Args:
            notional: Trade size in currency units
            volatility: Asset volatility (annualized, e.g., 0.02 = 2%)
            volume_pct: Trade size as % of daily volume (e.g., 0.01 = 1%)
            
        Returns:
            Slippage cost
        """
        # Base slippage in basis points
        base_slippage_bps = self.market_config['slippage_bps']
        
        # Volatility adjustment
        vol_multiplier = self.slippage_config.get('volatility_multiplier', 1.5)
        vol_adjustment = 1.0 + (volatility / 0.02 - 1.0) * (vol_multiplier - 1.0)
        
        # Volume adjustment (market impact)
        volume_threshold = self.slippage_config.get('volume_threshold', 0.01)
        if volume_pct > volume_threshold:
            large_order_penalty = self.slippage_config.get('large_order_penalty', 2.0)
            volume_adjustment = 1.0 + (volume_pct / volume_threshold - 1.0) * (large_order_penalty - 1.0)
        else:
            volume_adjustment = 1.0
        
        # Total slippage
        adjusted_slippage_bps = base_slippage_bps * vol_adjustment * volume_adjustment
        slippage = abs(notional) * (adjusted_slippage_bps / 10000)
        
        return slippage
    
    def calculate_market_impact(self, notional: float, volume_pct: float = 0.001) -> float:
        """
        Calculate market impact cost.
        
        Args:
            notional: Trade size in currency units
            volume_pct: Trade size as % of daily volume
            
        Returns:
            Market impact cost
        """
        impact_factor = self.market_config['market_impact_factor']
        
        # Square root model: impact ~ sqrt(volume_pct)
        impact = abs(notional) * impact_factor * (volume_pct ** 0.5)
        
        return impact
    
    def total_cost(self, trade: Trade) -> float:
        """
        Calculate total transaction cost.
        
        Args:
            trade: Trade object with notional, volatility, volume_pct
            
        Returns:
            Total cost (commission + slippage + market impact)
        """
        commission = self.calculate_commission(trade.notional)
        slippage = self.calculate_slippage(trade.notional, trade.volatility, trade.volume_pct)
        market_impact = self.calculate_market_impact(trade.notional, trade.volume_pct)
        
        total = commission + slippage + market_impact
        
        logger.debug(f"Total cost for {trade.notional:,.0f}: "
                    f"commission={commission:.2f}, slippage={slippage:.2f}, "
                    f"impact={market_impact:.2f}, total={total:.2f}")
        
        return total
    
    def cost_as_percentage(self, trade: Trade) -> float:
        """
        Calculate total cost as percentage of notional.
        
        Args:
            trade: Trade object
            
        Returns:
            Cost as percentage (e.g., 0.001 = 0.1%)
        """
        if trade.notional == 0:
            return 0.0
        
        return self.total_cost(trade) / trade.notional
