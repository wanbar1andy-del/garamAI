"""
Phase X-4: Peak-Entry Forensics
Goal: Definitively prove that "breakout confirmation = peak entry" is the structural problem.

Output: 4 Key Tables
1. Entry Slippage Map (MFE/MAE distribution)
2. Peak Proximity Score (How close to peak we buy)
3. Loss Attribution (Where losses come from)
4. Regime Conditioning (Expectancy by market regime)
"""
import pandas as pd
import numpy as np
import glob
import os
from datetime import datetime, timedelta

def load_all_data():
    """Load all 60-day data into memory"""
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

def compute_breakout_signals(df, vol_mult=2.0, lookback=30, vol_ma_period=20):
    """Compute breakout signals for a single symbol's day data"""
    if len(df) < lookback + vol_ma_period:
        return df
    
    df = df.copy().reset_index(drop=True)
    df['vol_ma'] = df['volume'].rolling(vol_ma_period).mean()
    df['high_30'] = df['high'].rolling(lookback).max()
    
    # Signal: vol > 2x MA AND close >= prev 30-high
    df['signal'] = (
        (df['volume'] > df['vol_ma'].shift(1) * vol_mult) & 
        (df['close'] >= df['high_30'].shift(1))
    )
    
    return df

def analyze_entries():
    """Main analysis: Generate all 4 forensic tables"""
    data_cache = load_all_data()
    
    all_trades = []
    
    # Get all unique dates
    all_dates = set()
    for sym, df in data_cache.items():
        df['date'] = df['ts'].dt.date
        all_dates.update(df['date'].unique())
    dates = sorted(list(all_dates))
    
    print(f"Analyzing {len(dates)} days...")
    
    for date in dates:
        for sym, df in data_cache.items():
            day_df = df[df['date'] == date].copy()
            if len(day_df) < 60: continue
            
            day_df = compute_breakout_signals(day_df)
            signals = day_df[day_df['signal'] == True]
            
            for idx, row in signals.iterrows():
                entry_time = row['ts']
                entry_price = row['close']  # We'd buy at next bar, but signal is at this close
                entry_idx = idx
                
                # Get data after entry
                future_df = day_df[day_df.index > entry_idx]
                if len(future_df) < 10: continue
                
                # MFE/MAE in 60 minutes
                future_60 = future_df.head(60)
                if len(future_60) > 0:
                    mfe_60 = (future_60['high'].max() / entry_price - 1) * 100
                    mae_60 = (future_60['low'].min() / entry_price - 1) * 100
                else:
                    mfe_60 = 0
                    mae_60 = 0
                
                # MFE/MAE in 120 minutes
                future_120 = future_df.head(120)
                if len(future_120) > 0:
                    mfe_120 = (future_120['high'].max() / entry_price - 1) * 100
                    mae_120 = (future_120['low'].min() / entry_price - 1) * 100
                else:
                    mfe_120 = mfe_60
                    mae_120 = mae_60
                
                # EOD Return
                eod_close = day_df.iloc[-1]['close']
                eod_return = (eod_close / entry_price - 1) * 100
                
                # Peak Proximity (before entry)
                past_df = day_df[day_df.index <= entry_idx].tail(30)
                peak_before_30 = past_df['high'].max()
                entry_vs_peak = (entry_price / peak_before_30 - 1) * 100
                
                # Peak After (30 min after entry)
                future_30 = future_df.head(30)
                if len(future_30) > 0:
                    peak_after_30 = future_30['high'].max()
                    entry_to_peak_after = (peak_after_30 / entry_price - 1) * 100
                else:
                    peak_after_30 = entry_price
                    entry_to_peak_after = 0
                
                # Stop hit first or TP hit first?
                stop_pct = -1.0  # -1% stop
                tp_pct = 5.0    # 5% TP
                
                stop_hit_first = False
                tp_hit_first = False
                exit_type = 'EOD'
                
                for fidx, frow in future_df.iterrows():
                    pnl = (frow['close'] / entry_price - 1) * 100
                    if pnl <= stop_pct:
                        stop_hit_first = True
                        exit_type = 'STOP'
                        break
                    elif pnl >= tp_pct:
                        tp_hit_first = True
                        exit_type = 'TP'
                        break
                
                all_trades.append({
                    'date': date,
                    'symbol': sym,
                    'entry_time': entry_time,
                    'entry_price': entry_price,
                    'mfe_60': mfe_60,
                    'mae_60': mae_60,
                    'mfe_120': mfe_120,
                    'mae_120': mae_120,
                    'eod_return': eod_return,
                    'entry_vs_peak': entry_vs_peak,
                    'entry_to_peak_after': entry_to_peak_after,
                    'stop_hit_first': stop_hit_first,
                    'tp_hit_first': tp_hit_first,
                    'exit_type': exit_type,
                })
    
    trades_df = pd.DataFrame(all_trades)
    print(f"\nTotal trades analyzed: {len(trades_df)}")
    
    return trades_df

def generate_report(trades_df):
    """Generate the 4 forensic tables"""
    
    print("\n" + "="*70)
    print("TABLE 1: ENTRY SLIPPAGE MAP (MFE/MAE Distribution)")
    print("="*70)
    
    print("\nMFE_60 (Max Favorable Excursion in 60 min):")
    print(f"  Mean:   {trades_df['mfe_60'].mean():.2f}%")
    print(f"  Median: {trades_df['mfe_60'].median():.2f}%")
    print(f"  25th:   {trades_df['mfe_60'].quantile(0.25):.2f}%")
    print(f"  75th:   {trades_df['mfe_60'].quantile(0.75):.2f}%")
    
    print("\nMAE_60 (Max Adverse Excursion in 60 min):")
    print(f"  Mean:   {trades_df['mae_60'].mean():.2f}%")
    print(f"  Median: {trades_df['mae_60'].median():.2f}%")
    print(f"  25th:   {trades_df['mae_60'].quantile(0.25):.2f}%")
    print(f"  75th:   {trades_df['mae_60'].quantile(0.75):.2f}%")
    
    stop_hit_rate = trades_df['stop_hit_first'].mean() * 100
    tp_hit_rate = trades_df['tp_hit_first'].mean() * 100
    
    print(f"\nStop (-1%) hit first: {stop_hit_rate:.1f}%")
    print(f"TP (+5%) hit first:   {tp_hit_rate:.1f}%")
    print(f"Neither (EOD exit):   {100 - stop_hit_rate - tp_hit_rate:.1f}%")
    
    print("\n" + "="*70)
    print("TABLE 2: PEAK PROXIMITY SCORE")
    print("="*70)
    
    print("\nEntry vs Peak (Before Entry, 30 min window):")
    print(f"  Mean:   {trades_df['entry_vs_peak'].mean():.2f}%")
    print(f"  Median: {trades_df['entry_vs_peak'].median():.2f}%")
    print("  (0% = bought exactly at peak, negative = bought below peak)")
    
    print("\nEntry to Peak After (30 min after entry):")
    print(f"  Mean:   {trades_df['entry_to_peak_after'].mean():.2f}%")
    print(f"  Median: {trades_df['entry_to_peak_after'].median():.2f}%")
    print("  (Small = little upside left after entry)")
    
    # Breakdown by peak proximity
    near_peak = trades_df[trades_df['entry_vs_peak'] >= -0.5]
    below_peak = trades_df[trades_df['entry_vs_peak'] < -0.5]
    
    print(f"\nNear Peak (>-0.5%): {len(near_peak)} trades ({len(near_peak)/len(trades_df)*100:.1f}%)")
    print(f"  Avg EOD Return: {near_peak['eod_return'].mean():.2f}%")
    print(f"Below Peak (<-0.5%): {len(below_peak)} trades ({len(below_peak)/len(trades_df)*100:.1f}%)")
    print(f"  Avg EOD Return: {below_peak['eod_return'].mean():.2f}%")
    
    print("\n" + "="*70)
    print("TABLE 3: LOSS ATTRIBUTION")
    print("="*70)
    
    exit_counts = trades_df['exit_type'].value_counts()
    for exit_type, count in exit_counts.items():
        subset = trades_df[trades_df['exit_type'] == exit_type]
        avg_eod = subset['eod_return'].mean()
        print(f"  {exit_type}: {count} trades ({count/len(trades_df)*100:.1f}%), Avg EOD: {avg_eod:.2f}%")
    
    # Loss from stops
    stops = trades_df[trades_df['exit_type'] == 'STOP']
    tps = trades_df[trades_df['exit_type'] == 'TP']
    eod = trades_df[trades_df['exit_type'] == 'EOD']
    
    print(f"\nLoss from STOPs: {len(stops)} trades × avg -1% = ~-{len(stops)*1:.0f}%")
    print(f"Gain from TPs:   {len(tps)} trades × avg +5% = ~+{len(tps)*5:.0f}%")
    print(f"Net from EOD:    {len(eod)} trades × avg {eod['eod_return'].mean():.2f}%")
    
    print("\n" + "="*70)
    print("TABLE 4: REGIME CONDITIONING (by Entry Hour)")
    print("="*70)
    
    trades_df['hour'] = pd.to_datetime(trades_df['entry_time']).dt.hour
    
    for hour in sorted(trades_df['hour'].unique()):
        subset = trades_df[trades_df['hour'] == hour]
        if len(subset) > 10:
            print(f"  Hour {hour}:00 - {len(subset)} trades, Avg EOD: {subset['eod_return'].mean():+.2f}%, Stop Rate: {subset['stop_hit_first'].mean()*100:.1f}%")
    
    print("\n" + "="*70)
    print("FINAL VERDICT")
    print("="*70)
    
    if stop_hit_rate > tp_hit_rate * 1.5:
        print("✗ STOP hits are dominant (>1.5x TP rate)")
        print("  → Entry quality is structurally poor")
        print("  → Breakout confirmation = Peak Entry CONFIRMED")
    elif trades_df['entry_vs_peak'].median() >= -0.5:
        print("✗ Most entries are NEAR PEAK (median >= -0.5%)")
        print("  → Entry quality is structurally poor")
        print("  → Breakout confirmation = Peak Entry CONFIRMED")
    else:
        print("? Results inconclusive, need deeper analysis")
    
    print("\n" + "="*70)
    
    # Save to CSV
    trades_df.to_csv("GARAM_Data/phase_x4_trades.csv", index=False)
    print("Saved detailed trades to GARAM_Data/phase_x4_trades.csv")

def main():
    print("="*70)
    print("PHASE X-4: PEAK-ENTRY FORENSICS")
    print("="*70)
    
    trades_df = analyze_entries()
    
    if len(trades_df) > 0:
        generate_report(trades_df)
    else:
        print("No trades found!")

if __name__ == "__main__":
    main()
