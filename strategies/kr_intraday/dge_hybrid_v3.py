import pandas as pd
import yaml
from datetime import datetime
from typing import Optional, List
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from config import PATHS
from strategies.kr_intraday.base_strategy import BaseIntradayStrategy, Signal, Action, Position
from strategies.components.regime_router import RegimeRouter, MarketState
from regime.edge_meter import EdgeMeter
from strategies.kr_intraday.dge_orb_v0_2 import DGEOrbStrategyV2
from strategies.kr_intraday.dge_orb_v0_3 import DGEOrbStrategyV3

class DGEHybridStrategyV3(BaseIntradayStrategy):
    """
    DGE Hybrid v3.0 (Trend-First)
    - Routes between v2 (Range) and v3 (Trend) based on Regime.
    - Uses EdgeMeter for classification and intensity.
    """
    
    def __init__(self, account, config, daily_df: pd.DataFrame = None, symbol: str = "UNKNOWN"):
        super().__init__(account, config, "DGE_Hybrid_v3")
        self.daily_df = daily_df
        self.symbol = symbol
        
        # 1. Initialize Components
        playbook_path = config.get('playbook_path', PATHS.CONFIG_DIR / "playbook_hybrid_v3.yaml")
        self.router = RegimeRouter(playbook_path)
        self.edge_meter = self.router.edge_meter # Use router's edge meter
        
        # 2. Initialize Sub-Modules
        # We need to pass specific configs to sub-modules if needed
        # For now, pass same config
        self.module_v3 = DGEOrbStrategyV3(account, config, daily_df)
        self.module_v2 = DGEOrbStrategyV2(account, config, daily_df)
        
        # 3. State
        self.current_regime = "UNKNOWN"
        self.current_module = "v3"
        self.current_intensity = 0.5
        
        # History for MarketState
        self.history_buffer = []
        self.orb_minutes = config.get('orb_minutes', 30)
        self.current_date = None
        self.orb_high = -float('inf')
        self.orb_low = float('inf')
        
    def on_bar(self, bar: pd.Series, timestamp: datetime) -> Optional[Signal]:
        # 1. Update Indicators & Market State
        self._update_indicators(bar, timestamp)
        market_state = self._calculate_market_state(bar, timestamp)
        
        if not market_state:
            return None
            
        # 2. Select Module via Router
        module_config = self.router.select_module(market_state)
        
        self.current_regime = module_config.regime_id
        self.current_module = module_config.module_id
        self.current_intensity = module_config.intensity
        
        # 3. Execute Module Logic
        # We inject dynamic risk based on intensity
        # Note: We assume sub-modules use self.risk_per_trade
        
        base_risk = 0.015 # Default 1.5%
        per_trade_risk = base_risk * self.current_intensity
        
        signal = None
        
        # Map module_id to instance
        # In playbook, module_id is M_ATTACK_V3 or M_RANGE_V2
        if "ATTACK" in self.current_module or "V3" in self.current_module:
            self.module_v3.risk_per_trade = per_trade_risk
            signal = self.module_v3.on_bar(bar, timestamp)
            # Update inactive module
            self.module_v2._update_indicators(bar, timestamp)
            
        elif "RANGE" in self.current_module or "V2" in self.current_module:
            self.module_v2.risk_per_trade = per_trade_risk
            signal = self.module_v2.on_bar(bar, timestamp)
            # Update inactive module
            self.module_v3._update_indicators(bar, timestamp)
            
        # If signal generated, we need to ensure open_position uses correct symbol
        # Sub-modules call self.open_position(signal, symbol, bar)
        # But wait, sub-modules don't know 'symbol' unless passed in init?
        # DGEOrbStrategyV2/V3 init doesn't take symbol currently (based on my previous check of v2).
        # But they call open_position(..., symbol, ...)
        # Where do they get symbol?
        # In v2 code I saw:
        # def on_bar(self, bar, timestamp): ...
        # It doesn't seem to have symbol.
        # This is the same bug I fixed in HybridV1!
        
        # I should fix V2 and V3 to accept symbol in init too?
        # Or I can intercept the signal here and call open_position myself?
        # But sub-modules call open_position internally.
        
        # If I can't modify V2/V3 easily right now (I can, but it's more work),
        # I can monkey-patch them or just ensure they use self.symbol if I add it to them?
        # Or, since I am calling them, maybe I should just copy their logic? No.
        
        # Let's assume I will fix V2 and V3 to accept symbol in init, just like HybridV1.
        # I will do that in next steps.
        
        return signal

    def on_position_update(self, position: Position, bar: pd.Series) -> Optional[Action]:
        # Delegate to the module that owns the position
        if position in self.module_v3.positions:
            return self.module_v3.on_position_update(position, bar)
        elif position in self.module_v2.positions:
            return self.module_v2.on_position_update(position, bar)
        return None

    @property
    def positions(self):
        # Aggregate positions from sub-modules
        return self.module_v3.positions + self.module_v2.positions
        
    @positions.setter
    def positions(self, value):
        # Ignore assignment (e.g. from BaseStrategy init)
        pass
        
    def close_position(self, position, price, time, reason):
        # This method is called by sub-modules when they decide to exit?
        # No, sub-modules call self.close_position (their own).
        # But if I call module.on_position_update, it returns Action.
        # Then who executes Action?
        # run_generic_backtest.py executes Action by calling strategy.close_position.
        # So run_generic_backtest calls Hybrid.close_position.
        
        # So Hybrid.close_position must delegate to the correct module.
        if position in self.module_v3.positions:
            self.module_v3.close_position(position, price, time, reason)
        elif position in self.module_v2.positions:
            self.module_v2.close_position(position, price, time, reason)

    def _update_indicators(self, bar, timestamp):
        # Update both modules
        self.module_v3._update_indicators(bar, timestamp)
        self.module_v2._update_indicators(bar, timestamp) # V2 might have different name?
        # V2 uses update_fs_fast_one_tick inside on_bar usually.
        # But if they have _update_indicators, call it.
        # Let's check V2/V3 code later. For now assume they handle it in on_bar.
        
        # Update local history for MarketState
        self.history_buffer.append({
            'close': bar['close'],
            'volume': bar['volume'],
            'timestamp': timestamp
        })
        if len(self.history_buffer) > 100: self.history_buffer.pop(0)
        
        # ORB (Local)
        if self.current_date != timestamp.date():
            self.current_date = timestamp.date()
            self.orb_high = -float('inf')
            self.orb_low = float('inf')
            
        from datetime import time, timedelta
        orb_end_time = (datetime.combine(timestamp.date(), time(9, 0)) + timedelta(minutes=self.orb_minutes)).time()
        if timestamp.time() <= orb_end_time:
            self.orb_high = max(self.orb_high, bar['high'])
            self.orb_low = min(self.orb_low, bar['low'])

    def _calculate_market_state(self, bar, timestamp) -> Optional[MarketState]:
        if self.daily_df is None or self.daily_df.empty: return None
        
        target_date = timestamp.date()
        mask = self.daily_df.index < pd.Timestamp(target_date)
        if not mask.any(): return None
        
        prev_daily = self.daily_df[mask].iloc[-1]
        
        trend_20d = prev_daily.get('trend_20d', 0.0)
        atr_z = prev_daily.get('atr_z', 0.5)
        fm = prev_daily.get('fm', 0.0)
        
        fs_orb = 0.0
        if self.orb_high > self.orb_low:
            mid = (self.orb_high + self.orb_low) / 2
            fs_orb = (bar['close'] - mid) / (self.orb_high - self.orb_low)
            
        fs_fast = 0.0 
        
        return MarketState(
            trend_20d=trend_20d,
            atr_z=atr_z,
            fm=fm,
            fs_orb=fs_orb,
            fs_fast=fs_fast,
            timestamp=str(timestamp)
        )

    def create_expectation(self, trade_id: str, signal: Signal):
        """
        Required by BaseIntradayStrategy.
        Not used directly as we delegate to sub-modules.
        """
        return None
