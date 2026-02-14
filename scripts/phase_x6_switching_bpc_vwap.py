"""
Phase X-6: Switching Engine Integration (Champion BPC + Switching)

Components:
1. Entry Engine: X-5c Champion (tf1200_pb020_hold2_vf100)
2. Portfolio Engine: Slot-based Switching (Phase 36 Logic)
3. Bear Policy: Cap(50%) or Ban(0%) based on rolling drawdown

Goal: Verify if structural entry improvements translate to portfolio equity.
"""

import os
import glob
import numpy as np
import pandas as pd
from datetime import datetime, time as dtime, timedelta
import argparse

# ==========================================
# 1. CHAMPION BPC PARAMETERS
# ==========================================
BPC_PARAMS = {
    "no_breakout_before": dtime(12, 0),
    "pb_depth": 0.020,        # 2.0% Pullback
    "hold_bars": 2,           # Reclaim hold
    "vol_factor": 1.00,       # 1.0x Volume
    
    "vol_mult": 2.0,
    "lookback": 30,
    "vol_ma_period": 20,
    "high_update_window": 10,
    "max_wait_bars": 60,
    "stop_buffer": 0.002,     # Stop 0.2% below pb_low
    
    # Exit Params
    "tp_pct": 5.0,
    "trail_trigger_1": 2.0, "trail_stop_1": 1.0,
    "trail_trigger_2": 3.0, "trail_stop_2": 1.2,
}

# ==========================================
# 2. PORTFOLIO CONSTANTS
# ==========================================
INITIAL_CASH = 10_000_000
MAX_SLOTS = 5
COMMISSION = 0.0023  # 0.23% per trade (slippage included basically)
SLIPPAGE_BPS = 0     # Additional slippage if needed (kept 0 for apples-to-apples)

# ==========================================
# 3. CORE LOGIC
# ==========================================

class Position:
    def __init__(self, symbol, entry_time, entry_price, size, stop_price, tp_price):
        self.symbol = symbol
        self.entry_time = entry_time
        self.entry_price = entry_price
        self.size = size  # Quantity
        self.stop_price = stop_price
        self.tp_price = tp_price
        self.max_pnl_pct = 0.0
        self.trail_active = False

def load_data_cache(data_dir):
    files = glob.glob(os.path.join(data_dir, "*.csv"))
    cache = {}
    print(f"Loading {len(files)} files from {data_dir}...")
    for f in files:
        try:
            df = pd.read_csv(f, parse_dates=['ts'])
            if df.empty: continue
            
            # Hygiene
            df = df.sort_values("ts").drop_duplicates(subset=["ts"], keep="last").reset_index(drop=True)
            sym = os.path.basename(f).replace(".csv", "")
            
            # Pre-calc indicators for speed
            df["vol_ma"] = df["volume"].rolling(BPC_PARAMS['vol_ma_period']).mean()
            df["high_30"] = df["high"].rolling(BPC_PARAMS['lookback']).max()
            df["ema20"] = df["close"].ewm(span=20, adjust=False).mean()
            
            # VWAP
            tp = (df["high"] + df["low"] + df["close"]) / 3.0
            pv = tp * df["volume"]
            cum_vol = df["volume"].cumsum()
            df["vwap"] = (pv.cumsum() / cum_vol).fillna(df["close"])
            
            cache[sym] = df
        except: pass
    return cache

def bpc_signal_generator(sym, day_df, state_cache):
    """
    Stateful BPC Signal Generator per symbol/day.
    Returns: Signal dict or None
    """
    # state_cache keys: state, break_idx, break_high, pb_low, reclaim_count
    
    # Check time filter first
    last_row = day_df.iloc[-1]
    ts = last_row['ts']
    t = ts.time()
    idx = len(day_df) - 1
    
    # Initialize state if needed
    if 'state' not in state_cache:
        state_cache.update({
            'state': 'IDLE',
            'break_idx': None,
            'break_high': None,
            'pb_low': None,
            'reclaim_count': 0
        })
    
    state = state_cache['state']
    
    # 1. IDLE -> BREAKOUT
    if state == 'IDLE':
        if t < BPC_PARAMS['no_breakout_before']:
            return None
            
        # Check breakout
        # Using pre-calced indicators (need prev row)
        if idx < 1: return None
        prev = day_df.iloc[idx-1]
        
        if pd.isna(prev['vol_ma']) or pd.isna(prev['high_30']): return None
        if prev['vol_ma'] == 0: return None
        
        if (last_row['volume'] > prev['vol_ma'] * BPC_PARAMS['vol_mult'] and 
            last_row['close'] >= prev['high_30']):
            
            state_cache['state'] = 'BREAKOUT'
            state_cache['break_idx'] = idx
            state_cache['break_high'] = last_row['high']
            
    # 2. BREAKOUT -> PULLBACK
    elif state == 'BREAKOUT':
        # Expiry
        if idx - state_cache['break_idx'] > BPC_PARAMS['max_wait_bars']:
            state_cache['state'] = 'EXPIRED'
            return None
            
        # Update high (window)
        if idx - state_cache['break_idx'] <= BPC_PARAMS['high_update_window']:
            state_cache['break_high'] = max(state_cache['break_high'], last_row['high'])
            
        # Check Pullback
        threshold = state_cache['break_high'] * (1 - BPC_PARAMS['pb_depth'])
        if last_row['low'] <= threshold or last_row['close'] <= threshold:
            state_cache['state'] = 'RECLAIM_WAIT'
            state_cache['pb_low'] = last_row['low']
            state_cache['reclaim_count'] = 0
            
    # 3. RECLAIM_WAIT -> ENTRY
    elif state == 'RECLAIM_WAIT':
        # Expiry
        if idx - state_cache['break_idx'] > BPC_PARAMS['max_wait_bars'] * 2:
            state_cache['state'] = 'EXPIRED'
            return None
            
        state_cache['pb_low'] = min(state_cache['pb_low'], last_row['low'])
        
        # Reclaim condition
        vwap = last_row['vwap']
        ema20 = last_row['ema20']
        
        cond = (last_row['close'] > vwap) and (last_row['close'] > ema20)
        
        if BPC_PARAMS['vol_factor'] > 0:
            if last_row['vol_ma'] > 0:
                cond = cond and (last_row['volume'] >= last_row['vol_ma'] * BPC_PARAMS['vol_factor'])
            else:
                cond = False
                
        if cond:
            state_cache['reclaim_count'] += 1
        else:
            state_cache['reclaim_count'] = 0
            
        # Trigger
        if state_cache['reclaim_count'] >= BPC_PARAMS['hold_bars']:
            # SIGNAL GENERATED!
            signal = {
                'symbol': sym,
                'ts': ts,
                'close': last_row['close'],
                'pb_low': state_cache['pb_low'],
                'break_high': state_cache['break_high'],
                'score': 100 # Simple score for now
            }
            state_cache['state'] = 'ENTRY_TRIGGERED' # Prevent multi-signal
            return signal
            
    return None

def run_simulation(data_cache, bear_policy='cap'):
    """
    Portfolio Replay
    bear_policy: 'cap' (50% exposure) or 'ban' (0% exposure)
    """
    
    # 1. Timeline
    all_dates = sorted(list(set(d.date() for df in data_cache.values() for d in df['ts'])))
    
    cash = INITIAL_CASH
    equity = INITIAL_CASH
    positions = [] # List of Position objects
    
    equity_curve = []
    trades_log = []
    daily_stats = []
    
    rolling_dd = 0.0
    peak_equity = INITIAL_CASH
    
    print(f"Starting X-6 ({bear_policy.upper()}) Simulation on {len(all_dates)} days...")
    
    for date in all_dates:
        # Day Setup
        day_dfs = {}
        for sym, df in data_cache.items():
            day_data = df[df['ts'].dt.date == date]
            if not day_data.empty:
                day_dfs[sym] = day_data.reset_index(drop=True)
                
        if not day_dfs: continue
        
        # Determine Market Regime (Simple DD based)
        is_bear = rolling_dd < -0.05 # -5% DD defines Bear
        
        exposure_cap = 1.0
        if is_bear:
            if bear_policy == 'cap': exposure_cap = 0.5
            elif bear_policy == 'ban': exposure_cap = 0.0
            
        booked_symbols = set() # One-shot per day
        bpc_states = {} # sym -> state dict
        
        # Minute-by-minute (approximate by looping all signals? No, need sync for portfolio)
        # To be fast, we iterate minute bars across all symbols? Too slow for python.
        # fast approach: Collect all timestamps, iterate sorted unique timestamps.
        
        all_ts = sorted(list(set(t for df in day_dfs.values() for t in df['ts'])))
        
        # State tracking per minute
        current_minute_idx = {sym: 0 for sym in day_dfs}
        
        for ts in all_ts:
            # 1. Update Portfolio & Check Exits (STOP/TP/TRAIL)
            # ------------------------------------------------
            # We check OHLC of current bar for existing positions
            active_pos = []
            
            for pos in positions:
                sym = pos.symbol
                if sym not in day_dfs: 
                    active_pos.append(pos) # Data missing, assume hold
                    continue
                    
                df = day_dfs[sym]
                # Find row for ts
                # Fast lookup: assume sorted, check current_minute_idx
                # (Simple linear scan is ok if data alignment is good, but explicit is safer)
                rows = df[df['ts'] == ts]
                if rows.empty:
                    active_pos.append(pos)
                    continue
                row = rows.iloc[0]
                
                # Check Exits (Intrabar)
                exit_type = None
                exit_price = None
                
                # Update Max PnL for trailing based on HIGH
                curr_high_pnl = (row['high'] / pos.entry_price - 1) * 100
                if curr_high_pnl > pos.max_pnl_pct:
                    pos.max_pnl_pct = curr_high_pnl
                    
                # 1. Stop Loss (LOW)
                if row['low'] <= pos.stop_price:
                    exit_type = 'STOP'
                    exit_price = pos.stop_price # Slippage applied later
                # 2. TP (HIGH)
                elif row['high'] >= pos.tp_price:
                    exit_type = 'TP'
                    exit_price = pos.tp_price
                # 3. Trailing (CLOSE - logic check)
                else:
                    trail_level = None
                    if pos.max_pnl_pct >= BPC_PARAMS['trail_trigger_2']:
                        trail_level = pos.max_pnl_pct - BPC_PARAMS['trail_stop_2']
                    elif pos.max_pnl_pct >= BPC_PARAMS['trail_trigger_1']:
                        trail_level = pos.max_pnl_pct - BPC_PARAMS['trail_stop_1']
                        
                    if trail_level is not None:
                         # Trailing trigger usually on CLOSE or LOW? 
                         # User spec: "Trailing ... (close-based trigger)"
                         curr_close_pnl = (row['close'] / pos.entry_price - 1) * 100
                         if curr_close_pnl <= trail_level:
                             exit_type = 'TRAIL'
                             exit_price = row['close'] # Exit at close
                             
                if exit_type:
                    # EXECUTE EXIT
                    pnl = (exit_price - pos.entry_price) * pos.size
                    commission = exit_price * pos.size * COMMISSION
                    net_pnl = pnl - commission
                    
                    cash += (exit_price * pos.size) - commission
                    equity = cash + sum(p.size * p.entry_price for p in active_pos) # Approx
                    
                    trades_log.append({
                        'date': date,
                        'ts': ts,
                        'symbol': sym,
                        'side': 'SELL',
                        'price': exit_price,
                        'qty': pos.size,
                        'reason': exit_type,
                        'pnl': net_pnl,
                        'pnl_pct': (exit_price/pos.entry_price - 1)*100
                    })
                    booked_symbols.add(sym) # Done for day
                else:
                    active_pos.append(pos)
            
            positions = active_pos
            
            # 2. Check Signals (Entries)
            # ------------------------------------------------
            # If exposure allowed
            current_exposure = sum(p.size * p.entry_price for p in positions) # Approx cost basis
            total_cap = cash + current_exposure
            target_exposure = total_cap * exposure_cap
            available_cash_for_trade = max(0, target_exposure - current_exposure)
            
            # Simple slot logic: strict slot count? or capital based?
            # User spec: "MAX_SLOTS = 5"
            open_slots = MAX_SLOTS - len(positions)
            
            if open_slots > 0 and available_cash_for_trade > 0:
                # Scan for signals
                for sym, df in day_dfs.items():
                    if sym in booked_symbols: continue
                    if any(p.symbol == sym for p in positions): continue
                    
                    rows = df[df['ts'] == ts]
                    if rows.empty: continue
                    # Feed step-by-step
                    # To effectively use BPC generator, we ideally need to feed it row by row.
                    # Here we just pass the DF sliced up to current TS? Inefficient.
                    # Optimized: just pass the row and manually manage state.
                    # Re-using bpc_signal_generator logic but simplified for row-by-row
                    
                    # Actually, we can pre-calc signals for the whole day?
                    # NO, because we need "Portfolio State" to decide entry.
                    # But Signal GENERATION is independent of portfolio.
                    # SO: Calculate ALL signals for the day FIRST, then iterate time.
                    pass 
            
            # To optimize: Pre-calculate signals for the whole day
            # (See block below loop)
        
        # --- END OF DAY LOGIC ---
        # Close all positions EOD?
        # User spec: "EOD Exit" (implied by previous context, let's assume EOD exit for intraday strategy)
        final_active = []
        for pos in positions:
            # Sell at EOD Close
            sym = pos.symbol
            if sym in day_dfs:
                price = day_dfs[sym].iloc[-1]['close']
                ts = day_dfs[sym].iloc[-1]['ts']
                
                pnl = (price - pos.entry_price) * pos.size
                commission = price * pos.size * COMMISSION
                net_pnl = pnl - commission
                cash += (price * pos.size) - commission
                
                trades_log.append({
                    'date': date,
                    'ts': ts,
                    'symbol': sym,
                    'side': 'SELL',
                    'price': price,
                    'qty': pos.size,
                    'reason': 'EOD',
                    'pnl': net_pnl,
                    'pnl_pct': (price/pos.entry_price - 1)*100
                })
            else:
                # Hold over? Assuming intraday for consistency
                # Force close at entry price (neutral) if missing data
                cash += pos.size * pos.entry_price
        
        positions = [] # Clear positions EOD
        
        # Recalc Equity
        equity = cash 
        if equity > peak_equity: peak_equity = equity
        dd = (equity - peak_equity) / peak_equity
        rolling_dd = dd # Carry over to next day regime
        
        daily_stats.append({
            'date': date,
            'equity': equity,
            'dd': dd,
            'trades': len([t for t in trades_log if t['date'] == date and t['side']=='SELL'])
        })
        equity_curve.append({'date': date, 'equity': equity})
        
        print(f"Date: {date} | Eq: {int(equity)} | DD: {dd*100:.2f}% | Trades: {daily_stats[-1]['trades']}")

    # ==========================
    # Pre-Calculation Optimization
    # ==========================
    # To fix the loop structure:
    # 1. For each day, pre-calculate ALL BPC signals for ALL symbols.
    # 2. Sort signals by time.
    # 3. Iterate through time, processing signals against portfolio slots.
    
    return daily_stats, trades_log, equity_curve

# RE-WRITING MAIN LOOP FOR CORRECT ARCHITECTURE
def run_simulation_optimized(data_cache, bear_policy='cap'):
    all_dates = sorted(list(set(d.date() for df in data_cache.values() for d in df['ts'])))
    
    cash = INITIAL_CASH
    equity = INITIAL_CASH
    rolling_dd = 0.0
    peak_equity = INITIAL_CASH
    
    all_trades = []
    equity_history = []
    
    print(f"Starting X-6 Optimized ({bear_policy}) Replay...")
    
    for date in all_dates:
        # 1. Regime Check
        is_bear = rolling_dd <= -0.05
        exposure_cap = 1.0
        if is_bear:
            exposure_cap = 0.5 if bear_policy == 'cap' else 0.0
            
        if exposure_cap == 0.0:
            # Skip day trading
            equity_history.append({'date': date, 'equity': equity, 'dd': rolling_dd})
            continue

        # 2. Prepare Signals
        day_dfs = {}
        daily_signals = []
        
        for sym, full_df in data_cache.items():
            day_df = full_df[full_df['ts'].dt.date == date]
            if day_df.empty: continue
            day_dfs[sym] = day_df.copy().reset_index(drop=True)
            
            # Generate Signals per symbol
            # Reusing the logic from BPC generator but iterating inside here
            # Ideally this logic is in the 'bpc_signal_generator' function
            # But we need to run it for the whole DF day
            
            # Run generator
            state_cache = {}
            for i in range(len(day_df)):
                # Hack: feeding incremental DF simulation
                # Optimization: Pass full DF and idx
                # Actually, let's implement a 'get_day_signal' helper that runs once
                pass

        # Helper to get signal (one-shot per day)
        signals = []
        for sym, df in day_dfs.items():
            sig = get_first_bpc_signal(sym, df)
            if sig: signals.append(sig)
            
        signals.sort(key=lambda x: x['entry_ts'])
        
        # 3. Execute Day
        positions = [] # list of dicts
        booked_syms = set()
        
        # Time Management
        # We need to simulate exits minute by minute to free up slots
        # Merge signal times and minute bars? 
        # Easier: Minute-by-minute loop, check if signal triggers AND exits trigger
        
        # Master Timeline
        minute_set = set()
        for df in day_dfs.values():
            minute_set.update(df['ts'].tolist())
        timeline = sorted(list(minute_set))
        
        signal_idx = 0
        
        for ts in timeline:
            # A. Process Exits First
            active_pos = []
            for pos in positions:
                sym = pos['symbol']
                df = day_dfs[sym]
                rows = df[df['ts'] == ts]
                if rows.empty: 
                    active_pos.append(pos)
                    continue
                row = rows.iloc[0]
                
                exit_res = check_exit(pos, row)
                if exit_res:
                    # Execute Exit
                    px = exit_res['price']
                    qty = pos['qty']
                    comm = px * qty * COMMISSION
                    pnl = (px - pos['entry_price']) * qty - comm
                    cash += (px * qty) - comm
                    
                    all_trades.append({
                        'date': date, 'ts': ts, 'symbol': sym, 'side': 'SELL',
                        'price': px, 'qty': qty, 'reason': exit_res['reason'],
                        'pnl': pnl
                    })
                else:
                    active_pos.append(pos)
            positions = active_pos
            
            # B. Process Entries
            # Check for signals at this exact minute (or triggered previous minute for open execution)
            # Signal 'entry_ts' is usually "next bar open". 
            # So if BPC triggered at T, entry is T+1.
            
            while signal_idx < len(signals) and signals[signal_idx]['entry_ts'] <= ts:
                sig = signals[signal_idx]
                signal_idx += 1
                
                if sig['entry_ts'] != ts: continue # Must match exactly (already sorted)
                
                sym = sig['symbol']
                if sym in booked_syms: continue
                
                # Check Constraints
                current_exposure = sum(p['qty'] * p['entry_price'] for p in positions)
                total_eq = cash + current_exposure
                target_limit = total_eq * exposure_cap
                
                if len(positions) < MAX_SLOTS and (current_exposure < target_limit):
                    # Calc Size
                    per_slot_cash = total_eq / MAX_SLOTS
                    # Cap by bear limit?
                    # If bear cap is 50%, and slots=5, each slot is 10%?
                    # Or fill slots until 50% reached?
                    # Standard: Equal weight of EQUITY.
                    # If cap=0.5, total investable = 0.5 * Eq. 5 slots. Each slot = 0.1 * Eq.
                    
                    size_amt = total_eq / MAX_SLOTS 
                    # Check if this addition breaches exposure cap
                    if current_exposure + size_amt > target_limit:
                        size_amt = max(0, target_limit - current_exposure)
                    
                    if size_amt < 10000: continue # Min trade size
                    
                    qty = int(size_amt / sig['entry_px'])
                    if qty > 0:
                        cost = qty * sig['entry_px']
                        comm = cost * COMMISSION
                        cash -= (cost + comm)
                        
                        stop_px = sig['pb_low'] * (1 - BPC_PARAMS['stop_buffer'])
                        tp_px = sig['entry_px'] * (1 + BPC_PARAMS['tp_pct']/100)
                        
                        pos = {
                            'symbol': sym,
                            'entry_price': sig['entry_px'],
                            'qty': qty,
                            'stop_price': stop_px,
                            'tp_price': tp_px,
                            'max_pnl_pct': 0.0,
                            'ts': ts
                        }
                        positions.append(pos)
                        booked_syms.add(sym)
                        
                        all_trades.append({
                            'date': date, 'ts': ts, 'symbol': sym, 'side': 'BUY',
                            'price': sig['entry_px'], 'qty': qty, 'reason': 'BPC_SIGNAL',
                            'pnl': 0
                        })

        # C. EOD Exit
        for pos in positions:
            sym = pos['symbol']
            row = day_dfs[sym].iloc[-1]
            px = row['close']
            qty = pos['qty']
            comm = px * qty * COMMISSION
            pnl = (px - pos['entry_price']) * qty - comm
            cash += (px * qty) - comm
            
            all_trades.append({
                'date': date, 'ts': row['ts'], 'symbol': sym, 'side': 'SELL',
                'price': px, 'qty': qty, 'reason': 'EOD',
                'pnl': pnl
            })
            
        # Update Equity
        equity = cash 
        if equity > peak_equity: peak_equity = equity
        rolling_dd = (equity - peak_equity) / peak_equity
        equity_history.append({'date': date, 'equity': equity, 'dd': rolling_dd})
        
        print(f"Date: {date} | Eq: {int(equity)} | Trades: {len([t for t in all_trades if t['date']==date and t['side']=='BUY'])}")
        
    return equity_history, all_trades

# Helper: One-shot Signal Scraper
def get_first_bpc_signal(sym, df):
    # Run loop to get FIRST triggering signal
    # Same logic as BPC generator
    # Returns {symbol, entry_ts, entry_px, pb_low}
    
    # State
    state = 'IDLE'
    break_idx = 0
    break_high = 0
    pb_low = 0
    reclaim_count = 0
    
    start_idx = max(BPC_PARAMS['lookback'], BPC_PARAMS['vol_ma_period']) + 1
    
    for i in range(start_idx, len(df)):
        row = df.iloc[i]
        t = row['ts'].time()
        
        if state == 'IDLE':
            if t < BPC_PARAMS['no_breakout_before']: continue
            prev = df.iloc[i-1]
            # Breakout check...
            if (row['volume'] > prev['vol_ma'] * BPC_PARAMS['vol_mult'] and 
                row['close'] >= prev['high_30']):
                state = 'BREAKOUT'
                break_idx = i
                break_high = row['high']
                
        elif state == 'BREAKOUT':
            if i - break_idx > BPC_PARAMS['max_wait_bars']:
                state = 'EXPIRED'; break
            if i - break_idx <= BPC_PARAMS['high_update_window']:
                break_high = max(break_high, row['high'])
                
            stop_thresh = break_high * (1 - BPC_PARAMS['pb_depth'])
            if row['low'] <= stop_thresh or row['close'] <= stop_thresh:
                state = 'RECLAIM_WAIT'
                pb_low = row['low']
                reclaim_count = 0
                
        elif state == 'RECLAIM_WAIT':
            if i - break_idx > BPC_PARAMS['max_wait_bars']*2:
                 state = 'EXPIRED'; break
            pb_low = min(pb_low, row['low'])
            
            cond = (row['close'] > row['vwap']) and (row['close'] > row['ema20'])
            if BPC_PARAMS['vol_factor'] > 0:
                cond = cond and (row['volume'] >= row['vol_ma'] * BPC_PARAMS['vol_factor'])
            
            if cond: reclaim_count += 1
            else: reclaim_count = 0
            
            if reclaim_count >= BPC_PARAMS['hold_bars']:
                # SIGNAL! Entry at NEXT BAR OPEN
                if i+1 < len(df):
                    entry_row = df.iloc[i+1]
                    return {
                        'symbol': sym,
                        'entry_ts': entry_row['ts'],
                        'entry_px': entry_row['open'],
                        'pb_low': pb_low
                    }
                else: break
    return None

def check_exit(pos, row):
    # Returns {reason, price} or None
    
    # Update trail
    high_pnl = (row['high']/pos['entry_price'] - 1)*100
    pos['max_pnl_pct'] = max(pos['max_pnl_pct'], high_pnl)
    
    # Stop
    if row['low'] <= pos['stop_price']:
        return {'reason': 'STOP', 'price': pos['stop_price']} # Assuming execution at stop
    
    # TP
    if row['high'] >= pos['tp_price']:
        return {'reason': 'TP', 'price': pos['tp_price']}
        
    # Trail
    trail_level = None
    if pos['max_pnl_pct'] >= BPC_PARAMS['trail_trigger_2']:
        trail_level = pos['max_pnl_pct'] - BPC_PARAMS['trail_stop_2']
    elif pos['max_pnl_pct'] >= BPC_PARAMS['trail_trigger_1']:
        trail_level = pos['max_pnl_pct'] - BPC_PARAMS['trail_stop_1']
        
    if trail_level is not None:
        close_pnl = (row['close']/pos['entry_price'] - 1)*100
        if close_pnl <= trail_level:
            return {'reason': 'TRAIL', 'price': row['close']}
            
    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_dir", default="GARAM_Data/60day_replay_kst")
    parser.add_argument("--bear_policy", default="cap", choices=["cap", "ban"])
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()
    
    cache = load_data_cache(args.data_dir)
    history, trades = run_simulation_optimized(cache, args.bear_policy)
    
    # Save Results
    pd.DataFrame(trades).to_csv("GARAM_Data/x6_trades.csv", index=False)
    pd.DataFrame(history).to_csv("GARAM_Data/x6_daily.csv", index=False)
    
    # Summary
    final_eq = history[-1]['equity']
    ret = (final_eq / INITIAL_CASH - 1) * 100
    mdd = min(h['dd'] for h in history) * 100
    
    print("\n" + "="*50)
    print("PHASE X-6 RESULTS")
    print("="*50)
    print(f"Bear Policy: {args.bear_policy.upper()}")
    print(f"Final Equity: {int(final_eq):,}")
    print(f"Return: {ret:.2f}%")
    print(f"MDD: {mdd:.2f}%")
    
    # Trade Stats
    if trades:
        df = pd.DataFrame(trades)
        exits = df[df['side']=='SELL']
        stop = len(exits[exits['reason']=='STOP'])
        tp = len(exits[exits['reason']=='TP'])
        trail = len(exits[exits['reason']=='TRAIL'])
        eod = len(exits[exits['reason']=='EOD'])
        total = len(exits)
        
        print(f"\nTrade Stats (Total {total}):")
        print(f"STOP: {stop} ({stop/total*100:.1f}%)")
        print(f"TP:   {tp} ({tp/total*100:.1f}%)")
        print(f"TRAIL:{trail} ({trail/total*100:.1f}%)")
        print(f"EOD:  {eod} ({eod/total*100:.1f}%)")
    
    print("="*50)

if __name__ == "__main__":
    main()
