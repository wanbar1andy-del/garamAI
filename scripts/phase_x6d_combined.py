
"""
Phase X-6d: Combined Engine (Regime Recovery + Early Escape + Hero Switching)

Integrates:
1. X-6c Regime Logic (Ban/Unban Option A, Staged Recovery)
2. X-6d Efficiency Logic (Fail-Fast Escape, Smart Switching, Hero Override)
"""

import os
import glob
import numpy as np
import pandas as pd
from datetime import datetime, time as dtime, timedelta
import argparse

# ==========================================
# 1. CHAMPION BPC PARAMETERS (X-5c Base)
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
    
    "tp_pct": 5.0,
    "trail_trigger_1": 2.0, "trail_stop_1": 1.0,
    "trail_trigger_2": 3.0, "trail_stop_2": 1.2,
}

# ==========================================
# 2. X-6d EFFICIENCY PARAMETERS
# ==========================================
EFFICIENCY_PARAMS = {
    # Escape
    "min_hold_mins": 5,             # Immunity period
    "reclaim_loss_bars": 2,         # Exit if Close < VWAP & EMA20 for 2 min
    "hard_exit_pnl": -0.007,        # -0.7% Force Exit (Fail Fast)
    
    # Switching
    "switch_threshold_pnl": -0.003, # Only switch if losing > 0.3%
    "min_score_edge": 0.10,         # New score > Old * 1.1
    
    # Hero
    "hero_score_abs": 3.0,          # Absolute Score (Vol Ratio) for Hero
    "hero_override_per_day": 1,     # Max 1 Hero Override/day
    "hero_target_frac": 0.60,       # Hero gets 60% of exposure
}

INITIAL_CASH = 10_000_000
MAX_SLOTS = 5
COMMISSION = 0.0023 

# ==========================================
# 3. REGIME & UNBAN PARAMS (X-6c)
# ==========================================
REGIME_PARAMS = {
    "bear_dd_trigger": -0.05,       # -5% DD starts BAN
    "min_ban_days": 5,
    "unban_lookback": 3,
    "unban_min_days_with_signals": 2,
    "unban_min_signals_per_day": 3,
    "recovery_stage_days": 2,       # Days at 20% cap
    "recovery_cap": 0.20,
    "bear_cap": 0.50                # Cap after recovery but still in DD
}

def load_data_cache(data_dir):
    files = glob.glob(os.path.join(data_dir, "*.csv"))
    cache = {}
    print(f"Loading {len(files)} files from {data_dir}...")
    for f in files:
        try:
            df = pd.read_csv(f, parse_dates=['ts'])
            if df.empty: continue
            df = df.sort_values("ts").drop_duplicates(subset=["ts"], keep="last").reset_index(drop=True)
            
            # Pre-calc indicators
            df["vol_ma"] = df["volume"].rolling(BPC_PARAMS['vol_ma_period']).mean()
            df["high_30"] = df["high"].rolling(BPC_PARAMS['lookback']).max()
            df["ema20"] = df["close"].ewm(span=20, adjust=False).mean()
            
            tp = (df["high"] + df["low"] + df["close"]) / 3.0
            pv = tp * df["volume"]
            df["vwap"] = (pv.cumsum() / df["volume"].cumsum()).fillna(df["close"])
            
            sym = os.path.basename(f).replace(".csv", "")
            cache[sym] = df
        except: pass
    return cache

def get_bpc_signals_for_day(sym, df, date_filter):
    """
    Returns counts of potential signals for UNBAN logic.
    Also returns Score (Vol Ratio) for Hero logic.
    """
    day_df = df[df['ts'].dt.date == date_filter].reset_index(drop=True)
    if day_df.empty: return []

    signals = []
    
    state = 'IDLE'
    break_idx = 0
    break_high = 0
    pb_low = 0
    reclaim_count = 0
    start_idx = max(BPC_PARAMS['lookback'], BPC_PARAMS['vol_ma_period']) + 1

    for i in range(start_idx, len(day_df)):
        row = day_df.iloc[i]
        t = row['ts'].time()
        
        if state == 'IDLE':
            if t < BPC_PARAMS['no_breakout_before']: continue
            prev = day_df.iloc[i-1]
            if (row['volume'] > prev['vol_ma'] * BPC_PARAMS['vol_mult'] and 
                row['close'] >= prev['high_30']):
                state = 'BREAKOUT'
                break_idx = i
                break_high = row['high']
                
        elif state == 'BREAKOUT':
            if i - break_idx > BPC_PARAMS['max_wait_bars']:
                state = 'IDLE'; continue 
            if i - break_idx <= BPC_PARAMS['high_update_window']:
                break_high = max(break_high, row['high'])
                
            stop_thresh = break_high * (1 - BPC_PARAMS['pb_depth'])
            if row['low'] <= stop_thresh or row['close'] <= stop_thresh:
                state = 'RECLAIM_WAIT'
                pb_low = row['low']
                reclaim_count = 0
                
        elif state == 'RECLAIM_WAIT':
            if i - break_idx > BPC_PARAMS['max_wait_bars']*2:
                 state = 'IDLE'; continue
            pb_low = min(pb_low, row['low'])
            
            cond = (row['close'] > row['vwap']) and (row['close'] > row['ema20'])
            if BPC_PARAMS['vol_factor'] > 0:
                cond = cond and (row['volume'] >= row['vol_ma'] * BPC_PARAMS['vol_factor'])
            
            if cond: reclaim_count += 1
            else: reclaim_count = 0
            
            if reclaim_count >= BPC_PARAMS['hold_bars']:
                if i+1 < len(day_df):
                    entry_row = day_df.iloc[i+1]
                    
                    # Calculate Score (Vol Ratio as proxy for conviction)
                    # Use breakout volume / MA
                    brk_row = day_df.iloc[break_idx]
                    vol_ratio = 1.0
                    if brk_row['vol_ma'] > 0:
                        vol_ratio = brk_row['volume'] / brk_row['vol_ma']
                    
                    sig = {
                        'symbol': sym,
                        'entry_ts': entry_row['ts'],
                        'entry_px': entry_row['open'],
                        'pb_low': pb_low,
                        'break_high': break_high,
                        'score': vol_ratio # Logic: Higher vol ratio = stronger breakout
                    }
                    signals.append(sig)
                    return [sig] 
    return signals

def run_simulation_x6d(data_cache):
    all_dates = sorted(list(set(d.date() for df in data_cache.values() for d in df['ts'])))
    
    cash = INITIAL_CASH
    equity = INITIAL_CASH
    peak_equity = INITIAL_CASH
    rolling_dd = 0.0
    
    # Regime State
    regime = 'NORMAL' 
    ban_start_date = None
    recovery_start_date = None
    
    history_signals_count = [] 
    
    all_trades = []
    equity_history = []
    regime_log = []
    
    print(f"Starting X-6d (Combined Logic) Replay on {len(all_dates)} days...")
    
    for current_date in all_dates:
        # --- REGIME LOGIC (X-6c) ---
        if equity > peak_equity: peak_equity = equity
        rolling_dd = (equity - peak_equity) / peak_equity
        
        exposure_cap = 1.0
        
        # A. Trigger BAN?
        if regime in ['NORMAL', 'RECOVERY'] and rolling_dd <= REGIME_PARAMS['bear_dd_trigger']:
             if regime != 'BAN': 
                 regime = 'BAN'
                 ban_start_date = current_date
                 regime_log.append({'date': current_date, 'event': 'BAN_TRIGGERED', 'dd': rolling_dd})
        
        # B. Trigger UNBAN?
        if regime == 'BAN':
             exposure_cap = 0.0
             idx = all_dates.index(current_date)
             ban_idx = all_dates.index(ban_start_date)
             
             if (idx - ban_idx) >= REGIME_PARAMS['min_ban_days']:
                 recent_counts = [c for d, c in history_signals_count if d < current_date][-REGIME_PARAMS['unban_lookback']:]
                 valid_days = sum(1 for c in recent_counts if c >= REGIME_PARAMS['unban_min_signals_per_day'])
                 if valid_days >= REGIME_PARAMS['unban_min_days_with_signals']:
                     regime = 'RECOVERY'
                     recovery_start_date = current_date
                     regime_log.append({'date': current_date, 'event': 'UNBAN_TRIGGERED', 'dd': rolling_dd})
                     
        # C. Handle RECOVERY
        if regime == 'RECOVERY':
            idx = all_dates.index(current_date)
            rec_idx = all_dates.index(recovery_start_date)
            days_in_recovery = idx - rec_idx
            
            if days_in_recovery < REGIME_PARAMS['recovery_stage_days']:
                exposure_cap = REGIME_PARAMS['recovery_cap'] # 20%
            else:
                if rolling_dd > REGIME_PARAMS['bear_dd_trigger']:
                    regime = 'NORMAL'; exposure_cap = 1.0
                else:
                    exposure_cap = REGIME_PARAMS['bear_cap'] # 50%
        
        # --- SIGNAL PREP ---
        day_signals = []
        full_day_dfs = {}
        signal_count_today = 0
        
        for sym, full_df in data_cache.items():
            sigs = get_bpc_signals_for_day(sym, full_df, current_date)
            if sigs:
                signal_count_today += 1 
                day_signals.extend(sigs)
            d_df = full_df[full_df['ts'].dt.date == current_date]
            if not d_df.empty:
                full_day_dfs[sym] = d_df.reset_index(drop=True)
                
        history_signals_count.append((current_date, signal_count_today))
        day_signals.sort(key=lambda x: x['entry_ts'])
        
        # --- EXECUTION (X-6d Logic) ---
        positions = [] 
        booked_syms = set()
        hero_overrides_today = 0
        
        if exposure_cap > 0:
            minute_set = set()
            for df in full_day_dfs.values(): minute_set.update(df['ts'].tolist())
            timeline = sorted(list(minute_set))
            
            sig_idx = 0
            
            for ts in timeline:
                # 1. EARLY ESCAPE & EXITS (Fail-Fast)
                active_pos = []
                for pos in positions:
                    df = full_day_dfs.get(pos['symbol'])
                    if df is None: active_pos.append(pos); continue
                    rows = df[df['ts'] == ts]
                    if rows.empty: active_pos.append(pos); continue
                    row = rows.iloc[0]
                    
                    exit_res = None
                    pos['max_pnl_pct'] = max(pos['max_pnl_pct'], (row['high']/pos['entry_price']-1)*100)
                    
                    # Standard Exits
                    if row['low'] <= pos['stop_price']: exit_res = {'reason': 'STOP', 'px': pos['stop_price']}
                    elif row['high'] >= pos['tp_price']: exit_res = {'reason': 'TP', 'px': pos['tp_price']}
                    else:
                        trail_level = None
                        if pos['max_pnl_pct'] >= BPC_PARAMS['trail_trigger_2']: trail_level = pos['max_pnl_pct'] - BPC_PARAMS['trail_stop_2']
                        elif pos['max_pnl_pct'] >= BPC_PARAMS['trail_trigger_1']: trail_level = pos['max_pnl_pct'] - BPC_PARAMS['trail_stop_1']
                        if trail_level is not None and (row['close']/pos['entry_price']-1)*100 <= trail_level:
                            exit_res = {'reason': 'TRAIL', 'px': row['close']}
                    
                    # X-6d: Fail-Fast Escape (User Logic)
                    if not exit_res:
                        held_mins = (ts - pos['entry_ts']).total_seconds() / 60.0
                        if held_mins >= EFFICIENCY_PARAMS['min_hold_mins']:
                            current_pnl = (row['close']/pos['entry_price'] - 1)
                            
                            # Hard Loss (-0.7%)
                            if current_pnl <= EFFICIENCY_PARAMS['hard_exit_pnl']:
                                exit_res = {'reason': 'HARD_LOSS', 'px': row['close']}
                            else:
                                # Reclaim Loss (2 bars)
                                # Check last N bars for Close < VWAP and Close < EMA20
                                sub_df = df[df['ts'] <= ts].tail(EFFICIENCY_PARAMS['reclaim_loss_bars'])
                                if len(sub_df) == EFFICIENCY_PARAMS['reclaim_loss_bars']:
                                    lost = ((sub_df['close'] < sub_df['vwap']) & (sub_df['close'] < sub_df['ema20'])).all()
                                    if lost:
                                        exit_res = {'reason': 'RECLAIM_LOST', 'px': row['close']}

                    if exit_res:
                        px = exit_res['px']
                        qty = pos['qty']
                        comm = px*qty*COMMISSION
                        cash += px*qty - comm
                        all_trades.append({'date': current_date, 'ts': ts, 'side': 'SELL', 'symbol': pos['symbol'], 'reason': exit_res['reason'], 'price': px, 'qty': qty})
                    else:
                        active_pos.append(pos)
                positions = active_pos
                
                # 2. ENTRIES & SWITCHING
                while sig_idx < len(day_signals) and day_signals[sig_idx]['entry_ts'] <= ts:
                    sig = day_signals[sig_idx]
                    sig_idx += 1
                    if sig['entry_ts'] != ts: continue
                    sym = sig['symbol']
                    if sym in booked_syms: continue
                    
                    # Prep Context
                    curr_exp = sum(p['qty']*p['entry_price'] for p in positions)
                    total_eq = cash + curr_exp
                    target_limit = total_eq * exposure_cap
                    
                    is_hero = sig['score'] >= EFFICIENCY_PARAMS['hero_score_abs']
                    
                    # Logic A: Standard Entry (Slots Available)
                    if len(positions) < MAX_SLOTS and curr_exp < target_limit:
                        # Size Logic: Hero Override Target?
                        # User spec: "Hero Target 60%".
                        # If Hero, we want to take up to 60% of equity. 
                        # If existing positions exist, they utilize slot space.
                        # Entering Hero here implies we have SPACE.
                        
                        size_amount = total_eq / MAX_SLOTS
                        if is_hero: 
                             # Target 60% allocation for this single position? 
                             # Or 60% of total equity? Yes "target fraction of max_exposure".
                             # If we have cash for it.
                             target_amt = total_eq * EFFICIENCY_PARAMS['hero_target_frac']
                             size_amount = target_amt
                             if hero_overrides_today < EFFICIENCY_PARAMS['hero_override_per_day']:
                                 hero_overrides_today += 1
                        
                        # Cap by available cash/limit
                        available_for_new = max(0, target_limit - curr_exp)
                        if size_amount > available_for_new: size_amount = available_for_new
                        
                        if size_amount > 10000:
                            qty = int(size_amount / sig['entry_px'])
                            if qty > 0:
                                cost = qty * sig['entry_px']
                                comm = cost * COMMISSION
                                cash -= (cost + comm)
                                pos = {
                                    'symbol': sym, 'entry_price': sig['entry_px'], 'qty': qty, 'entry_ts': sig['entry_ts'],
                                    'stop_price': sig['pb_low']*(1-BPC_PARAMS['stop_buffer']),
                                    'tp_price': sig['entry_px']*(1+BPC_PARAMS['tp_pct']/100),
                                    'max_pnl_pct': 0.0, 'score_at_entry': sig['score']
                                }
                                positions.append(pos)
                                booked_syms.add(sym)
                                all_trades.append({'date': current_date, 'ts': ts, 'side': 'BUY', 'symbol': sym, 'price': sig['entry_px'], 'qty': qty, 'note': 'HERO' if is_hero else ''})
                    
                    # Logic B: Switching (Slots Full)
                    elif len(positions) >= MAX_SLOTS:
                        # Find Candidate to Drop
                        weakest = None
                        min_score = 999
                        
                        for p in positions:
                            if p['score_at_entry'] < min_score:
                                min_score = p['score_at_entry']
                                weakest = p
                        
                        # Hero Force Logic (Override) - User Spec "Clear others -> Enter Hero"
                        if is_hero and hero_overrides_today < EFFICIENCY_PARAMS['hero_override_per_day']:
                            # Force kill ALL non-Hero positions to make room for 60% Hero
                            active_pos = []
                            for p in positions:
                                df = full_day_dfs[p['symbol']]
                                cur_px = df[df['ts']==ts].iloc[0]['close']
                                q = p['qty']
                                val = cur_px * q * (1-COMMISSION)
                                cash += val
                                all_trades.append({'date': current_date, 'ts': ts, 'side': 'SELL', 'symbol': p['symbol'], 'price': cur_px, 'qty': q, 'reason': 'HERO_CLEAR'})
                            positions = [] # All gone
                            
                            # Buy Hero (60% Target)
                            total_eq_now = cash
                            target_limit = total_eq_now * exposure_cap
                            size_amt = total_eq_now * EFFICIENCY_PARAMS['hero_target_frac']
                            if size_amt > target_limit: size_amt = target_limit
                            
                            qty = int(size_amt / sig['entry_px'])
                            if qty > 0:
                                cost = qty * sig['entry_px']
                                comm = cost * COMMISSION
                                cash -= (cost + comm)
                                pos = {
                                    'symbol': sym, 'entry_price': sig['entry_px'], 'qty': qty, 'entry_ts': sig['entry_ts'],
                                    'stop_price': sig['pb_low']*(1-BPC_PARAMS['stop_buffer']),
                                    'tp_price': sig['entry_px']*(1+BPC_PARAMS['tp_pct']/100),
                                    'max_pnl_pct': 0.0, 'score_at_entry': sig['score']
                                }
                                positions.append(pos)
                                booked_syms.add(sym)
                                all_trades.append({'date': current_date, 'ts': ts, 'side': 'BUY', 'symbol': sym, 'price': sig['entry_px'], 'qty': qty, 'note': 'HERO_OVERRIDE'})
                                hero_overrides_today += 1
                        
                        # Standard Smart Switching
                        elif weakest: 
                            # 1. Check PnL (Must be losing <= -0.3%)
                            df = full_day_dfs[weakest['symbol']]
                            cur_px = df[df['ts']==ts].iloc[0]['close']
                            weak_pnl = (cur_px / weakest['entry_price'] - 1)
                            
                            if weak_pnl <= EFFICIENCY_PARAMS['switch_threshold_pnl']:
                                # 2. Check Score Edge
                                if sig['score'] > weakest['score_at_entry'] * (1 + EFFICIENCY_PARAMS['min_score_edge']):
                                    # Execute Switch
                                    q = weakest['qty']
                                    val = cur_px * q * (1-COMMISSION)
                                    cash += val
                                    positions.remove(weakest)
                                    all_trades.append({'date': current_date, 'ts': ts, 'side': 'SELL', 'symbol': weakest['symbol'], 'price': cur_px, 'qty': q, 'reason': 'SWITCH_OUT'})
                                    
                                    # Buy New (Standard Slot)
                                    total_eq = cash + sum(p['qty']*p['entry_price'] for p in positions)
                                    size_amt = total_eq / MAX_SLOTS
                                    target_limit = total_eq * exposure_cap
                                    curr_exp = sum(p['qty']*p['entry_price'] for p in positions)
                                    if curr_exp + size_amt > target_limit: size_amt = target_limit - curr_exp
                                    
                                    qty = int(size_amt / sig['entry_px'])
                                    if qty > 0:
                                        cost = qty * sig['entry_px']
                                        comm = cost * COMMISSION
                                        cash -= (cost + comm)
                                        pos = {
                                            'symbol': sym, 'entry_price': sig['entry_px'], 'qty': qty, 'entry_ts': sig['entry_ts'],
                                            'stop_price': sig['pb_low']*(1-BPC_PARAMS['stop_buffer']),
                                            'tp_price': sig['entry_px']*(1+BPC_PARAMS['tp_pct']/100),
                                            'max_pnl_pct': 0.0, 'score_at_entry': sig['score']
                                        }
                                        positions.append(pos)
                                        booked_syms.add(sym)
                                        all_trades.append({'date': current_date, 'ts': ts, 'side': 'BUY', 'symbol': sym, 'price': sig['entry_px'], 'qty': qty, 'reason': 'SWITCH_IN'})

        # EOD Close (Execution)
        for pos in positions:
            sym = pos['symbol']
            df = full_day_dfs.get(sym)
            if df is not None:
                px = df.iloc[-1]['close']
                qty = pos['qty']
                comm = px*qty*COMMISSION
                cash += px*qty - comm
                all_trades.append({'date': current_date, 'ts': df.iloc[-1]['ts'], 'side': 'SELL', 'symbol': sym, 'reason': 'EOD', 'price': px, 'qty': qty})
        
        equity = cash
        equity_history.append({'date': current_date, 'equity': equity, 'regime': regime, 'exposure': exposure_cap})
        print(f"{current_date} | Eq: {int(equity)} | Regime: {regime}")

    return equity_history, all_trades, regime_log

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_dir", default="GARAM_Data/60day_replay_kst")
    args = parser.parse_args()
    
    cache = load_data_cache(args.data_dir)
    history, trades, logs = run_simulation_x6d(cache)
    
    # Save
    pd.DataFrame(history).to_csv("GARAM_Data/x6d_daily.csv", index=False)
    pd.DataFrame(trades).to_csv("GARAM_Data/x6d_trades.csv", index=False)
    
    final_eq = history[-1]['equity']
    ret = (final_eq / INITIAL_CASH - 1) * 100
    
    print("\nX-6d RESULTS")
    print(f"Final Equity: {int(final_eq):,}")
    print(f"Return: {ret:.2f}%")
    
if __name__ == "__main__":
    main()
