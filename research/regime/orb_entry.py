"""
ORB (Opening Range Breakout) Entry Template for DGE Aggressive v0.1

This entry logic identifies breakouts from the opening range combined with
momentum confirmation for aggressive intraday entries.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from garam.research.regime.miracle_engine import EntryTemplate


class ORBVolatilityBreakout(EntryTemplate):
    """
    Opening Range Breakout + Volatility-based Entry
    
    Entry Criteria:
    1. Price breaks above/below opening range (first N minutes)
    2. Breakout strength exceeds threshold (normalized by ATR)
    3. Short-term momentum (fs) confirms direction
   4. Sufficient stop-loss distance for risk management
    
    Parameters:
        - orb_minutes: Minutes for opening range (default: 30)
        - orb_buffer: Additional % of range to require (default: 0.2)
        - fs_thresh_long: fs threshold for long entry (default: 0.3)
        - fs_thresh_short: fs threshold for short entry (default: -0.3)
        - min_atr_multiplier: Minimum SL distance in ATR units (default: 0.5)
    """
    
    def check_entry(self, row: pd.Series, prev_row: pd.Series, context: Dict[str, Any]) -> int:
        """
        Check if ORB breakout + momentum conditions are met.
        
        Returns:
            1: Long signal
            -1: Short signal
            0: No signal
        """
        # Extract ORB indicators (should be pre-calculated in data)
        orb_high = row.get('ORB_high', None)
        orb_low = row.get('ORB_low', None)
        orb_range = row.get('ORB_range', None)
        
        if orb_high is None or orb_low is None or orb_range is None:
            return 0  # ORB not available (likely still in opening range period)
        
        # Get current price and ATR
        close = row.get('close', 0.0)
        atr = row.get('ATR_15m', row.get('ATR', 1.0))  # Use 15m ATR if available
        
        # Get momentum signal (fs)
        fs = row.get('fs', 0.0)
        
        # Get parameters
        orb_buffer = self.params.get('orb_buffer', 0.2)
        fs_thresh_long = self.params.get('fs_thresh_long', 0.3)
        fs_thresh_short = self.params.get('fs_thresh_short', -0.3)
        min_atr_mult = self.params.get('min_atr_multiplier', 0.5)
        
        # Calculate breakout thresholds
        long_breakout_level = orb_high + orb_buffer * orb_range
        short_breakdown_level = orb_low - orb_buffer * orb_range
        
        # Check Long Entry
        if close > long_breakout_level and fs >= fs_thresh_long:
            # Validate stop-loss distance
            potential_sl = orb_low
            sl_distance = close - potential_sl
            min_sl_distance = min_atr_mult * atr
            
            if sl_distance >= min_sl_distance:
                return 1  # Long signal
        
        # Check Short Entry
        elif close < short_breakdown_level and fs <= fs_thresh_short:
            # Validate stop-loss distance
            potential_sl = orb_high
            sl_distance = potential_sl - close
            min_sl_distance = min_atr_mult * atr
            
            if sl_distance >= min_sl_distance:
                return -1  # Short signal
        
        return 0  # No signal


# For backward compatibility with template naming
ImmediateBreakoutEntry = ORBVolatilityBreakout
