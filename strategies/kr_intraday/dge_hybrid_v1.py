import pandas as pd
from datetime import datetime
from typing import Optional, Dict

from strategies.kr_intraday.base_strategy import BaseIntradayStrategy, Signal, Action, Position
from strategies.components.regime_router import RegimeRouter, MarketState
from config import PATHS
from garam.signals.fs_fast import update_fs_fast_one_tick
from garam.signals.utils import FsFastParams
from sim.test_account import TradeExpectation

class DGEHybridStrategyV1(BaseIntradayStrategy):
    """
    DGE Hybrid Engine v1.0
    Routes between v2/v3 modules based on 7 Market Regimes.
    """
    
    def __init__(self, account, config, daily_df: pd.DataFrame = None, symbol: str = "UNKNOWN"):
        super().__init__(account, config, "DGE_Hybrid_v1")
        self.daily_df = daily_df
        self.symbol = symbol
        self.strategy_name = "DGE_Hybrid_v1"
        
        # Initialize Router
        playbook_path = PATHS.CONFIG_DIR / "playbook_v1.yaml"
        # Allow override from config
        if config.get('playbook_path'):
            playbook_path = config['playbook_path']
        self.router = RegimeRouter(playbook_path)
        
        # State
        self.current_regime = "UNKNOWN"
        self.current_module = "UNKNOWN"
        self.current_intensity = 0.0
        
        # History for fs_fast
        self.history_buffer = []
        # Initialize FsFastParams
        fs_config = config.get('fs_params', {})
        self.fs_params = FsFastParams(
            N_ret=fs_config.get('N_ret', 20),
            N_fs=fs_config.get('N_fs', 10)
        )
        
        # ORB State
        self.orb_high = -float('inf')
        self.orb_low = float('inf')
        self.orb_minutes = config.get('orb_minutes', 30)
        self.orb_complete = False
        self.current_date = None
        
        # Position Params Storage
        self.position_params: Dict[int, Dict] = {}

    def on_bar(self, bar: pd.Series, timestamp: datetime):
        # 1. Update History & Indicators
        self._update_indicators(bar, timestamp)
        
        # 2. Market State Calculation
        market_state = self._calculate_market_state(bar, timestamp)
        if not market_state: return None
        
        # 3. Router Selection
        module_config = self.router.select_module(market_state)
        self.current_regime = module_config.regime_id
        self.current_module = module_config.module_id
        self.current_intensity = module_config.intensity
        
        # 4. Check Entry (Based on Module Logic)
        self._check_entry(module_config, bar, timestamp, market_state)
        
    def _update_indicators(self, bar, timestamp):
        # History Buffer
        self.history_buffer.append({
            'close': bar['close'],
            'volume': bar['volume'],
            'timestamp': timestamp
        })
        if len(self.history_buffer) > 100: self.history_buffer.pop(0)
        
        # ORB
        if self.current_date != timestamp.date():
            self.current_date = timestamp.date()
            self.orb_high = -float('inf')
            self.orb_low = float('inf')
            self.orb_complete = False
            
        from datetime import time, timedelta
        orb_end_time = (datetime.combine(timestamp.date(), time(9, 0)) + timedelta(minutes=self.orb_minutes)).time()
        if timestamp.time() <= orb_end_time:
            self.orb_high = max(self.orb_high, bar['high'])
            self.orb_low = min(self.orb_low, bar['low'])
            
    def _calculate_market_state(self, bar, timestamp) -> Optional[MarketState]:
        # Need Daily Data for Trend/ATR
        if self.daily_df is None or self.daily_df.empty: return None
        
        # Get Daily Metrics (Pre-calculated or Calculate on fly)
        # Assuming daily_df has 'close', 'atr'
        # For prototype, we calculate simple trend
        
        # Trend 20d
        # We need previous day's data
        target_date = timestamp.date()
        mask = self.daily_df.index < pd.Timestamp(target_date)
        if not mask.any(): return None
        
        prev_daily = self.daily_df[mask].iloc[-1]
        
        # Calculate Trend 20d (if not in df)
        # Assuming daily_df has 'close'
        # We need 20 days history. 
        # For simplicity, let's assume 'trend_20d' column exists or calculate it simply
        # trend_20d = (close - close_20) / close_20
        # We'll use 'fm' as proxy if available, or calculate.
        
        trend_20d = prev_daily.get('trend_20d', 0.0)
        atr_z = prev_daily.get('atr_z', 0.5) # Default mid
        fm = prev_daily.get('fm', 0.0)
        
        # Intraday Indicators
        if len(self.history_buffer) < 50: return None
        df_hist = pd.DataFrame(self.history_buffer).set_index('timestamp')
        fs_fast = update_fs_fast_one_tick(df_hist, self.fs_params)
        
        # fs_orb
        orb_range = self.orb_high - self.orb_low
        fs_orb = 0.0
        if orb_range > 0:
            if bar['close'] > self.orb_high:
                fs_orb = (bar['close'] - self.orb_high) / orb_range
            elif bar['close'] < self.orb_low:
                fs_orb = (bar['close'] - self.orb_low) / orb_range
                
        return MarketState(
            trend_20d=trend_20d,
            atr_z=atr_z,
            fm=fm,
            fs_orb=fs_orb,
            fs_fast=fs_fast,
            timestamp=str(timestamp)
        )

    def _check_entry(self, config, bar, timestamp, state):
        params = config.params
        mode = params.get('mode', 'Off')
        
        if mode == 'Off': return
        
        # Entry Logic Mapping
        entry_signal = None
        
        # M_ATTACK_V3 (Trend Follow)
        if "ATTACK" in config.module_id:
            # fm is (Close - MA20)/MA20. 0.5 is 50%, which is too high.
            # Changed to 0.02 (2%) or just > 0.
            if state.fm >= 0.01 and state.fs_orb >= 0.3:
                entry_signal = "LONG"
            elif state.fm <= -0.01 and state.fs_orb <= -0.3:
                entry_signal = "SHORT" # If allowed
                
        # M_RANGE_V2 (Mean Reversion)
        elif "RANGE" in config.module_id:
            if abs(state.fm) < 0.2:
                if state.fs_fast <= -0.5: entry_signal = "LONG"
                # Short logic if needed
                
        # M_DOWN (Balanced/Attack)
        elif "DOWN" in config.module_id:
             if state.fm <= -0.2 and state.fs_orb <= -0.2:
                 entry_signal = "SHORT"
        
        if entry_signal:
            # Check Max Positions
            if len(self.positions) >= params.get('max_positions', 3): return
            
            # Create Signal
            current_price = bar['close']
            stop_price = current_price * (1 - params['stop_R'] * 0.01) if entry_signal == "LONG" else current_price * (1 + params['stop_R'] * 0.01)
            target_price = current_price * (1 + params['target_R'] * 0.01) if entry_signal == "LONG" else current_price * (1 - params['target_R'] * 0.01)
            
            sig = Signal(entry_signal, current_price, stop_price, target_price, timestamp, f"{config.module_id}_{config.regime_id}")
            self.open_position(sig, self.symbol, bar, params)

    def open_position(self, signal, symbol, bar, params):
        super().open_position(signal, symbol, bar)
        if self.positions:
            # Store params for the new position
            self.position_params[id(self.positions[-1])] = params

    def on_position_update(self, position: Position, bar: pd.Series) -> Optional[Action]:
        params = self.position_params.get(id(position))
        if not params: return super().on_position_update(position, bar)
        
        current_price = bar['close']
        
        # 1. Time Stop
        holding_mins = (bar.name - position.entry_time).total_seconds() / 60
        if holding_mins >= params['time_stop_min']:
            return Action("EXIT", current_price, "Time Stop")
            
        # 2. Target / Stop (R based)
        # Calculate R
        risk_unit = position.entry_price * 0.01 # Assume 1% risk unit for R calc
        pnl_r = (current_price - position.entry_price) / risk_unit if position.direction == "LONG" else (position.entry_price - current_price) / risk_unit
        
        if pnl_r >= params['target_R']: return Action("EXIT", current_price, "Target")
        if pnl_r <= -params['stop_R']: return Action("EXIT", current_price, "Stop")
        
        return None

    def create_expectation(self, trade_id: str, signal: Signal) -> TradeExpectation:
        """
        Create trade expectation for anomaly tracking.
        """
        # Calculate expected R based on target/stop
        risk_per_share = abs(signal.entry_price - signal.stop_price)
        if risk_per_share == 0:
            expected_r = 0
        else:
            expected_r = abs(signal.target_price - signal.entry_price) / risk_per_share
            
        # Holding period expectation (default from config or signal)
        # We can extract it from signal.reason if we stored it there, or just use a default
        expected_holding_bars = 60 # Default
        
        return TradeExpectation(
            trade_id=trade_id,
            expected_direction=signal.direction,
            expected_R_range=(1.0, expected_r * 1.5), # Min 1.0, Max Buffer
            expected_holding_period=expected_holding_bars,
            expected_regime=self.current_regime,
            notes=f"Module: {self.current_module}"
        )
