"""
DGE Sharpened V3.2 (Pure V3 + Mode Switching + Cooldown)
- Core: DGE ORB V3 (Trend Following)
- Modes: PURE (Attack), SHARP (Defense), PROBE (Survival)
- Micro-Safety: Fast Cut (Stagnation) with Cooldown (Churning Prevention)
- Macro-Safety: EdgeMeter (Daily R & Streak based Mode Switching)
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple
from enum import Enum
from collections import defaultdict

from strategies.kr_intraday.dge_orb_v0_3 import DGEOrbStrategyV3
from strategies.kr_intraday.base_strategy import Position, Action, Signal
from regime.edge_meter import EdgeMeter

class SharpenedMode(Enum):
    PURE = "PURE"    # High Edge: Max Risk, Min Cut
    SHARP = "SHARP"  # Normal: Reduced Risk, Active Cut
    PROBE = "PROBE"  # Low Edge: Min Risk, Active Cut, Limited Entry

class DGEV3Sharpened(DGEOrbStrategyV3):
    """
    DGE Sharpened V3.2
    Extends V3 with Mode Switching and Cooldown.
    """
    
    def __init__(self, account, config, daily_df: pd.DataFrame = None, symbol: str = "UNKNOWN"):
        super().__init__(account, config, daily_df, symbol)
        self.strategy_name = "DGE_V3_Sharpened"
        
        # State for Macro-Safety
        self.daily_r = 0.0
        self.daily_trades = 0
        self.consecutive_losses = 0
        self.current_mode = SharpenedMode.SHARP # Default start
        
        # Cooldown Manager
        # Key: (symbol, direction), Value: datetime until cooldown ends
        self.cooldown_map: Dict[Tuple[str, str], datetime] = {}
        self.cooldown_minutes = 30
        
        # Parameters
        self.base_risk_pct = 0.015 # 1.5%
        
        # Mode Config
        self.mode_config = {
            SharpenedMode.PURE: {
                "risk_mult": 1.0,
                "fast_cut_enabled": False, # Or very loose
            },
            SharpenedMode.SHARP: {
                "risk_mult": 0.7,
                "fast_cut_enabled": True,
            },
            SharpenedMode.PROBE: {
                "risk_mult": 0.3,
                "fast_cut_enabled": True,
            }
        }
        
        # Fast Cut Params
        self.fast_cut_r_min = -0.3
        self.fast_cut_r_max = 0.1

    def on_bar(self, bar: pd.Series, timestamp: datetime):
        """
        Override on_bar to inject Mode Switching and Cooldown Check.
        """
        # 1. Update Indicators (Standard V3)
        self._update_indicators(bar, timestamp)
        
        if not self.orb_complete:
            return None
            
        # 2. Decide Mode (Macro-Safety)
        self.decide_mode()
        
        # 3. Set Risk based on Mode
        cfg = self.mode_config[self.current_mode]
        self.risk_per_trade = self.base_risk_pct * cfg["risk_mult"]
        
        # 4. Check Cooldown before calling parent (which checks entry)
        # Parent on_bar calls open_position if signal.
        # We can't easily intercept the signal inside parent's on_bar without copying code.
        # BUT, we can override open_position to block it if cooldown is active!
        # Wait, open_position is called AFTER signal generation.
        # If we block in open_position, we lose the signal but that's fine.
        # Better: Copy-paste Entry Logic from V3?
        # Or just let parent generate signal and block in open_position.
        # Blocking in open_position is cleaner.
        
        # However, parent logic:
        # if signal: open_position()
        # if we block in open_position, we just return.
        
        return super().on_bar(bar, timestamp)

    def open_position(self, signal: Signal, symbol: str, bar: pd.Series):
        """
        Override to enforce Cooldown and Mode restrictions.
        """
        # 1. Check Cooldown
        if not self.can_enter(symbol, signal.direction, signal.timestamp):
            # Blocked by Cooldown
            return
            
        # 2. Check Mode Restrictions (PROBE mode might limit new entries?)
        # For now, PROBE just reduces risk (handled in on_bar).
        
        # 3. Proceed
        super().open_position(signal, symbol, bar)

    def decide_mode(self):
        """
        Update current_mode based on Daily R and Streak.
        """
        # 1. PURE (Great Day): +2R or more & Streak <= 2
        if self.daily_r >= 2.0 and self.consecutive_losses <= 2:
            self.current_mode = SharpenedMode.PURE
            return
            
        # 2. PROBE (Bad Day): -2R or worse OR Streak >= 4
        if self.daily_r <= -2.0 or self.consecutive_losses >= 4:
            self.current_mode = SharpenedMode.PROBE
            return
            
        # 3. SHARP (Normal): Default
        self.current_mode = SharpenedMode.SHARP

    def on_position_update(self, position: Position, bar: pd.Series) -> Optional[Action]:
        """
        Override to inject Micro-Safety (Fast Cut).
        """
        # 1. Check Fast Cut
        if self.check_fast_cut(position, bar):
            # Register Cooldown
            self.register_cooldown(position.symbol, position.direction, bar.name)
            return Action("EXIT", bar['close'], "FastCut")
            
        # 2. Standard V3 Exit Logic
        return super().on_position_update(position, bar)

    def check_fast_cut(self, position: Position, bar: pd.Series) -> bool:
        """
        Micro-Safety: Check for failure signatures.
        Dependent on Current Mode.
        """
        cfg = self.mode_config[self.current_mode]
        if not cfg["fast_cut_enabled"]:
            return False
            
        # Calculate Unrealized R
        current_price = bar['close']
        direction_mult = 1 if position.direction == "LONG" else -1
        risk_unit = position.entry_price * 0.015 # Approx
        unrealized_r = (current_price - position.entry_price) * direction_mult / risk_unit
        
        # Calculate Bars Held
        bars_held = (bar.name - position.entry_time).total_seconds() / 60
        
        # 1. Stagnation Cut (Relative to Time Stop)
        params = self.position_params.get(id(position))
        if params:
            time_stop_bars = params.time_stop_bars
            # Check if 30% of time stop has passed
            if bars_held >= (time_stop_bars * 0.3):
                # If stuck between -0.3R and +0.1R
                if self.fast_cut_r_min <= unrealized_r <= self.fast_cut_r_max:
                    return True
        else:
             if bars_held >= 10:
                 if self.fast_cut_r_min <= unrealized_r <= self.fast_cut_r_max:
                    return True
                
        # 2. Momentum Flip Cut (Optional - kept simple for now)
        
        return False

    def register_cooldown(self, symbol: str, direction: str, now: datetime):
        """Activate cooldown for this symbol/direction."""
        self.cooldown_map[(symbol, direction)] = now + timedelta(minutes=self.cooldown_minutes)

    def can_enter(self, symbol: str, direction: str, now: datetime) -> bool:
        """Check if entry is allowed."""
        cooldown_end = self.cooldown_map.get((symbol, direction))
        if cooldown_end and now < cooldown_end:
            return False
        return True

    def on_trade_closed(self, trade_pnl: float, timestamp: datetime, expectation=None, outcome=None, entry_time=None, symbol="UNKNOWN"):
        """
        Track Daily R and Consecutive Losses.
        """
        # Reset daily stats if new day
        if self.current_date != timestamp.date():
             self.daily_r = 0.0
             self.daily_trades = 0
             self.consecutive_losses = 0
             self.current_date = timestamp.date()
             self.cooldown_map.clear() # Clear cooldowns on new day
             
        # Calculate Realized R (Approx if not provided)
        realized_r = 0.0
        if outcome:
            realized_r = outcome.realized_R
        else:
            # Fallback approx
            # Assuming 1.5% risk unit per trade approx
            # We don't have entry price here easily without outcome/expectation
            # But trade_pnl is absolute.
            # Let's use trade_pnl / (start_equity * 0.015) as approx R
            risk_amt = self.start_equity * 0.015
            if risk_amt > 0:
                realized_r = trade_pnl / risk_amt
        
        self.daily_r += realized_r
        self.daily_trades += 1
        
        if trade_pnl < 0:
            self.consecutive_losses += 1
        else:
            self.consecutive_losses = 0
            
        super().on_trade_closed(trade_pnl, timestamp, expectation, outcome, entry_time, symbol)
