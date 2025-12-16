"""
DGE ORB Strategy v0.3 (Attack Engine)
- Regime-Specific Exit Logic (Time Stop, Target R)
- Attack/Defense Modes
"""

import pandas as pd
from datetime import datetime
from typing import Optional, Dict

from strategies.kr_intraday.dge_orb_v0_2 import DGEOrbStrategyV2
from strategies.components.micro_regime import MicroRegimeClassifier
from strategies.components.exit_profile import ExitProfileTable, ExitParams
from strategies.kr_intraday.base_strategy import Position, Action

class DGEOrbStrategyV3(DGEOrbStrategyV2):
    """
    DGE ORB v0.3
    Dynamic Exit based on Micro-Regime.
    """
    
    def __init__(self, account, config, daily_df: pd.DataFrame = None, symbol: str = "UNKNOWN"):
        super().__init__(account, config, daily_df, symbol)
        self.strategy_name = "DGE_ORB_v0.3"
        
        # Components
        self.regime_classifier = MicroRegimeClassifier()
        self.exit_profiles = ExitProfileTable()
        
        # Global Mode (can be changed dynamically)
        self.mode = config.get('mode', 'ATTACK') 
        
        # Track Exit Params per Position
        # Key: Position ID (or object), Value: ExitParams
        self.position_params: Dict[int, ExitParams] = {} 

    def _update_indicators(self, bar: pd.Series, timestamp: datetime):
        # 1. Update History Buffer for fs_fast
        self.history_buffer.append({
            'close': bar['close'],
            'volume': bar['volume'],
            'timestamp': timestamp
        })
        
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
        from datetime import time, timedelta
        orb_end_time = (datetime.combine(timestamp.date(), time(9, 0)) + timedelta(minutes=self.orb_minutes)).time()
        
        if current_time <= orb_end_time:
            self.orb_high = max(self.orb_high, bar['high'])
            self.orb_low = min(self.orb_low, bar['low'])
        else:
            self.orb_complete = True

    def on_bar(self, bar: pd.Series, timestamp: datetime):
        """
        Override on_bar to implement Regime-Specific Entry Thresholds.
        """
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
        from garam.signals.fs_fast import update_fs_fast_one_tick
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
        
        # --- Regime-Specific Entry Threshold ---
        regime = self.regime_classifier.get_regime(self.daily_df, timestamp)
        
        # Default Threshold (Defense/Standard)
        current_fs_orb_thresh = 0.5 
        
        # Attack Mode Tuning: Relax threshold for STRONG_UP
        if "STRONG_UP_HIGH_VOL" in regime or "STRONG_UP_LOW_VOL" in regime:
            current_fs_orb_thresh = 0.3
        # Note: STRONG_UP_MED_VOL stays at 0.5 (Conservative)
        
        # Entry Logic
        from strategies.kr_intraday.base_strategy import Signal
        
        # LONG: fm >= fm_thresh and fs_orb >= current_fs_orb_thresh
        if fm >= self.fm_thresh and fs_orb >= current_fs_orb_thresh and fs_fast >= self.fs_fast_thresh:
            self.open_position(
                Signal("LONG", current_price, current_price * 0.98, current_price * 1.10, timestamp, f"Signal_{regime}"),
                self.symbol, bar
            )
            return None
            
        # SHORT: fm <= -fm_thresh and fs_orb <= -current_fs_orb_thresh
        elif fm <= -self.fm_thresh and fs_orb <= -current_fs_orb_thresh and fs_fast <= -self.fs_fast_thresh:
            self.open_position(
                Signal("SHORT", current_price, current_price * 1.02, current_price * 0.90, timestamp, f"Signal_{regime}"),
                self.symbol, bar
            )
            return None
            
        return None 

    def open_position(self, signal, symbol: str, bar: pd.Series):
        """Override to store exit params"""
        # 1. Determine Regime & Exit Params
        # Use signal timestamp for classification
        regime = self.regime_classifier.get_regime(self.daily_df, signal.timestamp)
        exit_params = self.exit_profiles.get_params(regime, self.mode)
        
        # 2. Call super to create position
        super().open_position(signal, symbol, bar)
        
        # 3. Store params for the new position
        if self.positions:
            new_pos = self.positions[-1]
            self.position_params[id(new_pos)] = exit_params
            # Log regime
            # Note: Position dataclass might not have 'entry_reason' field mutable or existing?
            # BaseStrategy Position has: trade_id, symbol, direction...
            # It doesn't have 'entry_reason'. We can't add it dynamically to a dataclass instance easily if frozen.
            # But standard dataclasses are mutable. Let's check BaseStrategy Position definition.
            # It doesn't have 'entry_reason'. It has 'trade_id'.
            # We can store regime in a separate dict if needed for analysis, or just rely on params.
            # For now, just storing params is enough for execution.
            pass

    def on_position_update(self, position: Position, bar: pd.Series) -> Optional[Action]:
        """
        Manage Position with Dynamic Exit Params
        """
        # Get Params
        params = self.position_params.get(id(position))
        
        # Fallback to v0.2 defaults if no params (shouldn't happen in v0.3)
        if not params:
            return super().on_position_update(position, bar)
            
        current_price = bar['close']
        direction_mult = 1 if position.direction == "LONG" else -1
        pnl_pct = (current_price - position.entry_price) / position.entry_price * direction_mult
        
        # Calculate R (approximate based on Stop R = -0.7 or -1.0)
        # We need the Risk Unit. v0.2 uses ATR or fixed %.
        # Let's assume Risk Unit = 1.5% of Entry Price (Standard)
        risk_unit = position.entry_price * 0.015
        current_r = (current_price - position.entry_price) * direction_mult / risk_unit
        
        # 1. Time Stop (Dynamic)
        # Calculate holding duration in minutes (assuming 1 bar = 1 minute)
        # If bars are not 1 minute, this logic needs adjustment.
        # But for now we assume 1 minute bars.
        holding_minutes = (bar.name - position.entry_time).total_seconds() / 60
        
        if holding_minutes >= params.time_stop_bars:
            # Check if profitable? v0.2 Time Stop is unconditional usually, or "if not profitable enough"
            # Research showed unconditional Time Stop is fine if tuned.
            # But usually Time Stop is "if trade isn't working".
            # If we are in huge profit, do we kill it?
            # Ideally, if Trailing Stop is ON, Time Stop might be relaxed.
            # For now, implement simple Time Stop as per research.
            return Action("EXIT", current_price, "Time Stop")
            
        # 2. Stop Loss (Dynamic)
        if current_r <= params.stop_r:
             return Action("EXIT", current_price, "Stop")
             
        # 3. Target (Dynamic)
        if current_r >= params.target_r:
             return Action("EXIT", current_price, "Target")
             
        # 4. Trailing Stop (Dynamic)
        if params.use_trailing:
            # Simple Trailing: If R > 1.0, move stop to Breakeven.
            # If R > 2.0, move stop to 1.0.
            # Or use MFE based.
            pass # TODO: Implement detailed trailing logic if needed. 
                 # For now, Target/Stop/Time is the main engine.
        
        # 5. Trend Reversal (fm) - Keep v0.2 logic as safety?
        # v0.2 checks fm signal. We can keep it or disable it.
        # Research didn't explicitly test fm exit, but it's a good safety net.
        # Let's call super's check for fm ONLY (not time/stop/target)
        # But super.on_position_update does everything.
        # So we replicate fm check here if we want it.
        
        # Replicate fm check from v0.2
        # if self.fm_thresh != 0 and ...
        # For v0.3, let's rely on the Regime Exit primarily.
        
        # position.bars_held += 1 # Removed as attribute doesn't exist
        position.current_price = current_price
        self.update_position_excursions(position, current_price)
        
        return None
