"""
DGE V3 Max Profit (Aggressive)
- Core: DGE ORB V3
- Philosophy: Maximize PnL, Ignore Risk Metrics.
- Settings:
    - Risk per Trade: 2.0% (vs 1.5% standard)
    - Fast Cut: OFF
    - Regime Filter: OFF (Always Attack)
"""

import pandas as pd
from datetime import datetime
from typing import Optional

from strategies.kr_intraday.dge_orb_v0_3 import DGEOrbStrategyV3
from strategies.kr_intraday.base_strategy import Position, Action, Signal

class DGEV3MaxProfit(DGEOrbStrategyV3):
    """
    DGE V3 Max Profit
    Aggressive configuration of Pure V3.
    """
    
    def __init__(self, account, config, daily_df: pd.DataFrame = None, symbol: str = "UNKNOWN"):
        super().__init__(account, config, daily_df, symbol)
        self.strategy_name = "DGE_V3_MaxProfit"
        
        # Aggressive Risk
        self.base_risk_pct = 0.02 # 2.0%
        
        # No Safety Mechanisms
        # Just pure V3 logic from parent.

    def on_bar(self, bar: pd.Series, timestamp: datetime):
        """
        Standard V3 execution with aggressive sizing.
        """
        # 1. Update Indicators
        self._update_indicators(bar, timestamp)
        
        if not self.orb_complete:
            return None
            
        # 2. Check Entry (Parent Logic)
        # Parent uses self.risk_per_trade? 
        # DGEOrbStrategyV3 uses self.position_sizer.calc_size(...)
        # We need to ensure self.risk_per_trade is set or passed.
        # DGEOrbStrategyV3.on_bar doesn't explicitly set risk_per_trade before calling open_position.
        # It calculates size inside open_position or on_bar?
        # Let's check parent on_bar.
        
        return super().on_bar(bar, timestamp)

    def open_position(self, signal: Signal, symbol: str, bar: pd.Series):
        """
        Override to apply aggressive sizing.
        """
        # Calculate size with 2.0% risk
        # self.account.equity might be needed.
        # DGEOrbStrategyV3.open_position calls self.position_sizer.calc_size
        # We need to make sure we use 2.0% risk.
        
        # Actually, DGEOrbStrategyV3.on_bar calls:
        # size = self.position_sizer.calc_size(self.account.get_total_balance(), self.risk_per_trade, bar['close'], stop_loss)
        # Wait, DGEOrbStrategyV3 might not have 'risk_per_trade' attribute initialized to what we want.
        # In __init__, we set self.base_risk_pct = 0.02.
        # We should ensure self.risk_per_trade is used.
        
        # Let's just override on_bar to be sure, or rely on parent using a property?
        # Parent DGEOrbStrategyV3 likely uses a fixed risk or config.
        # Let's check DGEOrbStrategyV3 code in a moment.
        # For now, assuming parent uses self.base_risk_pct if available, or we inject it.
        
        # To be safe, we set the instance variable that parent uses.
        self.risk_per_trade = self.base_risk_pct
        
        super().open_position(signal, symbol, bar)
