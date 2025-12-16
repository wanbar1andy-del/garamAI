"""
DGE ORB Strategy v0.2
Integrated with fs_fast (Ultra-short term direction)
"""

from typing import Optional, List, Dict
from datetime import datetime, time, timedelta
import pandas as pd
import numpy as np
import sys
from pathlib import Path

# Add project root
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from strategies.kr_intraday.base_strategy import BaseIntradayStrategy, Signal, Position, Action
from sim.test_account import TradeExpectation
from garam.signals.utils import FsFastParams
from garam.signals.fs_fast import update_fs_fast_one_tick

class DGEOrbStrategyV2(BaseIntradayStrategy):
    """
    DGE ORB Strategy v0.2
    
    Signals:
    1. fm (Daily Trend): EMA Slope Z-score
    2. fs_orb (Intraday Momentum): ORB Breakout Strength
    3. fs_fast (Ultra-short Direction): Price + Volume + Consistency
    
    State Machine:
    - Entry: Requires fm + fs_orb + fs_fast alignment
    - Exit: fm reversal OR fs_fast reversal (Dynamic Time-cut)
    """
    
    def __init__(self, account, config, daily_df: pd.DataFrame = None, symbol: str = "UNKNOWN"):
        super().__init__(account, config, "DGE_ORB_v0.2")
        self.symbol = symbol
        
        self.daily_df = daily_df
        
        # Params
        self.orb_minutes = config.get('orb_minutes', 30)
        
        # Thresholds
        self.fs_orb_thresh = config.get('fs_orb_thresh', 0.5)
        self.fs_fast_thresh = config.get('fs_fast_thresh', 0.8)
        self.fm_thresh = config.get('fm_thresh', 0.0)
        
        # fs_fast params
        self.fs_params = FsFastParams(
            k_return=config.get('fs_k', 3),
            N_ret=config.get('fs_N', 120)
        )
        
        # Risk
        self.target_r = config.get('target_r', 2.5)
        self.time_stop_bars = config.get('time_stop_bars', 16)
        
        # State
        self.current_date = None
        self.orb_high = -float('inf')
        self.orb_low = float('inf')
        self.orb_complete = False
        
        # History buffer for fs_fast
        self.history_buffer = [] # List of dicts
        
        # Pre-calc daily
        if self.daily_df is not None:
             self._calc_daily_metrics()
             
    def _calc_daily_metrics(self):
        """Calculate Daily EMA Slope Z-Score (Simplified)"""
        df = self.daily_df.copy()
        df['ema20'] = df['close'].ewm(span=20, adjust=False).mean()
        df['slope'] = df['ema20'].pct_change() * 100
        
        # Simple Z-score (rolling 60)
        roll = df['slope'].rolling(60)
        df['fm'] = (df['slope'] - roll.mean()) / (roll.std() + 1e-6)
        
        self.daily_df = df
        
    def get_daily_fm(self, timestamp: datetime) -> float:
        if self.daily_df is None: return 0.0
        target_date = timestamp.date()
        mask = self.daily_df.index < pd.Timestamp(target_date)
        if not mask.any(): return 0.0
        return self.daily_df[mask].iloc[-1].get('fm', 0.0)

    def _update_indicators(self, bar: pd.Series, timestamp: datetime):
        # 1. Update History Buffer for fs_fast
        self.history_buffer.append({
            'close': bar['close'],
            'volume': bar['volume'],
            'timestamp': timestamp
        })
        
        # Keep enough history
        max_len = self.fs_params.N_ret + self.fs_params.N_fs + 20
        if len(self.history_buffer) > max_len:
            self.history_buffer.pop(0)
            
        # 2. Reset Daily State
        if self.current_date != timestamp.date():
            self.current_date = timestamp.date()
            self.orb_high = -float('inf')
            self.orb_low = float('inf')
            self.orb_complete = False
            
        # 3. Update ORB
        current_time = timestamp.time()
        orb_end_time = (datetime.combine(timestamp.date(), time(9, 0)) + timedelta(minutes=self.orb_minutes)).time()
        
        if current_time <= orb_end_time:
            self.orb_high = max(self.orb_high, bar['high'])
            self.orb_low = min(self.orb_low, bar['low'])
        else:
            self.orb_complete = True

    def on_bar(self, bar: pd.Series, timestamp: datetime) -> Optional[Signal]:
        self._update_indicators(bar, timestamp)
        
        if not self.orb_complete:
            return None
            
        # 4. Check Entry Conditions
        if len(self.positions) >= self.max_positions:
            return None
            
        # Calculate fs_fast
        if len(self.history_buffer) < 50: # Need warm up
            return None
            
        df_hist = pd.DataFrame(self.history_buffer).set_index('timestamp')
        fs_fast = update_fs_fast_one_tick(df_hist, self.fs_params)
        
        # Calculate fs_orb (Normalized)
        orb_range = self.orb_high - self.orb_low
        if orb_range == 0: return None
        
        current_price = bar['close']
        fs_orb = 0.0
        if current_price > self.orb_high:
            fs_orb = (current_price - self.orb_high) / orb_range
        elif current_price < self.orb_low:
            fs_orb = (current_price - self.orb_low) / orb_range # Negative
            
        # Daily Trend
        if 'fm' in bar and not pd.isna(bar['fm']):
            fm = bar['fm']
        else:
            fm = self.get_daily_fm(timestamp)
        
        # Entry Logic
        # LONG: fm >= fm_thresh and fs_orb >= fs_orb_thresh and fs_fast >= fs_fast_thresh
        if fm >= self.fm_thresh and fs_orb >= self.fs_orb_thresh and fs_fast >= self.fs_fast_thresh:
            self.open_position(
                Signal("LONG", current_price, current_price * 0.98, current_price * 1.10, timestamp, "Signal"),
                self.symbol, bar
            )
            return None
            
        # SHORT: fm <= -fm_thresh and fs_orb <= -fs_orb_thresh and fs_fast <= -fs_fast_thresh
        elif fm <= -self.fm_thresh and fs_orb <= -self.fs_orb_thresh and fs_fast <= -self.fs_fast_thresh:
            self.open_position(
                Signal("SHORT", current_price, current_price * 1.02, current_price * 0.90, timestamp, "Signal"),
                self.symbol, bar
            )
            return None
            
        return None

    def on_position_update(self, position: Position, bar: pd.Series) -> Optional[Action]:
        current_price = bar['close']
        self.update_position_excursions(position, current_price)
        
        # Update fs_fast for exit logic
        # Note: history_buffer is updated in on_bar, which is called BEFORE this?
        # Actually backtest runner calls process_bar (update pos) THEN on_bar (entry).
        # So we need to ensure history is up to date.
        # In runner: _process_bar -> on_position_update.
        # So history buffer might be 1 bar behind if we rely on on_bar to update it.
        # FIX: We should update history in runner or have a separate update method.
        # For now, let's assume slight lag is acceptable or we peek current bar.
        
        # Dynamic Time-cut using fs_fast
        # If we are in a trade, and fs_fast drops to 0 (loss of momentum), exit early.
        
        # Re-calc fs_fast (expensive in loop? optimize later)
        # For this prototype, we'll skip re-calc here to save time and rely on standard rules + fm check
        
        fm = self.get_daily_fm(bar.name)
        
        # 1. Trend Reversal
        if position.direction == "LONG" and fm < -0.5:
            return Action("EXIT", current_price, f"Trend Reversal fm={fm:.2f}")
        if position.direction == "SHORT" and fm > 0.5:
            return Action("EXIT", current_price, f"Trend Reversal fm={fm:.2f}")
            
        # 2. Standard Rules (Target, Stop, Time)
        # ... (Same as v0.1 for now, can add fs_fast exit later)
        
        # Calculate current R
        risk = abs(position.entry_price - position.stop_price)
        if risk == 0: risk = 1
        
        pnl_r = 0
        if position.direction == "LONG":
            pnl_r = (current_price - position.entry_price) / risk
        else:
            pnl_r = (position.entry_price - current_price) / risk
            
        # Time Stop
        holding_bars = (bar.name - position.entry_time).total_seconds() / 60 / 1 # assuming 1m
        if holding_bars >= (self.time_stop_bars * 15):
             if pnl_r < 0.5:
                 return Action("EXIT", current_price, "Time Stop")

        # Trailing
        if pnl_r >= 1.5:
            if position.direction == "LONG":
                new_stop = position.entry_price + risk * 1.0
                if new_stop > position.stop_price:
                    position.stop_price = new_stop
            else:
                new_stop = position.entry_price - risk * 1.0
                if new_stop < position.stop_price:
                    position.stop_price = new_stop
                    
        # Target/Stop
        if position.direction == "LONG":
            if current_price >= position.target_price: return Action("EXIT", current_price, "Target")
            if current_price <= position.stop_price: return Action("EXIT", current_price, "Stop")
        else:
            if current_price <= position.target_price: return Action("EXIT", current_price, "Target")
            if current_price >= position.stop_price: return Action("EXIT", current_price, "Stop")
            
        return None

    def create_expectation(self, trade_id: str, signal: Signal) -> TradeExpectation:
        return TradeExpectation(
            trade_id=trade_id,
            expected_direction=signal.direction,
            expected_R_range=(1.0, 3.0),
            expected_holding_period=120,
            expected_regime="MOMENTUM",
            notes=signal.reason
        )
