"""
Phase X-5b: BPC Entry Refinement (3-Set Comparison)

Fixes Applied:
1. Morning Ban: Breakout detection time filter
2. Continuation Strengthened: close >= break_high * (1 + reentry_gap)
3. Rebound Confirmation: Higher Low after pullback
4. Break_idx Fix: Don't reset on high update

3 Parameter Sets:
- Conservative: 12:00, +0.3%, Higher Low required
- Default: 11:30, +0.2%, Higher Low required
- Aggressive: 11:00, +0.1%, No Higher Low
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
    HIGHER_LOW_WAIT = 3
    ENTRY_TRIGGERED = 4
    EXPIRED = 5

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
    
    return data_cache

def run_bpc_v2(data_cache, dates, params):
    """BPC Entry with refinements"""
    
    # Parameters
    vol_mult = params.get('vol_mult', 2.0)
    lookback = params.get('lookback', 30)
    vol_ma_period = params.get('vol_ma_period', 20)
    pb_low = params.get('pb_low', 0.012)
    pb_close = params.get('pb_close', 0.010)
    reentry_gap = params.get('reentry_gap', 0.002)  # FIX 2: Positive gap (above break_high)
    max_wait_bars = params.get('max_wait_bars', 60)
    no_breakout_before = params.get('no_breakout_before', dtime(11, 30))  # FIX 1
    require_higher_low = params.get('require_higher_low', True)  # FIX 3
    
    stop_pct = params.get('stop_pct', -1.0)
    tp_pct = params.get('tp_pct', 5.0)
    trail_trigger_1 = params.get('trail_trigger_1', 2.0)
    trail_stop_1 = params.get('trail_stop_1', 1.0)
    trail_trigger_2 = params.get('trail_trigger_2', 3.0)
    trail_stop_2 = params.get('trail_stop_2', 1.2)
    
    all_trades = []
    stats = {'breakouts': 0, 'pullbacks': 0, 'higher_lows': 0, 'entries': 0, 'expired': 0}
    
    for date in dates:
        for sym, df in data_cache.items():
            day_df = df[df['date'] == date].copy().reset_index(drop=True)
            if len(day_df) < lookback + vol_ma_period + max_wait_bars:
                continue
            
            day_df['vol_ma'] = day_df['volume'].rolling(vol_ma_period).mean()
            day_df['high_30'] = day_df['high'].rolling(lookback).max()
            
            state = CandidateState.IDLE
            break_idx = None
            break_idx_original = None  # FIX 4: Keep original for expiry
            break_high = None
            pb_low_price = None
            traded_today = False
            
            for idx in range(lookback + vol_ma_period, len(day_df)):
                row = day_df.iloc[idx]
                ts = row['ts']
                ts_time = ts.time()
                
                if traded_today:
                    break
                
                # STATE: IDLE
                if state == CandidateState.IDLE:
                    # FIX 1: Time filter on BREAKOUT_DETECTED
                    if ts_time < no_breakout_before:
                        continue
                    
                    prev_vol_ma = day_df.iloc[idx-1]['vol_ma']
                    prev_high_30 = day_df.iloc[idx-1]['high_30']
                    
                    if np.isnan(prev_vol_ma) or prev_vol_ma == 0:
                        continue
                    
                    if row['volume'] > prev_vol_ma * vol_mult and row['close'] >= prev_high_30:
                        state = CandidateState.BREAKOUT_DETECTED
                        break_idx = idx
                        break_idx_original = idx  # FIX 4: Remember original
                        break_high = row['high']
                        stats['breakouts'] += 1
                        continue
                
                # STATE: BREAKOUT_DETECTED
                elif state == CandidateState.BREAKOUT_DETECTED:
                    # Update break_high but NOT break_idx_original (FIX 4)
                    if row['high'] > break_high:
                        break_high = row['high']
                        break_idx = idx  # Update for pullback reference
                    
                    # Check expiry based on ORIGINAL breakout idx
                    if idx - break_idx_original > max_wait_bars:
                        state = CandidateState.EXPIRED
                        stats['expired'] += 1
                        continue
                    
                    # Check pullback
                    pb_by_low = row['low'] <= break_high * (1 - pb_low)
                    pb_by_close = row['close'] <= break_high * (1 - pb_close)
                    
                    if pb_by_low or pb_by_close:
                        pb_low_price = row['low']
                        if require_higher_low:
                            state = CandidateState.HIGHER_LOW_WAIT
                        else:
                            state = CandidateState.PULLBACK_CONFIRMED
                        stats['pullbacks'] += 1
                        continue
                
                # STATE: HIGHER_LOW_WAIT (FIX 3)
                elif state == CandidateState.HIGHER_LOW_WAIT:
                    if idx - break_idx_original > max_wait_bars * 1.5:
                        state = CandidateState.EXPIRED
                        stats['expired'] += 1
                        continue
                    
                    # Check for higher low
                    if row['low'] > pb_low_price:
                        state = CandidateState.PULLBACK_CONFIRMED
                        stats['higher_lows'] += 1
                        continue
                    else:
                        # Update pb_low if lower low
                        pb_low_price = min(pb_low_price, row['low'])
                
                # STATE: PULLBACK_CONFIRMED
                elif state == CandidateState.PULLBACK_CONFIRMED:
                    if idx - break_idx_original > max_wait_bars * 2:
                        state = CandidateState.EXPIRED
                        stats['expired'] += 1
                        continue
                    
                    # FIX 2: Continuation = ABOVE break_high
                    if row['close'] >= break_high * (1 + reentry_gap):
                        state = CandidateState.ENTRY_TRIGGERED
                        stats['entries'] += 1
                        
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
                        trail_level = None
                        
                        for fidx in range(entry_idx + 1, len(day_df)):
                            frow = day_df.iloc[fidx]
                            high_pnl = (frow['high'] / entry_price - 1) * 100
                            low_pnl = (frow['low'] / entry_price - 1) * 100
                            close_pnl = (frow['close'] / entry_price - 1) * 100
                            
                            if high_pnl > max_pnl:
                                max_pnl = high_pnl
                            
                            if low_pnl <= stop_pct:
                                exit_type = 'STOP'
                                exit_price = entry_price * (1 + stop_pct / 100)
                                break
                            
                            if high_pnl >= tp_pct:
                                exit_type = 'TP'
                                exit_price = entry_price * (1 + tp_pct / 100)
                                break
                            
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
                            'exit_type': exit_type,
                            'realized_pnl': realized_pnl,
                        })
                        
                        traded_today = True
                        break
    
    return pd.DataFrame(all_trades), stats

def summarize(name, trades_df, stats):
    """Print summary for one parameter set"""
    print(f"\n{'='*60}")
    print(f"{name}")
    print(f"{'='*60}")
    
    if len(trades_df) == 0:
        print("No trades!")
        return None
    
    stop_count = len(trades_df[trades_df['exit_type'] == 'STOP'])
    tp_count = len(trades_df[trades_df['exit_type'] == 'TP'])
    trail_count = len(trades_df[trades_df['exit_type'] == 'TRAIL'])
    eod_count = len(trades_df[trades_df['exit_type'] == 'EOD'])
    
    stop_rate = stop_count / len(trades_df) * 100
    tp_rate = tp_count / len(trades_df) * 100
    avg_pnl = trades_df['realized_pnl'].mean()
    win_rate = (trades_df['realized_pnl'] > 0).mean() * 100
    
    print(f"Stats: {stats}")
    print(f"Trades: {len(trades_df)}")
    print(f"Stop Rate: {stop_rate:.1f}%")
    print(f"TP Rate: {tp_rate:.1f}%")
    print(f"Trail Rate: {trail_count/len(trades_df)*100:.1f}%")
    print(f"Avg PnL: {avg_pnl:+.2f}%")
    print(f"Win Rate: {win_rate:.1f}%")
    
    return {
        'name': name,
        'trades': len(trades_df),
        'stop_rate': stop_rate,
        'tp_rate': tp_rate,
        'avg_pnl': avg_pnl,
        'win_rate': win_rate,
    }

def main():
    print("="*70)
    print("PHASE X-5b: BPC REFINEMENT (3-SET COMPARISON)")
    print("="*70)
    
    data_cache = load_all_data()
    print(f"Loaded {len(data_cache)} symbols")
    
    # Prepare dates
    all_dates = set()
    for sym, df in data_cache.items():
        df['date'] = df['ts'].dt.date
        all_dates.update(df['date'].unique())
    dates = sorted(list(all_dates))
    print(f"Analyzing {len(dates)} days...")
    
    # 3 Parameter Sets
    param_sets = {
        'Conservative': {
            'no_breakout_before': dtime(12, 0),
            'reentry_gap': 0.003,  # +0.3% above break_high
            'require_higher_low': True,
        },
        'Default': {
            'no_breakout_before': dtime(11, 30),
            'reentry_gap': 0.002,  # +0.2% above break_high
            'require_higher_low': True,
        },
        'Aggressive': {
            'no_breakout_before': dtime(11, 0),
            'reentry_gap': 0.001,  # +0.1% above break_high
            'require_higher_low': False,
        },
    }
    
    results = []
    
    for name, params in param_sets.items():
        print(f"\nRunning {name}...")
        trades_df, stats = run_bpc_v2(data_cache, dates, params)
        result = summarize(name, trades_df, stats)
        if result:
            results.append(result)
        
        # Save trades
        trades_df.to_csv(f"GARAM_Data/phase_x5b_{name.lower()}_trades.csv", index=False)
    
    # Comparison Table
    print("\n" + "="*70)
    print("COMPARISON TABLE")
    print("="*70)
    print(f"{'Metric':<15} {'X-4b':<12} {'X-5':<12} {'Conserv':<12} {'Default':<12} {'Aggress':<12}")
    print("-"*70)
    
    x4b = {'trades': 23271, 'stop_rate': 44.8, 'tp_rate': 3.3, 'avg_pnl': 0.03, 'win_rate': 38.4}
    x5 = {'trades': 4843, 'stop_rate': 51.4, 'tp_rate': 2.0, 'avg_pnl': 0.02, 'win_rate': 37.5}
    
    r_cons = results[0] if len(results) > 0 else {}
    r_def = results[1] if len(results) > 1 else {}
    r_agg = results[2] if len(results) > 2 else {}
    
    print(f"{'Trades':<15} {x4b['trades']:<12} {x5['trades']:<12} {r_cons.get('trades', 'N/A'):<12} {r_def.get('trades', 'N/A'):<12} {r_agg.get('trades', 'N/A'):<12}")
    print(f"{'Stop Rate':<15} {x4b['stop_rate']:.1f}%{'':<7} {x5['stop_rate']:.1f}%{'':<7} {r_cons.get('stop_rate', 0):.1f}%{'':<7} {r_def.get('stop_rate', 0):.1f}%{'':<7} {r_agg.get('stop_rate', 0):.1f}%")
    print(f"{'TP Rate':<15} {x4b['tp_rate']:.1f}%{'':<8} {x5['tp_rate']:.1f}%{'':<8} {r_cons.get('tp_rate', 0):.1f}%{'':<8} {r_def.get('tp_rate', 0):.1f}%{'':<8} {r_agg.get('tp_rate', 0):.1f}%")
    print(f"{'Avg PnL':<15} {x4b['avg_pnl']:+.2f}%{'':<6} {x5['avg_pnl']:+.2f}%{'':<6} {r_cons.get('avg_pnl', 0):+.2f}%{'':<6} {r_def.get('avg_pnl', 0):+.2f}%{'':<6} {r_agg.get('avg_pnl', 0):+.2f}%")
    print(f"{'Win Rate':<15} {x4b['win_rate']:.1f}%{'':<7} {x5['win_rate']:.1f}%{'':<7} {r_cons.get('win_rate', 0):.1f}%{'':<7} {r_def.get('win_rate', 0):.1f}%{'':<7} {r_agg.get('win_rate', 0):.1f}%")
    
    print("\n" + "="*70)
    print("VERDICT")
    print("="*70)
    
    best = max(results, key=lambda x: x['avg_pnl']) if results else None
    if best and best['avg_pnl'] > x4b['avg_pnl'] and best['stop_rate'] < x4b['stop_rate']:
        print(f"✓ {best['name']} IMPROVES over X-4b baseline")
        print(f"  Stop Rate: {x4b['stop_rate']:.1f}% → {best['stop_rate']:.1f}%")
        print(f"  Avg PnL: {x4b['avg_pnl']:+.2f}% → {best['avg_pnl']:+.2f}%")
    else:
        print("? No clear winner, further investigation needed")

if __name__ == "__main__":
    main()
