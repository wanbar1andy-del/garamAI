"""
Phase X-5: BPC Entry (Breakout → Pullback → Continuation)

State Machine:
1. IDLE -> BREAKOUT_DETECTED (observe only, no entry)
2. BREAKOUT_DETECTED -> PULLBACK_CONFIRMED (wait for dip)
3. PULLBACK_CONFIRMED -> ENTRY (continuation confirmed)

Rules:
- One-shot: 1 entry per symbol per day
- No new breakout before 10:00
- Max wait: 60 bars for pullback
- Pullback: low <= break_high * (1 - 0.012) OR close <= break_high * (1 - 0.010)
- Continuation: close >= break_high * (1 - 0.003)
- Stop: -1%, TP: +5%
- Trailing: +2% -> trail 1%, +3% -> trail 1.2%
"""
import pandas as pd
import numpy as np
import glob
import os
from datetime import datetime, time as dtime
from enum import Enum

class CandidateState(Enum):
    IDLE = 0
    BREAKOUT_DETECTED = 1
    PULLBACK_CONFIRMED = 2
    ENTRY_TRIGGERED = 3
    EXPIRED = 4

def load_all_data():
    data_dir = "GARAM_Data/60day_replay_kst"
    files = glob.glob(os.path.join(data_dir, "*.csv"))
    
    data_cache = {}
    for f in files:
        try:
            df = pd.read_csv(f, parse_dates=['ts'])
            if df.empty: continue
            sym = os.path.basename(f).replace(".csv", "")
            data_cache[sym] = df
        except: pass
    
    print(f"Loaded {len(data_cache)} symbols")
    return data_cache

def analyze_bpc_entries():
    """BPC Entry Analysis with State Machine"""
    data_cache = load_all_data()
    
    # Parameters
    vol_mult = 2.0
    lookback = 30
    vol_ma_period = 20
    pb_low = 0.012       # Pullback threshold (low)
    pb_close = 0.010     # Pullback threshold (close)
    reentry_gap = 0.003  # Continuation threshold
    max_wait_bars = 60   # Max bars to wait for pullback
    no_breakout_before = dtime(10, 0)  # Option A: No new breakout before 10:00
    
    # Stop/TP/Trail
    stop_pct = -1.0
    tp_pct = 5.0
    trail_trigger_1 = 2.0   # Activate trail at +2%
    trail_stop_1 = 1.0
    trail_trigger_2 = 3.0   # Tighten trail at +3%
    trail_stop_2 = 1.2
    
    all_trades = []
    stats = {'breakouts': 0, 'pullbacks': 0, 'entries': 0, 'expired': 0, 'time_filtered': 0}
    
    # Get all unique dates
    all_dates = set()
    for sym, df in data_cache.items():
        df['date'] = df['ts'].dt.date
        all_dates.update(df['date'].unique())
    dates = sorted(list(all_dates))
    
    print(f"Analyzing {len(dates)} days with BPC Entry...")
    
    for date in dates:
        for sym, df in data_cache.items():
            day_df = df[df['date'] == date].copy().reset_index(drop=True)
            if len(day_df) < lookback + vol_ma_period + max_wait_bars:
                continue
            
            # Compute indicators
            day_df['vol_ma'] = day_df['volume'].rolling(vol_ma_period).mean()
            day_df['high_30'] = day_df['high'].rolling(lookback).max()
            
            # State machine for this symbol/day
            state = CandidateState.IDLE
            break_idx = None
            break_high = None
            pb_confirmed = False
            traded_today = False
            
            for idx in range(lookback + vol_ma_period, len(day_df)):
                row = day_df.iloc[idx]
                ts = row['ts']
                ts_time = ts.time()
                
                if traded_today:
                    break  # One-shot
                
                # STATE: IDLE - Look for breakout
                if state == CandidateState.IDLE:
                    # Time filter: No new breakout before 10:00
                    if ts_time < no_breakout_before:
                        continue
                    
                    # Breakout condition
                    prev_vol_ma = day_df.iloc[idx-1]['vol_ma']
                    prev_high_30 = day_df.iloc[idx-1]['high_30']
                    
                    if np.isnan(prev_vol_ma) or prev_vol_ma == 0:
                        continue
                    
                    if row['volume'] > prev_vol_ma * vol_mult and row['close'] >= prev_high_30:
                        # Breakout detected - observe only
                        state = CandidateState.BREAKOUT_DETECTED
                        break_idx = idx
                        break_high = row['high']
                        stats['breakouts'] += 1
                        continue
                
                # STATE: BREAKOUT_DETECTED - Wait for pullback
                elif state == CandidateState.BREAKOUT_DETECTED:
                    # Update break_high if higher high
                    if row['high'] > break_high:
                        break_high = row['high']
                        break_idx = idx  # Reset wait counter
                    
                    # Check expiry
                    if idx - break_idx > max_wait_bars:
                        state = CandidateState.EXPIRED
                        stats['expired'] += 1
                        continue
                    
                    # Check pullback condition
                    pb_by_low = row['low'] <= break_high * (1 - pb_low)
                    pb_by_close = row['close'] <= break_high * (1 - pb_close)
                    
                    if pb_by_low or pb_by_close:
                        state = CandidateState.PULLBACK_CONFIRMED
                        stats['pullbacks'] += 1
                        continue
                
                # STATE: PULLBACK_CONFIRMED - Wait for continuation
                elif state == CandidateState.PULLBACK_CONFIRMED:
                    # Check expiry (extend max_wait from pullback point)
                    if idx - break_idx > max_wait_bars * 2:
                        state = CandidateState.EXPIRED
                        stats['expired'] += 1
                        continue
                    
                    # Check continuation condition
                    if row['close'] >= break_high * (1 - reentry_gap):
                        # ENTRY TRIGGERED - will execute at next bar open
                        state = CandidateState.ENTRY_TRIGGERED
                        stats['entries'] += 1
                        
                        # Entry at next bar open
                        if idx + 1 >= len(day_df):
                            continue
                        
                        entry_row = day_df.iloc[idx + 1]
                        entry_price = entry_row['open']
                        entry_time = entry_row['ts']
                        entry_idx = idx + 1
                        
                        # Simulate trade
                        exit_type = 'EOD'
                        exit_price = day_df.iloc[-1]['close']
                        max_pnl = 0
                        trail_active = False
                        trail_level = None
                        
                        for fidx in range(entry_idx + 1, len(day_df)):
                            frow = day_df.iloc[fidx]
                            high_pnl = (frow['high'] / entry_price - 1) * 100
                            low_pnl = (frow['low'] / entry_price - 1) * 100
                            close_pnl = (frow['close'] / entry_price - 1) * 100
                            
                            # Update max PnL for trailing
                            if high_pnl > max_pnl:
                                max_pnl = high_pnl
                            
                            # Check stop (by low)
                            if low_pnl <= stop_pct:
                                exit_type = 'STOP'
                                exit_price = entry_price * (1 + stop_pct / 100)
                                break
                            
                            # Check TP (by high)
                            if high_pnl >= tp_pct:
                                exit_type = 'TP'
                                exit_price = entry_price * (1 + tp_pct / 100)
                                break
                            
                            # Trailing logic
                            if max_pnl >= trail_trigger_2:
                                trail_level = max_pnl - trail_stop_2
                            elif max_pnl >= trail_trigger_1:
                                trail_level = max_pnl - trail_stop_1
                            
                            if trail_level is not None and close_pnl <= trail_level:
                                exit_type = 'TRAIL'
                                exit_price = entry_price * (1 + trail_level / 100)
                                break
                        
                        realized_pnl = (exit_price / entry_price - 1) * 100
                        
                        all_trades.append({
                            'date': date,
                            'symbol': sym,
                            'entry_time': entry_time,
                            'entry_price': entry_price,
                            'exit_price': exit_price,
                            'exit_type': exit_type,
                            'realized_pnl': realized_pnl,
                            'break_high': break_high,
                        })
                        
                        traded_today = True
                        break
    
    trades_df = pd.DataFrame(all_trades)
    print(f"\nStats: {stats}")
    print(f"Total BPC trades: {len(trades_df)}")
    
    return trades_df, stats

def generate_report(trades_df, stats):
    """Generate comparison report"""
    
    print("\n" + "="*70)
    print("PHASE X-5: BPC ENTRY RESULTS")
    print("="*70)
    print(f"Breakouts Detected: {stats['breakouts']}")
    print(f"Pullbacks Confirmed: {stats['pullbacks']}")
    print(f"Entries Triggered: {stats['entries']}")
    print(f"Expired (no pullback): {stats['expired']}")
    
    if len(trades_df) == 0:
        print("No trades! Check parameters.")
        return
    
    stop_count = len(trades_df[trades_df['exit_type'] == 'STOP'])
    tp_count = len(trades_df[trades_df['exit_type'] == 'TP'])
    trail_count = len(trades_df[trades_df['exit_type'] == 'TRAIL'])
    eod_count = len(trades_df[trades_df['exit_type'] == 'EOD'])
    
    stop_rate = stop_count / len(trades_df) * 100
    tp_rate = tp_count / len(trades_df) * 100
    trail_rate = trail_count / len(trades_df) * 100
    eod_rate = eod_count / len(trades_df) * 100
    
    print(f"\n=== Exit Distribution ===")
    print(f"Stop (-1%):  {stop_rate:.1f}% ({stop_count})")
    print(f"TP (+5%):    {tp_rate:.1f}% ({tp_count})")
    print(f"Trail:       {trail_rate:.1f}% ({trail_count})")
    print(f"EOD:         {eod_rate:.1f}% ({eod_count})")
    
    print(f"\n=== PnL Summary ===")
    total_pnl = trades_df['realized_pnl'].sum()
    avg_pnl = trades_df['realized_pnl'].mean()
    win_rate = (trades_df['realized_pnl'] > 0).mean() * 100
    
    print(f"Total PnL:   {total_pnl:.1f}%")
    print(f"Avg PnL:     {avg_pnl:.2f}%")
    print(f"Win Rate:    {win_rate:.1f}%")
    
    print(f"\n=== By Exit Type ===")
    for exit_type in ['STOP', 'TP', 'TRAIL', 'EOD']:
        subset = trades_df[trades_df['exit_type'] == exit_type]
        if len(subset) > 0:
            print(f"  {exit_type}: Avg PnL {subset['realized_pnl'].mean():.2f}%, Total {subset['realized_pnl'].sum():.1f}%")
    
    # Hour breakdown
    trades_df['hour'] = pd.to_datetime(trades_df['entry_time']).dt.hour
    print(f"\n=== By Entry Hour ===")
    for hour in sorted(trades_df['hour'].unique()):
        subset = trades_df[trades_df['hour'] == hour]
        if len(subset) > 5:
            stop_r = (subset['exit_type'] == 'STOP').mean() * 100
            print(f"  Hour {hour}:00 - {len(subset)} trades, Avg PnL: {subset['realized_pnl'].mean():+.2f}%, Stop Rate: {stop_r:.1f}%")
    
    print("\n" + "="*70)
    print("COMPARISON: X-4b (Breakout) vs X-5 (BPC)")
    print("="*70)
    print(f"{'Metric':<20} {'X-4b (Breakout)':<20} {'X-5 (BPC)':<20}")
    print(f"{'Trades':<20} {'23,271':<20} {len(trades_df):<20}")
    print(f"{'Stop Rate':<20} {'44.8%':<20} {f'{stop_rate:.1f}%':<20}")
    print(f"{'TP Rate':<20} {'3.3%':<20} {f'{tp_rate:.1f}%':<20}")
    print(f"{'Avg PnL':<20} {'+0.03%':<20} {f'{avg_pnl:+.2f}%':<20}")
    print(f"{'Win Rate':<20} {'38.4%':<20} {f'{win_rate:.1f}%':<20}")
    
    # Verdict
    print("\n" + "="*70)
    print("VERDICT")
    print("="*70)
    if stop_rate < 44.8 and avg_pnl > 0.03:
        print("✓ BPC ENTRY IMPROVES PERFORMANCE")
        print(f"  Stop Rate: 44.8% → {stop_rate:.1f}% (Δ{stop_rate-44.8:+.1f}%p)")
        print(f"  Avg PnL:   +0.03% → {avg_pnl:+.2f}% (Δ{avg_pnl-0.03:+.2f}%p)")
    else:
        print("? BPC did not clearly improve, investigate parameters")
    
    # Save
    trades_df.to_csv("GARAM_Data/phase_x5_trades.csv", index=False)
    print("\nSaved to GARAM_Data/phase_x5_trades.csv")

def main():
    print("="*70)
    print("PHASE X-5: BPC ENTRY (Breakout → Pullback → Continuation)")
    print("="*70)
    print("Parameters:")
    print("  - One-Shot: Yes")
    print("  - No breakout before: 10:00")
    print("  - Pullback: -1.2% (low) or -1.0% (close)")
    print("  - Continuation: -0.3% from high")
    print("  - Max wait: 60 bars")
    print("  - Stop: -1%, TP: +5%")
    print("  - Trailing: +2% → 1%, +3% → 1.2%")
    print("="*70)
    
    trades_df, stats = analyze_bpc_entries()
    
    if len(trades_df) > 0:
        generate_report(trades_df, stats)

if __name__ == "__main__":
    main()
