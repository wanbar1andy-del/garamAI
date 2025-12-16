"""
Gap Reversal Strategy
Trades mean reversion after overnight gaps.
"""

from typing import Optional
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

from .base_strategy import BaseIntradayStrategy, Signal, Position, Action
from sim.test_account import TradeExpectation

class GapReversalStrategy(BaseIntradayStrategy):
    """
    Gap Reversal Strategy
    
    Entry: Gap > 2% from previous close, wait 30min, enter on 50% retrace
    Exit: Target 1.5R (75% gap fill), Stop -1R, Time stop 2 hours
    """
    
    def __init__(self, account, config):
        super().__init__(account, config, "GAP_REVERSAL")
        
        # Strategy parameters
        self.min_gap_pct = config.get('min_gap_pct', 0.02)  # 2%
        self.wait_minutes = config.get('wait_minutes', 30)
        self.retrace_pct = config.get('retrace_pct', 0.5)  # 50% retrace
        self.target_r = config.get('target_r', 1.5)
        self.max_holding_minutes = config.get('max_holding_minutes', 120)
        
        # State tracking
        self.prev_close = None
        self.gap_detected = False
        self.gap_direction = None
        self.gap_size = 0.0
        self.gap_time = None
        self.session_start = None
        
    def on_bar(self, bar: pd.Series, timestamp: datetime) -> Optional[Signal]:
        """Process bar and generate signal"""
        # Track session start (9:00 AM)
        if timestamp.hour == 9 and timestamp.minute == 0:
            self.session_start = timestamp
            self.gap_detected = False
            
        # Detect gap at market open
        if self.prev_close is not None and timestamp.hour == 9 and timestamp.minute == 0:
            open_price = bar['open']
            gap_pct = (open_price - self.prev_close) / self.prev_close
            
            if abs(gap_pct) >= self.min_gap_pct:
                self.gap_detected = True
                self.gap_direction = "UP" if gap_pct > 0 else "DOWN"
                self.gap_size = abs(gap_pct)
                self.gap_time = timestamp
                
        # Wait for initial volatility to settle
        if self.gap_detected and self.gap_time:
            minutes_since_gap = (timestamp - self.gap_time).total_seconds() / 60
            
            if minutes_since_gap >= self.wait_minutes:
                # Check for retrace entry
                signal = self._check_retrace_entry(bar, timestamp)
                if signal:
                    self.gap_detected = False  # Reset after entry
                    return signal
                    
        # Update previous close at end of day
        if timestamp.hour == 15 and timestamp.minute == 30:
            self.prev_close = bar['close']
            
        return None
        
    def _check_retrace_entry(self, bar: pd.Series, timestamp: datetime) -> Optional[Signal]:
        """Check if price has retraced enough for entry"""
        if self.prev_close is None or not self.gap_detected:
            return None
            
        current_price = bar['close']
        
        if self.gap_direction == "UP":
            # Gap up: enter short on retrace down
            gap_high = bar['high']
            retrace_target = self.prev_close + (gap_high - self.prev_close) * self.retrace_pct
            
            if current_price <= retrace_target:
                entry_price = current_price
                stop_price = gap_high
                target_price = entry_price - (stop_price - entry_price) * self.target_r
                
                return Signal(
                    direction="SHORT",
                    entry_price=entry_price,
                    stop_price=stop_price,
                    target_price=target_price,
                    timestamp=timestamp,
                    reason=f"Gap up {self.gap_size:.2%} retrace entry"
                )
                
        else:  # Gap down
            # Gap down: enter long on retrace up
            gap_low = bar['low']
            retrace_target = self.prev_close - (self.prev_close - gap_low) * self.retrace_pct
            
            if current_price >= retrace_target:
                entry_price = current_price
                stop_price = gap_low
                target_price = entry_price + (entry_price - stop_price) * self.target_r
                
                return Signal(
                    direction="LONG",
                    entry_price=entry_price,
                    stop_price=stop_price,
                    target_price=target_price,
                    timestamp=timestamp,
                    reason=f"Gap down {self.gap_size:.2%} retrace entry"
                )
                
        return None
        
    def on_position_update(self, position: Position, bar: pd.Series) -> Optional[Action]:
        """Check exit conditions"""
        current_price = bar['close']
        self.update_position_excursions(position, current_price)
        
        # Time stop
        holding_minutes = (bar.name - position.entry_time).total_seconds() / 60
        if holding_minutes >= self.max_holding_minutes:
            return Action("EXIT", current_price, "Time stop")
            
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
            expected_R_range=(0.5, 2.0),
            expected_holding_period=60,  # 60 minutes average
            expected_regime="UNKNOWN",
            notes=signal.reason
        )
