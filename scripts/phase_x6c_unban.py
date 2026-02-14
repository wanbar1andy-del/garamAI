"""
Phase X-6c: Switching Engine with Regime Recovery (Ban + Unban)

Implements User Option A:
- BAN: DD <= -5% -> Exposure 0%
- UNBAN: 
    - Min 5 days wait.
    - Signal Logic: Last 3 days, >= 2 days with >= 3 signals.
    - Staging: 20% Exposure (2 days) -> 50% Exposure (Bear Cap) -> 100% (If DD clears)
"""

import os
import glob
import numpy as np
import pandas as pd
from datetime import datetime, time as dtime, timedelta
import argparse

# ==========================================
# 1. CHAMPION BPC PARAMETERS (X-5c)
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

INITIAL_CASH = 10_000_000
MAX_SLOTS = 5
COMMISSION = 0.0023 

# ==========================================
# 2. REGIME & UNBAN PARAMS
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
    """
    day_df = df[df['ts'].dt.date == date_filter].reset_index(drop=True)
    if day_df.empty: return []

    signals = []
    
    # Simple Loop logic (Reused from X-6)
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
                state = 'EXPIRED'; continue # Fixed to continue loop? No in generator we reset.
                # Here simplified: Reset to IDLE? No, Wait for next breakout?
                # Actually original logic: state machine just resets.
                state = 'IDLE' 
                continue 
                
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
                # Valid Signal Found
                if i+1 < len(day_df):
                    entry_row = day_df.iloc[i+1]
                    sig = {
                        'symbol': sym,
                        'entry_ts': entry_row['ts'],
                        'entry_px': entry_row['open'],
                        'pb_low': pb_low,
                        'break_high': break_high
                    }
                    signals.append(sig)
                    # One shot? Yes, one per day for checking purposes?
                    # But for "Signal Count", we count valid triggers.
                    # User spec: "One shot per symbol". So 1 max per symbol.
                    return [sig] 
    return signals

def run_simulation_x6c(data_cache):
    all_dates = sorted(list(set(d.date() for df in data_cache.values() for d in df['ts'])))
    
    cash = INITIAL_CASH
    equity = INITIAL_CASH
    peak_equity = INITIAL_CASH
    rolling_dd = 0.0
    
    # Regime State
    regime = 'NORMAL' # NORMAL, BAN, RECOVERY
    ban_start_date = None
    recovery_start_date = None
    
    history_signals_count = [] # (date, count) list
    
    all_trades = []
    equity_history = []
    regime_log = []
    
    print(f"Starting X-6c (Regime Recovery) Replay on {len(all_dates)} days...")
    
    for current_date in all_dates:
        # 1. Update DD
        if equity > peak_equity: peak_equity = equity
        rolling_dd = (equity - peak_equity) / peak_equity
        
        # 2. Determine Regime Transition
        prev_regime = regime
        exposure_cap = 1.0
        
        # A. Trigger BAN?
        if regime in ['NORMAL', 'RECOVERY'] and rolling_dd <= REGIME_PARAMS['bear_dd_trigger']:
             if regime != 'BAN': # State Entry
                 regime = 'BAN'
                 ban_start_date = current_date
                 regime_log.append({'date': current_date, 'event': 'BAN_TRIGGERED', 'dd': rolling_dd})
                 
        # B. Trigger UNBAN?
        if regime == 'BAN':
             exposure_cap = 0.0
             # Check minimum duration
             days_banned = 0
             if ban_start_date:
                 # Poor man's business day calc: just index diff?
                 # using simple loop counter is safer if all_dates is linear
                 pass # using logic below
             
             # Calculate Signal Density (need to run signal scan first?)
             # Yes, we need "Potential Signals" even if banned.
             
             # Check Unban Logic
             # Need 5 days min (approx check)
             idx = all_dates.index(current_date)
             ban_idx = all_dates.index(ban_start_date)
             if (idx - ban_idx) >= REGIME_PARAMS['min_ban_days']:
                 # Check last 3 days signals
                 # We need signal counts for current day? No, "Recent 3 days" usually implies T-1, T-2, T-3.
                 # Let's count signals for today later, but check unban at start of day using PREVIOUS days?
                 # "Recent 3 days" -> Let's use T-1 to T-3.
                 recent_counts = [c for d, c in history_signals_count if d < current_date][-REGIME_PARAMS['unban_lookback']:]
                 
                 valid_days = sum(1 for c in recent_counts if c >= REGIME_PARAMS['unban_min_signals_per_day'])
                 if valid_days >= REGIME_PARAMS['unban_min_days_with_signals']:
                     regime = 'RECOVERY'
                     recovery_start_date = current_date
                     regime_log.append({'date': current_date, 'event': 'UNBAN_TRIGGERED', 'dd': rolling_dd, 'valid_days': valid_days})
                     
        # C. Handle RECOVERY
        if regime == 'RECOVERY':
            # Check Staging
            idx = all_dates.index(current_date)
            rec_idx = all_dates.index(recovery_start_date)
            days_in_recovery = idx - rec_idx
            
            if days_in_recovery < REGIME_PARAMS['recovery_stage_days']:
                exposure_cap = REGIME_PARAMS['recovery_cap'] # 20%
            else:
                # Post-Recovery Stage -> Check DD
                # If still in DD > -5%, go to BEAR CAP (50%)
                # If recovered, go to NORMAL (100%)
                # Wait, "unban" implies we are trying to trade. So 50% max.
                if rolling_dd > REGIME_PARAMS['bear_dd_trigger']:
                    regime = 'NORMAL' # Fully recovered
                    exposure_cap = 1.0
                else:
                    exposure_cap = REGIME_PARAMS['bear_cap'] # 50%
        
        # 3. Collect Signals for Today
        # We must run this every day to separate "Potential Count" from "Executed Trades"
        day_signals = []
        full_day_dfs = {}
        
        # Optimization: Only load/proc relevant DFs?
        # We need to scan anyway for signals.
        
        signal_count_today = 0
        
        for sym, full_df in data_cache.items():
            sigs = get_bpc_signals_for_day(sym, full_df, current_date)
            if sigs:
                signal_count_today += 1 # One per symbol
                day_signals.extend(sigs)
            
            # Cache day df for execution
            d_df = full_df[full_df['ts'].dt.date == current_date]
            if not d_df.empty:
                full_day_dfs[sym] = d_df.reset_index(drop=True)
                
        history_signals_count.append((current_date, signal_count_today))
        
        # Sort execution signals
        day_signals.sort(key=lambda x: x['entry_ts'])
        
        # 4. Execute Day (If exposure > 0)
        positions = [] 
        # Need to persist positions across days? Current logic clears EOD.
        # Yes, standard logic is EOD.
        
        booked_syms = set()
        
        if exposure_cap > 0:
            # Reconstruct timeline
            minute_set = set()
            for df in full_day_dfs.values():
                minute_set.update(df['ts'].tolist())
            timeline = sorted(list(minute_set))
            
            sig_idx = 0
            
            for ts in timeline:
                # Exits
                active_pos = []
                for pos in positions:
                    df = full_day_dfs.get(pos['symbol'])
                    if df is None:
                        active_pos.append(pos); continue
                        
                    rows = df[df['ts'] == ts]
                    if rows.empty:
                        active_pos.append(pos); continue
                    row = rows.iloc[0]
                    
                    # Exit Check logic (same as X-6)
                    exit_res = None
                    pos['max_pnl_pct'] = max(pos['max_pnl_pct'], (row['high']/pos['entry_price']-1)*100)
                    
                    if row['low'] <= pos['stop_price']: exit_res = {'reason': 'STOP', 'px': pos['stop_price']}
                    elif row['high'] >= pos['tp_price']: exit_res = {'reason': 'TP', 'px': pos['tp_price']}
                    else:
                        trail_level = None
                        if pos['max_pnl_pct'] >= BPC_PARAMS['trail_trigger_2']: trail_level = pos['max_pnl_pct'] - BPC_PARAMS['trail_stop_2']
                        elif pos['max_pnl_pct'] >= BPC_PARAMS['trail_trigger_1']: trail_level = pos['max_pnl_pct'] - BPC_PARAMS['trail_stop_1']
                        
                        if trail_level is not None:
                            if (row['close']/pos['entry_price']-1)*100 <= trail_level:
                                exit_res = {'reason': 'TRAIL', 'px': row['close']}
                    
                    if exit_res:
                        px = exit_res['px']
                        qty = pos['qty']
                        comm = px*qty*COMMISSION
                        cash += px*qty - comm
                        all_trades.append({'date': current_date, 'ts': ts, 'side': 'SELL', 'symbol': pos['symbol'], 'reason': exit_res['reason'], 'price': px, 'qty': qty})
                    else:
                        active_pos.append(pos)
                positions = active_pos
                
                # Entries
                while sig_idx < len(day_signals) and day_signals[sig_idx]['entry_ts'] <= ts:
                    sig = day_signals[sig_idx]
                    sig_idx += 1
                    if sig['entry_ts'] != ts: continue
                    
                    sym = sig['symbol']
                    if sym in booked_syms: continue
                    
                    # Exposure Check
                    curr_exp = sum(p['qty']*p['entry_price'] for p in positions)
                    total_eq = cash + curr_exp
                    target_limit = total_eq * exposure_cap
                    
                    if len(positions) < MAX_SLOTS and curr_exp < target_limit:
                        size_amt = total_eq / MAX_SLOTS
                        if curr_exp + size_amt > target_limit:
                            size_amt = max(0, target_limit - curr_exp)
                        
                        if size_amt > 10000:
                            qty = int(size_amt / sig['entry_px'])
                            if qty > 0:
                                cost = qty * sig['entry_px']
                                comm = cost * COMMISSION
                                cash -= (cost + comm)
                                pos = {
                                    'symbol': sym, 'entry_price': sig['entry_px'], 'qty': qty,
                                    'stop_price': sig['pb_low']*(1-BPC_PARAMS['stop_buffer']),
                                    'tp_price': sig['entry_px']*(1+BPC_PARAMS['tp_pct']/100),
                                    'max_pnl_pct': 0.0
                                }
                                positions.append(pos)
                                booked_syms.add(sym)
                                all_trades.append({'date': current_date, 'ts': ts, 'side': 'BUY', 'symbol': sym, 'price': sig['entry_px'], 'qty': qty})

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
        equity_history.append({'date': current_date, 'equity': equity, 'regime': regime, 'exposure': exposure_cap, 'signals': signal_count_today})
        
        print(f"{current_date} | Eq: {int(equity)} | Regime: {regime} (Exp {int(exposure_cap*100)}%) | Sig: {signal_count_today}")

    return equity_history, all_trades, regime_log

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_dir", default="GARAM_Data/60day_replay_kst")
    args = parser.parse_args()
    
    cache = load_data_cache(args.data_dir)
    history, trades, logs = run_simulation_x6c(cache)
    
    # Save
    pd.DataFrame(history).to_csv("GARAM_Data/x6c_daily.csv", index=False)
    pd.DataFrame(trades).to_csv("GARAM_Data/x6c_trades.csv", index=False)
    
    final_eq = history[-1]['equity']
    ret = (final_eq / INITIAL_CASH - 1) * 100
    
    print("\n" + "="*50)
    print("PHASE X-6c RESULTS (UNBAN OPTION A)")
    print("="*50)
    print(f"Final Equity: {int(final_eq):,}")
    print(f"Return: {ret:.2f}%")
    print("\nRegime Events:")
    for l in logs:
        print(l)
    print("="*50)

if __name__ == "__main__":
    main()
