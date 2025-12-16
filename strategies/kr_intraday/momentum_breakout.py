"""
Momentum Breakout Strategy
Trades breakouts from consolidation ranges with volume confirmation.
"""

from typing import Optional, List
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from collections import deque

from .base_strategy import BaseIntradayStrategy, Signal, Position, Action
from sim.test_account import TradeExpectation

class MomentumBreakoutStrategy(BaseIntradayStrategy):
    """
    Momentum Breakout Strategy
    
    Entry: 15min consolidation (range < 1%), volume spike > 1.5x, breakout
    Exit: Target 2R, Stop -1R, Trailing stop after 1.5R
    """
    
    def __init__(self, account, config):
        super().__init__(account, config, "MOMENTUM_BREAKOUT")
        
        # Strategy parameters
        self.consolidation_bars = config.get('consolidation_bars', 15)
        self.max_range_pct = config.get('max_range_pct', 0.01)  # 1%
        self.volume_multiplier = config.get('volume_multiplier', 1.5)
        self.target_r = config.get('target_r', 2.0)
        self.trailing_trigger_r = config.get('trailing_trigger_r', 1.5)
        self.max_holding_minutes = config.get('max_holding_minutes', 180)
        
        # State tracking
        self.price_history: deque = deque(maxlen=self.consolidation_bars)
        self.volume_history: deque = deque(maxlen=20)  # For avg volume
        self.in_consolidation = False
        self.consolidation_high = None
        self.consolidation_low = None
        
    def on_bar(self, bar: pd.Series, timestamp: datetime) -> Optional[Signal]:
        """Process bar and generate signal"""
        # Update history
        self.price_history.append({
            'high': bar['high'],
            'low': bar['low'],
            'close': bar['close']
        })
        self.volume_history.append(bar['volume'])
        
        # Need enough history
        if len(self.price_history) < self.consolidation_bars:
            return None
            
        # Check for consolidation
        self._check_consolidation()
        
        # If in consolidation, check for breakout
        if self.in_consolidation:
            return self._check_breakout(bar, timestamp)
            
        return None
        
    def _check_consolidation(self):
        """Check if recent bars form a consolidation"""
        highs = [p['high'] for p in self.price_history]
        lows = [p['low'] for p in self.price_history]
        
        range_high = max(highs)
        range_low = min(lows)
        range_mid = (range_high + range_low) / 2
        
        range_pct = (range_high - range_low) / range_mid
        
        if range_pct <= self.max_range_pct:
            self.in_consolidation = True
            self.consolidation_high = range_high
            self.consolidation_low = range_low
        else:
            self.in_consolidation = False
            
    def _check_breakout(self, bar: pd.Series, timestamp: datetime) -> Optional[Signal]:
        """Check for breakout with volume confirmation"""
        if not self.in_consolidation:
            return None
            
        current_price = bar['close']
        current_volume = bar['volume']
        
        # Calculate average volume
        avg_volume = np.mean(list(self.volume_history)) if len(self.volume_history) > 0 else 0
        
        # Volume spike check
        if avg_volume == 0 or current_volume < avg_volume * self.volume_multiplier:
            return None
            
        # Breakout up
        if current_price > self.consolidation_high:
            entry_price = current_price
            stop_price = self.consolidation_low
            range_height = self.consolidation_high - self.consolidation_low
            target_price = entry_price + range_height * self.target_r
            
            self.in_consolidation = False  # Reset
            
            return Signal(
                direction="LONG",
                entry_price=entry_price,
                stop_price=stop_price,
                target_price=target_price,
                timestamp=timestamp,
                reason=f"Breakout up, vol {current_volume/avg_volume:.1f}x"
            )
            
        # Breakout down
        elif current_price < self.consolidation_low:
            entry_price = current_price
            stop_price = self.consolidation_high
            range_height = self.consolidation_high - self.consolidation_low
            target_price = entry_price - range_height * self.target_r
            
            self.in_consolidation = False  # Reset
            
            return Signal(
                direction="SHORT",
                entry_price=entry_price,
                stop_price=stop_price,
                target_price=target_price,
                timestamp=timestamp,
                reason=f"Breakout down, vol {current_volume/avg_volume:.1f}x"
            )
            
        return None
        
    def on_position_update(self, position: Position, bar: pd.Series) -> Optional[Action]:
        """Check exit conditions with trailing stop"""
        current_price = bar['close']
        self.update_position_excursions(position, current_price)
        
        # Time stop
        holding_minutes = (bar.name - position.entry_time).total_seconds() / 60
        if holding_minutes >= self.max_holding_minutes:
            return Action("EXIT", current_price, "Time stop")
            
        # Calculate current R
        risk_per_share = abs(position.entry_price - position.stop_price)
        if position.direction == "LONG":
            current_r = (current_price - position.entry_price) / risk_per_share
        else:
            current_r = (position.entry_price - current_price) / risk_per_share
            
        # Trailing stop activation
        if current_r >= self.trailing_trigger_r:
            # Lock in 1R profit
            if position.direction == "LONG":
                new_stop = position.entry_price + risk_per_share * 1.0
                if new_stop > position.stop_price:
                    position.stop_price = new_stop
            else:
                new_stop = position.entry_price - risk_per_share * 1.0
                if new_stop < position.stop_price:
                    position.stop_price = new_stop
                    
        # Target hit
        if position.direction == "LONG":
            if current_price >= position.target_price:
                return Action("EXIT", current_price, "Target hit")
            if current_price <= position.stop_price:
                return Action("EXIT", current_price, "Stop hit")
        else:
            if current_price <= position.target_price:
                return Action("EXIT", current_price, "Target hit")
            if current_price >= position.stop_price:
                return Action("EXIT", current_price, "Stop hit")
                
        return None
        
    def create_expectation(self, trade_id: str, signal: Signal) -> TradeExpectation:
        """Create trade expectation"""
        return TradeExpectation(
            trade_id=trade_id,
            expected_direction=signal.direction,
            expected_R_range=(0.8, 3.0),
            expected_holding_period=90,  # 90 minutes average
            expected_regime="UNKNOWN",
            notes=signal.reason
        )
