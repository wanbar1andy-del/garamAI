"""
DGE ORB Aggressive Strategy v0.1
Dual Horizon (Intraday ORB + Daily Trend) Strategy
"""

from typing import Optional, List, Dict
from datetime import datetime, time, timedelta
import pandas as pd
import numpy as np
from .base_strategy import BaseIntradayStrategy, Signal, Position, Action
from sim.test_account import TradeExpectation

class DGEOrbAggressiveStrategy(BaseIntradayStrategy):
    """
    DGE ORB Aggressive Strategy
    
    Short Horizon (fs): 15m ORB Momentum
    Mid Horizon (fm): Daily 20 EMA Slope
    
    State Machine: FLAT -> LONG/SHORT -> FLAT
    """
    
    def __init__(self, account, config, daily_df: pd.DataFrame = None):
        super().__init__(account, config, "DGE_ORB_AGGRESSIVE")
        
        self.daily_df = daily_df
        
        # Params
        self.orb_minutes = config.get('orb_minutes', 30)
        self.orb_buffer_pct = config.get('orb_buffer', 0.2)
        
        self.fs_thresh_long = config.get('fs_thresh_long', 0.5) # Increased from 0.3
        self.fs_thresh_short = config.get('fs_thresh_short', -0.5)
        self.fm_thresh_long = config.get('fm_thresh_long', 0.0) # Increased from -0.1 (Strict positive trend)
        self.fm_thresh_short = config.get('fm_thresh_short', 0.0)
        
        self.target_r = config.get('rr_init', 2.5)
        self.trail_start_r = config.get('trail_start_R', 1.5)
        self.time_stop_bars = config.get('time_stop_bars', 16)
        
        # State
        self.state = "FLAT" # FLAT, LONG, SHORT
        self.orb_high = None
        self.orb_low = None
        self.orb_complete = False
        self.current_date = None
        
        # Pre-calculate Daily EMA Slope if daily_df provided
        if self.daily_df is not None:
             self._calc_daily_metrics()
             
    def _calc_daily_metrics(self):
        """Calculate Daily EMA(20) Slope"""
        df = self.daily_df.copy()
        df['ema20'] = df['close'].ewm(span=20, adjust=False).mean()
        # Slope: (EMA_t - EMA_t-1) / EMA_t-1 * 100
        df['ema_slope'] = df['ema20'].pct_change() * 100
        self.daily_df = df
        
    def get_daily_fm(self, timestamp: datetime) -> float:
        """Get fm (Daily EMA Slope) for the given date (using previous close)"""
        if self.daily_df is None:
            return 0.0
            
        # Look for previous day's data
        target_date = timestamp.date()
        # Find row before target_date
        mask = self.daily_df.index < pd.Timestamp(target_date)
        if not mask.any():
            return 0.0
            
        prev_day_row = self.daily_df[mask].iloc[-1]
        return prev_day_row.get('ema_slope', 0.0)

    def on_bar(self, bar: pd.Series, timestamp: datetime) -> Optional[Signal]:
        # Reset ORB on new day
        if self.current_date != timestamp.date():
            self.current_date = timestamp.date()
            self.orb_high = -float('inf')
            self.orb_low = float('inf')
            self.orb_complete = False
            self.state = "FLAT" # Reset state daily? Or keep? Usually intraday resets.
            
        # Update ORB
        current_time = timestamp.time()
        orb_end_time = (datetime.combine(timestamp.date(), time(9, 0)) + timedelta(minutes=self.orb_minutes)).time()
        
        if current_time <= orb_end_time:
            self.orb_high = max(self.orb_high, bar['high'])
            self.orb_low = min(self.orb_low, bar['low'])
            return None
        else:
            self.orb_complete = True
            
        # If already in position, no new entry (for now, max 1 per direction usually)
        if len(self.positions) >= self.max_positions:
            return None
            
        # Calculate fs (Intraday Momentum)
        # Simplified: Breakout strength relative to ORB range
        orb_range = self.orb_high - self.orb_low
        if orb_range == 0: return None
        
        close = bar['close']
        fs = 0.0
        
        if close > self.orb_high:
            fs = (close - self.orb_high) / orb_range
        elif close < self.orb_low:
            fs = (close - self.orb_low) / orb_range # Negative
            
        # Get fm (Daily Trend)
        fm = self.get_daily_fm(timestamp)
        
        # State Machine Entry Logic
        signal = None
        
        if self.state == "FLAT":
            # LONG Entry
            if fs >= self.fs_thresh_long and fm >= self.fm_thresh_long:
                entry_price = close
                stop_price = self.orb_low # Stop at ORB Low
                target_price = entry_price + (entry_price - stop_price) * self.target_r
                
                signal = Signal("LONG", entry_price, stop_price, target_price, timestamp, 
                                f"ORB Breakout (fs={fs:.2f}, fm={fm:.2f})")
                self.state = "LONG"
                
            # SHORT Entry
            elif fs <= self.fs_thresh_short and fm <= self.fm_thresh_short:
                entry_price = close
                stop_price = self.orb_high # Stop at ORB High
                target_price = entry_price - (stop_price - entry_price) * self.target_r
                
                signal = Signal("SHORT", entry_price, stop_price, target_price, timestamp,
                                f"ORB Breakdown (fs={fs:.2f}, fm={fm:.2f})")
                self.state = "SHORT"
                
        return signal

    def on_position_update(self, position: Position, bar: pd.Series) -> Optional[Action]:
        current_price = bar['close']
        self.update_position_excursions(position, current_price)
        
        fm = self.get_daily_fm(bar.name)
        
        # Calculate current R
        risk = abs(position.entry_price - position.stop_price)
        if risk == 0: risk = 1
        
        pnl_r = 0
        if position.direction == "LONG":
            pnl_r = (current_price - position.entry_price) / risk
        else:
            pnl_r = (position.entry_price - current_price) / risk
            
        # 1. Trend Reversal Exit
        if position.direction == "LONG" and fm < -0.1:
             return Action("EXIT", current_price, f"Trend Reversal (fm={fm:.2f})")
        if position.direction == "SHORT" and fm > 0.1:
             return Action("EXIT", current_price, f"Trend Reversal (fm={fm:.2f})")
             
        # 2. Time Stop
        holding_bars = (bar.name - position.entry_time).total_seconds() / 60 # Assuming 1m bars? No, checking logic
        # Actually bar.name is timestamp. 
        # If bars are 1m, holding_bars is minutes.
        # Strategy config says 'time_stop_bars: 16'. If 15m bars, that's 4 hours.
        # If 1m bars, we need to adjust. 
        # Let's assume the runner passes 1m bars, but the strategy might be thinking in 15m chunks?
        # The config says "16 bars (~4 hours)". So 1 bar = 15 min.
        # So 16 * 15 = 240 minutes.
        if holding_bars >= (self.time_stop_bars * 15): 
            # Check if profit < 0.5R (as per yaml)
            if pnl_r < 0.5:
                return Action("EXIT", current_price, "Time Stop (Stagnant)")
                
        # 3. Trailing Stop
        if pnl_r >= self.trail_start_r:
            # Move stop to +1.0R (or trail)
            if position.direction == "LONG":
                new_stop = position.entry_price + risk * 1.0
                if new_stop > position.stop_price:
                    position.stop_price = new_stop
            else:
                new_stop = position.entry_price - risk * 1.0
                if new_stop < position.stop_price:
                    position.stop_price = new_stop
                    
        # 4. Target/Stop Hit
        if position.direction == "LONG":
            if current_price >= position.target_price:
                return Action("EXIT", current_price, "Target Hit")
            if current_price <= position.stop_price:
                return Action("EXIT", current_price, "Stop Hit")
        else:
            if current_price <= position.target_price:
                return Action("EXIT", current_price, "Target Hit")
            if current_price >= position.stop_price:
                return Action("EXIT", current_price, "Stop Hit")
                
        return None

    def create_expectation(self, trade_id: str, signal: Signal) -> TradeExpectation:
        return TradeExpectation(
            trade_id=trade_id,
            expected_direction=signal.direction,
            expected_R_range=(1.0, 2.5),
            expected_holding_period=240,
            expected_regime="UNKNOWN",
            notes=signal.reason
        )
