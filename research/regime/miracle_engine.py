"""
Miracle Engine
Core framework for Policy Vector Optimization.
Defines Entry/Exit/Filter/Risk Templates and the MiracleBacktester.
"""

import pandas as pd
import numpy as np
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from garam.risk.dge import DailyGrowthEngine, RiskConfig

# ==========================================
# Data Models
# ==========================================

@dataclass
class Trade:
    entry_time: pd.Timestamp
    entry_price: float
    side: int # 1 (Long), -1 (Short)
    
    # Exit fields (initially None/Zero)
    exit_time: Optional[pd.Timestamp] = None
    exit_price: float = 0.0
    pnl: float = 0.0
    pnl_pct: float = 0.0
    duration: int = 0
    exit_reason: str = ""
    regime: str = ""
    
    # Metadata for Analysis
    theta_id: str = ""
    entry_mode: str = ""
    exit_mode: str = ""
    risk_mode: str = ""
    filter_mode: str = ""
    
    # Risk Metrics
    risk_pct: float = 0.0 # Initial risk % of capital
    position_size: float = 0.0

# ==========================================
# Templates (Abstract Base Classes)
# ==========================================

class Template(ABC):
    def __init__(self, params: Dict[str, Any]):
        self.params = params
    
    @property
    def name(self):
        return self.__class__.__name__

class EntryTemplate(Template):
    @abstractmethod
    def check_entry(self, row: pd.Series, prev_row: pd.Series, context: Dict[str, Any]) -> int:
        """Returns signal: 1 (Long), -1 (Short), 0 (None)"""
        pass

class ExitTemplate(Template):
    @abstractmethod
    def check_exit(self, row: pd.Series, trade: Trade, context: Dict[str, Any]) -> Tuple[bool, str]:
        """Returns (should_exit, reason)"""
        pass

class FilterTemplate(Template):
    @abstractmethod
    def check_filter(self, row: pd.Series, context: Dict[str, Any]) -> bool:
        """Returns True if entry is allowed, False otherwise"""
        pass

class RiskTemplate(Template):
    @abstractmethod
    def calculate_size(self, capital: float, row: pd.Series, stop_loss_price: Optional[float]) -> float:
        """Returns position size (in currency units or shares)"""
        pass
        
    @abstractmethod
    def check_risk_limits(self, context: Dict[str, Any]) -> bool:
        """Returns True if trade is allowed by global risk limits (e.g. max daily loss)"""
        pass

# ==========================================
# Concrete Templates
# ==========================================

# --- Entry Templates ---

class ImmediateBreakoutEntry(EntryTemplate):
    def check_entry(self, row: pd.Series, prev_row: pd.Series, context: Dict[str, Any]) -> int:
        strategy_type = self.params.get('strategy_type', 'TrendFollowing')
        
        if strategy_type == 'TrendFollowing':
            fast = row.get(f"ma_{self.params['window_fast']}")
            slow = row.get(f"ma_{self.params['window_slow']}")
            prev_fast = prev_row.get(f"ma_{self.params['window_fast']}")
            prev_slow = prev_row.get(f"ma_{self.params['window_slow']}")
            
            if pd.isna(fast) or pd.isna(slow) or pd.isna(prev_fast): return 0
            
            if prev_fast <= prev_slow and fast > slow: return 1
            if prev_fast >= prev_slow and fast < slow: return -1
            
        elif strategy_type == 'MeanReversion':
            w = self.params['window']
            std = self.params['std_dev']
            lower = row.get(f'lower_{w}_{std}')
            upper = row.get(f'upper_{w}_{std}')
            
            if pd.isna(lower) or pd.isna(upper): return 0
            if row['close'] < lower: return 1
            if row['close'] > upper: return -1
            
        return 0

class ConfirmEntry(EntryTemplate):
    def __init__(self, params):
        super().__init__(params)
        
    def check_entry(self, row: pd.Series, prev_row: pd.Series, context: Dict[str, Any]) -> int:
        delay = self.params.get('delay_days', 1)
        base_signal = ImmediateBreakoutEntry(self.params).check_entry(row, prev_row, context)
        
        if 'pending_entry' not in context:
            context['pending_entry'] = {'signal': 0, 'days': 0}
            
        state = context['pending_entry']
        
        if base_signal != 0:
            state['signal'] = base_signal
            state['days'] = 0
            return 0 
            
        if state['signal'] != 0:
            state['days'] += 1
            if state['days'] >= delay:
                sig = state['signal']
                state['signal'] = 0
                state['days'] = 0
                return sig
                
        return 0

class PullbackEntry(EntryTemplate):
    """
    Wait for price to retrace X% or touch MA after signal.
    """
    def check_entry(self, row: pd.Series, prev_row: pd.Series, context: Dict[str, Any]) -> int:
        # Simplified: if we have a pending signal, check if Low < MA (for Long)
        # This requires more complex state. Placeholder for now.
        return ImmediateBreakoutEntry(self.params).check_entry(row, prev_row, context)

# --- Exit Templates ---

class SignalReversalExit(ExitTemplate):
    def check_exit(self, row: pd.Series, trade: Trade, context: Dict[str, Any]) -> Tuple[bool, str]:
        current_signal = context.get('current_signal', 0)
        if trade.side == 1 and current_signal == -1: return True, "Signal Reversal"
        if trade.side == -1 and current_signal == 1: return True, "Signal Reversal"
        return False, ""

class FixedTargetExit(ExitTemplate):
    def check_exit(self, row: pd.Series, trade: Trade, context: Dict[str, Any]) -> Tuple[bool, str]:
        price = row['close']
        entry = trade.entry_price
        pnl_pct = (price - entry) / entry if trade.side == 1 else (entry - price) / entry
            
        sl = self.params.get('sl_pct', 0.05)
        tp = self.params.get('tp_pct', 0.10)
        
        if pnl_pct <= -sl: return True, "Stop Loss"
        if pnl_pct >= tp: return True, "Take Profit"
        return False, ""

class TimeStopExit(ExitTemplate):
    def check_exit(self, row: pd.Series, trade: Trade, context: Dict[str, Any]) -> Tuple[bool, str]:
        days_held = (row.name - trade.entry_time).days
        max_days = self.params.get('max_days', 20)
        if days_held >= max_days: return True, "Time Stop"
        return False, ""

class TrailingStopExit(ExitTemplate):
    def check_exit(self, row: pd.Series, trade: Trade, context: Dict[str, Any]) -> Tuple[bool, str]:
        # Simple trailing stop
        # Need to track high_water_mark in trade or context?
        # Trade object doesn't have it. We can use context['active_trade_hwm']
        
        trail_pct = self.params.get('trail_pct', 0.05)
        price = row['close']
        
        if 'hwm' not in context:
            context['hwm'] = trade.entry_price
            
        if trade.side == 1:
            context['hwm'] = max(context['hwm'], price)
            drawdown = (price - context['hwm']) / context['hwm']
            if drawdown <= -trail_pct: return True, "Trailing Stop"
        else:
            context['hwm'] = min(context['hwm'], price)
            drawdown = (context['hwm'] - price) / context['hwm']
            if drawdown <= -trail_pct: return True, "Trailing Stop"
            
        return False, ""

# --- Filter Templates ---

class VolatilityFilter(FilterTemplate):
    def check_filter(self, row: pd.Series, context: Dict[str, Any]) -> bool:
        # Assume ATR is pre-calculated as 'atr' or 'atr_14'
        # Or calculate roughly: (High-Low)/Close
        vol = (row['high'] - row['low']) / row['close']
        min_vol = self.params.get('min_vol', 0.0)
        max_vol = self.params.get('max_vol', 1.0)
        return min_vol <= vol <= max_vol

class RegimeFilter(FilterTemplate):
    def check_filter(self, row: pd.Series, context: Dict[str, Any]) -> bool:
        allowed = self.params.get('allowed_regimes', [])
        if not allowed: return True
        return row.get('state', 'UNKNOWN') in allowed

# --- Risk Templates ---

class StandardRisk(RiskTemplate):
    def calculate_size(self, capital: float, row: pd.Series, stop_loss_price: Optional[float]) -> float:
        risk_per_trade = self.params.get('risk_per_trade', 0.01) # 1%
        
        if stop_loss_price:
            risk_amt = capital * risk_per_trade
            dist = abs(row['close'] - stop_loss_price)
            if dist == 0: return capital # Fallback
            return risk_amt / dist * row['close'] # Notional value
        else:
            # If no SL, use fixed fractional
            # e.g. 10% of capital
            return capital * 0.1 

    def check_risk_limits(self, context: Dict[str, Any]) -> bool:
        # Check daily loss, consecutive losses
        max_daily = self.params.get('max_daily_loss', 0.03)
        daily_pnl = context.get('daily_pnl', 0.0)
        
        if daily_pnl <= -max_daily:
            return False
            
        max_cons = self.params.get('max_consecutive_losses', 5)
        cons_loss = context.get('consecutive_losses', 0)
        
        if cons_loss >= max_cons:
            return False
            
        return True

class DGERisk(RiskTemplate):
    def __init__(self, params: Dict[str, Any]):
        super().__init__(params)
        self.config = RiskConfig(
            max_daily_loss_pct=params.get('max_daily_loss', 0.03),
            max_risk_per_trade_pct=params.get('risk_per_trade', 0.01),
            kelly_fraction=params.get('kelly_fraction', 0.25),
            use_kelly=params.get('use_kelly', True)
        )
        self.engine = DailyGrowthEngine(self.config)

    def calculate_size(self, capital: float, row: pd.Series, stop_loss_price: Optional[float]) -> float:
        stats = {
            'win_rate': self.params.get('win_rate', 0.5),
            'payoff_ratio': self.params.get('payoff_ratio', 2.0)
        }
        # Pass regime if available, else default to GREEN
        regime = row.get('state', 'GREEN')
        return self.engine.calculate_position_size(capital, row['close'], stop_loss_price, stats, regime=regime)

    def check_risk_limits(self, context: Dict[str, Any]) -> bool:
        return self.engine.risk_manager.check_can_trade()
    
    def update_daily_pnl(self, pnl: float, capital: float):
        self.engine.update_daily_status(pnl, capital)
        
    def reset_daily(self):
        self.engine.reset_daily()

# ==========================================
# Policy Vector
# ==========================================

class Policy:
    def __init__(self, 
                 entry_logic: EntryTemplate, 
                 exit_logics: List[ExitTemplate],
                 filters: List[FilterTemplate] = None,
                 risk_logic: RiskTemplate = None,
                 theta_id: str = "default",
                 horizons: Dict[str, Any] = None,
                 coordination_rules: List[Dict[str, Any]] = None):
        self.entry_logic = entry_logic
        self.exit_logics = exit_logics
        self.filters = filters or []
        self.risk_logic = risk_logic or StandardRisk({'risk_per_trade': 0.01})
        self.theta_id = theta_id
        self.horizons = horizons or {}
        self.coordination_rules = coordination_rules or []
        self.coordination_engine = CoordinationEngine(self.coordination_rules) if self.coordination_rules else None

class CoordinationEngine:
    def __init__(self, rules: List[Dict[str, Any]]):
        self.rules = rules
        
    def evaluate(self, state: str, fs: float, fm: float) -> Tuple[str, Dict[str, Any]]:
        """
        Evaluates rules against current state and signals.
        Returns (action, params).
        """
        # Find rules for current state
        state_rules = next((r['rules'] for r in self.rules if r['state'] == state), [])
        
        # Filter matching rules
        matches = []
        for rule in state_rules:
            condition = rule['condition']
            # Safe evaluation context
            eval_context = {'fs': fs, 'fm': fm}
            try:
                if eval(condition, {"__builtins__": None}, eval_context):
                    matches.append(rule)
            except Exception as e:
                print(f"Rule evaluation error: {e}")
                continue
        
        if not matches:
            return "WAIT", {}
            
        # Sort by priority (descending) and pick top
        # Default priority is 0 if not specified
        best_rule = sorted(matches, key=lambda x: x.get('priority', 0), reverse=True)[0]
        
        return best_rule['action'], best_rule.get('params', {})

# ==========================================
# Miracle Backtester
# ==========================================

class MiracleBacktester:
    def __init__(self, data: pd.DataFrame):
        self.data = data.sort_index()
        self.signal_logs = []
        
    def run(self, policy: Policy, initial_capital: float = 10000.0) -> List[Trade]:
        trades = []
        active_trade: Optional[Trade] = None
        context = {
            'daily_pnl': 0.0,
            'consecutive_losses': 0,
            'current_date': None
        }
        
        capital = initial_capital
        
        for i in range(1, len(self.data)):
            row = self.data.iloc[i]
            prev_row = self.data.iloc[i-1]
            timestamp = row.name
            
            # Daily Reset
            if context['current_date'] != timestamp.date():
                context['current_date'] = timestamp.date()
                context['daily_pnl'] = 0.0
                context['consecutive_losses'] = 0
            
            # 1. Update Active Trade
            if active_trade:
                # Update HWM for trailing
                if 'hwm' not in context: context['hwm'] = active_trade.entry_price
                if active_trade.side == 1: context['hwm'] = max(context['hwm'], row['close'])
                else: context['hwm'] = min(context['hwm'], row['close'])

                # Check Exits
                should_exit = False
                reason = ""
                
                # Multi-Horizon Logic for Exit/Hold
                if policy.coordination_engine:
                    fs = self._calculate_horizon_signal(row, policy.horizons.get('short'))
                    fm = self._calculate_horizon_signal(row, policy.horizons.get('mid'))
                    
                    current_state = "LONG" if active_trade.side == 1 else "SHORT"
                    action, params = policy.coordination_engine.evaluate(current_state, fs, fm)
                    
                    if action == "EXIT_ALL":
                        should_exit = True
                        reason = params.get('reason', 'CoordinationExit')
                    elif action == "REDUCE":
                        pass  # Not implemented
                
                # Standard Exit Logic (Fallback or Complementary)
                if not should_exit:
                    for exit_logic in policy.exit_logics:
                        ex, r = exit_logic.check_exit(row, active_trade, context)
                        if ex:
                            should_exit = True
                            reason = r
                            break
                
                if should_exit:
                    pnl = (row['close'] - active_trade.entry_price) * active_trade.side
                    pnl_pct = pnl / active_trade.entry_price
                    
                    active_trade.exit_time = timestamp
                    active_trade.exit_price = row['close']
                    active_trade.pnl = pnl
                    active_trade.pnl_pct = pnl_pct
                    active_trade.duration = (timestamp - active_trade.entry_time).days
                    active_trade.exit_reason = reason
                    
                    trades.append(active_trade)
                    active_trade = None
                    
                    # Update Risk Context
                    if pnl_pct < 0:
                        context['consecutive_losses'] += 1
                        context['daily_pnl'] += pnl_pct
                    else:
                        context['consecutive_losses'] = 0
                        context['daily_pnl'] += pnl_pct
            
            # 2. Check Entry (if no active trade)
            if not active_trade:
                # Initialize log entry
                log_entry = {
                    'timestamp': timestamp,
                    'state': 'FLAT',
                    'signal_raw': False,
                    'filter_ok': True,
                    'filter_reason': None,
                    'risk_ok': True,
                    'risk_reason': None,
                    'executed': False,
                    'block_source': None,
                    'fs': 0.0,
                    'fm': 0.0,
                    'action': 'WAIT',
                    'rule_name': None,
                    'priority': None,
                    'size_mod': None,
                    'risk_profile': None
                }
                
                # Multi-Horizon Logic for Entry
                if policy.coordination_engine:
                    fs = self._calculate_horizon_signal(row, policy.horizons.get('short'))
                    fm = self._calculate_horizon_signal(row, policy.horizons.get('mid'))
                    
                    log_entry['fs'] = fs
                    log_entry['fm'] = fm
                    
                    action, params = policy.coordination_engine.evaluate("FLAT", fs, fm)
                    log_entry['action'] = action
                    log_entry['size_mod'] = params.get('size_mod')
                    log_entry['risk_profile'] = params.get('risk_profile')
                    
                    if action in ["ENTER_LONG", "ENTER_SHORT", "SCALP_LONG"]:
                        signal = 1 if action in ["ENTER_LONG", "SCALP_LONG"] else -1
                        log_entry['signal_raw'] = True
                        
                        # Check Filters
                        filter_ok = True
                        for f in policy.filters:
                            if not f.check_filter(row, context):
                                filter_ok = False
                                log_entry['filter_reason'] = f.__class__.__name__
                                log_entry['block_source'] = 'Filter'
                                break
                        log_entry['filter_ok'] = filter_ok
                        
                        # Check Risk
                        risk_ok = True
                        if filter_ok:
                            if not policy.risk_logic.check_risk_limits(context):
                                risk_ok = False
                                log_entry['risk_reason'] = 'RiskLimitHit'
                                log_entry['block_source'] = 'Risk'
                        log_entry['risk_ok'] = risk_ok
                        
                        if filter_ok and risk_ok:
                            size = policy.risk_logic.calculate_size(capital, row, None)
                            # Apply size modifier
                            size_mod = params.get('size_mod', 1.0)
                            size *= size_mod
                            
                            active_trade = Trade(
                                entry_time=timestamp,
                                entry_price=row['close'],
                                side=signal,
                                position_size=size
                            )
                            context['hwm'] = row['close']
                            log_entry['executed'] = True
                
                else:
                    # Legacy Logic
                    signal = policy.entry_logic.check_entry(row, prev_row, context)
                    log_entry['signal_raw'] = (signal != 0)
                    
                    if signal != 0:
                        # Check Filters
                        filter_ok = True
                        for f in policy.filters:
                            if not f.check_filter(row, context):
                                filter_ok = False
                                log_entry['filter_reason'] = f.__class__.__name__
                                log_entry['block_source'] = 'Filter'
                                break
                        log_entry['filter_ok'] = filter_ok
                        
                        # Check Risk
                        risk_ok = True
                        if filter_ok:
                            if not policy.risk_logic.check_risk_limits(context):
                                risk_ok = False
                                log_entry['risk_reason'] = 'RiskLimitHit'
                                log_entry['block_source'] = 'Risk'
                        log_entry['risk_ok'] = risk_ok
                        
                        if filter_ok and risk_ok:
                            size = policy.risk_logic.calculate_size(capital, row, None)
                            active_trade = Trade(
                                entry_time=timestamp,
                                entry_price=row['close'],
                                side=signal,
                                position_size=size
                            )
                            context['hwm'] = row['close']
                            log_entry['executed'] = True
                        
                # Log the signal attempt
                self.signal_logs.append(log_entry)
                    
        return trades

    def _calculate_horizon_signal(self, row: pd.Series, config: Dict[str, Any]) -> float:
        """
        Calculates signal for a given horizon configuration.
        Supports: Momentum, Trend, ORB (Opening Range Breakout), EMASlope
        """
        if not config: return 0.0
        
        type_ = config.get('type')
        params = config.get('params', {})
        normalize = params.get('normalize', False)
        
        val = 0.0
        
        # === Daily/Swing Signals ===
        if type_ in ['Momentum', 'MomentumHorizon']:
            # Simple ROC: (Close - Close[N]) / Close[N]
            # Assumes pre-calculated columns like 'mom_5'
            col = f"mom_{params['window']}"
            val = row.get(col, 0.0)
            
        elif type_ in ['Trend', 'TrendHorizon']:
            # MA Crossover or Slope
            # Assume 'trend_60' column exists
            col = f"trend_{params['window']}"
            val = row.get(col, 0.0)
        
        # === Intraday DGE Signals ===
        elif type_ in ['ORB', 'ORBMomentum']:
            # Opening Range Breakout strength
            orb_high = row.get('ORB_high', 0.0)
            orb_low = row.get('ORB_low', 0.0)
            close = row.get('close', 0.0)
            atr = row.get('ATR_15m', row.get('ATR', 1.0))
            
            # Normalized breakout distance
            if close > orb_high and orb_high > 0:
                val = (close - orb_high) / (atr + 1e-8)
            elif close < orb_low and orb_low > 0:
                val = (close - orb_low) / (atr + 1e-8)
            else:
                val = 0.0
        
        elif type_ in ['EMASlope', 'TrendSlope']:
            # EMA slope normalized by ATR and time
            window = params.get('window', 20)
            
            # Try to get pre-calculated EMA slope
            col_slope = f"ema_{window}_slope"
            if col_slope in row.index:
                val = row.get(col_slope, 0.0)
            else:
                # Fallback: calculate on the fly if EMA and lag are available
                ema_current = row.get(f"ema_{window}", 0.0)
                ema_past = row.get(f"ema_{window}_lag_{window}", 0.0)
                atr_daily = row.get('ATR_daily', row.get('ATR', 1.0))
                
                if ema_past > 0 and atr_daily > 0:
                    val = (ema_current - ema_past) / (window * atr_daily + 1e-8)
                else:
                    val = 0.0
            
        # Normalization (common for all signal types)
        if normalize:
            # Tanh scaling to [-1, 1]
            scale = params.get('scale_factor', 100.0) 
            val = np.tanh(val * scale)
            
        return val

class TradeComparator:
    """
    Compares two sets of trades (Baseline vs Miracle) to identify gaps.
    """
    def __init__(self, baseline_trades: List[Trade], miracle_trades: List[Trade]):
        self.baseline_trades = sorted(baseline_trades, key=lambda x: x.entry_time)
        self.miracle_trades = sorted(miracle_trades, key=lambda x: x.entry_time)



class TradeComparator:
    """
    Compares two sets of trades (Baseline vs Miracle) to identify gaps.
    """
    def __init__(self, baseline_trades: List[Trade], miracle_trades: List[Trade]):
        self.baseline_trades = sorted(baseline_trades, key=lambda x: x.entry_time)
        self.miracle_trades = sorted(miracle_trades, key=lambda x: x.entry_time)

    def run_comparison(self) -> pd.DataFrame:
        """
        Matches trades and calculates gaps.
        Returns a DataFrame of paired trades and their differences.
        """
        pairs = []
        baseline_idx = 0
        n_baseline = len(self.baseline_trades)
        
        for m_trade in self.miracle_trades:
            matched_b = None
            
            # Advance baseline_idx to relevant window
            while baseline_idx < n_baseline and self.baseline_trades[baseline_idx].exit_time < m_trade.entry_time:
                baseline_idx += 1
                
            # Check candidates
            curr_idx = baseline_idx
            best_overlap = 0
            
            while curr_idx < n_baseline:
                b_trade = self.baseline_trades[curr_idx]
                if b_trade.entry_time > m_trade.exit_time:
                    break # No more overlap possible
                    
                # Calculate overlap
                start = max(m_trade.entry_time, b_trade.entry_time)
                end = min(m_trade.exit_time, b_trade.exit_time)
                
                if start < end:
                    overlap = (end - start).total_seconds()
                    if overlap > best_overlap:
                        best_overlap = overlap
                        matched_b = b_trade
                
                curr_idx += 1
            
            if matched_b:
                pairs.append({
                    'type': 'MATCHED',
                    'miracle_entry': m_trade.entry_time,
                    'baseline_entry': matched_b.entry_time,
                    'entry_gap_days': (matched_b.entry_time - m_trade.entry_time).days,
                    'miracle_pnl': m_trade.pnl_pct,
                    'baseline_pnl': matched_b.pnl_pct,
                    'pnl_gap': m_trade.pnl_pct - matched_b.pnl_pct,
                    'miracle_exit_reason': m_trade.exit_reason,
                    'baseline_exit_reason': matched_b.exit_reason
                })
            else:
                pairs.append({
                    'type': 'MISSED_OPPORTUNITY',
                    'miracle_entry': m_trade.entry_time,
                    'baseline_entry': None,
                    'entry_gap_days': None,
                    'miracle_pnl': m_trade.pnl_pct,
                    'baseline_pnl': 0.0,
                    'pnl_gap': m_trade.pnl_pct,
                    'miracle_exit_reason': m_trade.exit_reason,
                    'baseline_exit_reason': None
                })
                
        return pd.DataFrame(pairs)

        years = total_days / 365.25
        trades_per_year = n_trades / years if years > 0 else 0
        
        active_days = 0
        if all_dates is not None:
            active_mask = pd.Series(False, index=all_dates)
            for t in trades:
                try:
                    # Mark days between entry and exit as active
                    # Ensure timestamps are valid for the index
                    start = t.entry_time
                    end = t.exit_time
                    if start > end: continue # Should not happen
                    
                    # Slice index
                    active_mask.loc[start:end] = True
                except KeyError:
                    pass
            active_days = active_mask.sum()
            active_day_ratio = active_days / len(all_dates) if len(all_dates) > 0 else 0
        else:
            # Approximation if all_dates not provided
            active_day_ratio = 0.0
            
        return {
            'total_return': total_pnl,
            'win_rate': win_rate,
            'trades': n_trades,
            'trades_per_year': trades_per_year,
            'active_day_ratio': active_day_ratio
        }
