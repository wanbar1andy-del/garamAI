"""
Trailing Stop + Time-based Exit Template for DGE Aggressive v0.1

This exit logic implements:
1. Fixed R:R target with trailing stop
2. Time-based exit if no meaningful profit
3. Standard stop-loss protection
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from garam.research.regime.miracle_engine import ExitTemplate, Trade


class FixedTargetWithTrail(ExitTemplate):
    """
    Trailing Stop + Time Exit Strategy
    
    Exit Criteria:
    1. Take Profit: Price reaches initial R:R target (e.g., 2.5:1)
    2. Trailing Stop: After reaching trail_start_R profit, trail SL to trail_floor_R
    3. Time Stop: Exit if no meaningful profit after N bars
    4. Stop Loss: Hard stop at initial risk level
    
    Parameters:
        - rr_init: Initial R:R ratio for TP (default: 2.5)
        - trail_start_R: Profit level to start trailing (default: 1.5R)
        - trail_floor_R: Trailing stop floor (default: 0.5R, i.e., breakeven+)
        - time_stop_bars: Bars to wait before time stop (default: 16)
        - profit_target: Override with fixed % if provided
        - stop_loss: Override with fixed % if provided
    """
    
    def check_exit(self, row: pd.Series, trade: Trade, context: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Check if any exit condition is met.
        
        Returns:
            (should_exit: bool, reason: str)
        """
        close = row.get('close', 0.0)
        timestamp = row.name
        
        # Calculate bars since entry
        bars_since_entry = context.get('bars_since_entry', 0)
        context['bars_since_entry'] = bars_since_entry + 1
        
        # Get parameters
        rr_init = self.params.get('rr_init', 2.5)
        trail_start_R = self.params.get('trail_start_R', 1.5)
        trail_floor_R = self.params.get('trail_floor_R', 0.5)
        time_stop_bars = self.params.get('time_stop_bars', 16)
        
        # Use override params if provided
        profit_target_pct = self.params.get('profit_target', None)
        stop_loss_pct = self.params.get('stop_loss', None)
        
        # Calculate initial risk (distance from entry to initial SL)
        # Assume SL was set at entry and stored in context or trade metadata
        initial_sl = context.get('initial_sl', trade.entry_price * 0.99)  # Fallback: 1% below entry
        initial_risk = abs(trade.entry_price - initial_sl)
        
        # === 1. STOP LOSS CHECK ===
        if trade.side == 1:  # Long
            if close <= initial_sl:
                return (True, "StopLoss")
        else:  # Short
            if close >= initial_sl:
                return (True, "StopLoss")
        
        # === 2. TAKE PROFIT CHECK (Initial R:R) ===
        current_pnl = (close - trade.entry_price) * trade.side
        current_R = current_pnl / initial_risk if initial_risk > 0 else 0
        
        if profit_target_pct:
            # Use fixed % if provided
            pnl_pct = current_pnl / trade.entry_price
            if trade.side == 1 and pnl_pct >= profit_target_pct:
                return (True, "TakeProfit_Fixed")
            elif trade.side == -1 and pnl_pct >= profit_target_pct:
                return (True, "TakeProfit_Fixed")
        else:
            # Use R:R ratio
            if current_R >= rr_init:
                return (True, f"TakeProfit_{rr_init}R")
        
        # === 3. TRAILING STOP CHECK ===
        if current_R >= trail_start_R:
            # Start trailing
            trail_sl = trade.entry_price + (trail_floor_R * initial_risk * trade.side)
            
            if trade.side == 1:  # Long
                if close <= trail_sl:
                    return (True, f"TrailingStop_{trail_floor_R}R")
            else:  # Short
                if close >= trail_sl:
                    return (True, f"TrailingStop_{trail_floor_R}R")
        
        # === 4. TIME STOP CHECK ===
        if bars_since_entry >= time_stop_bars:
            # Check if we have at least 0.5R profit
            if current_R < 0.5:
                return (True, f"TimeStop_{time_stop_bars}bars")
        
        return (False, "")


# Alias for compatibility
TimeStopExit = FixedTargetWithTrail
