"""
Phase X-4b: Precision Forensics (Court-Level Evidence)

Fixes from X-4:
1. One-shot: Only FIRST signal per symbol per day
2. Peak Before: EXCLUDE signal bar
3. Entry Price: NEXT bar OPEN
4. Stop/TP: HIGH/LOW intrabar judgment

Goal: Definitively confirm or reject "breakout = peak entry" hypothesis.
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

def analyze_entries_x4b():
    """Main analysis with all 4 precision fixes"""
    data_cache = load_all_data()
    
    all_trades = []
    
    # Get all unique dates
    all_dates = set()
    for sym, df in data_cache.items():
        df['date'] = df['ts'].dt.date
        all_dates.update(df['date'].unique())
    dates = sorted(list(all_dates))
    
    print(f"Analyzing {len(dates)} days with PRECISION FIXES...")
    
    for date in dates:
        for sym, df in data_cache.items():
            day_df = df[df['date'] == date].copy()
            if len(day_df) < 60: continue
            
            day_df = compute_breakout_signals(day_df)
            signals = day_df[day_df['signal'] == True]
            
            if signals.empty: continue
            
            # FIX 1: ONE-SHOT - Only FIRST signal per symbol per day
            first_signal = signals.iloc[0]
            signal_idx = first_signal.name  # Index in day_df
            signal_close = first_signal['close']
            signal_time = first_signal['ts']
            signal_high = first_signal['high']
            
            # FIX 3: Entry is NEXT BAR OPEN
            entry_idx = signal_idx + 1
            if entry_idx >= len(day_df):
                continue  # No next bar available
            
            entry_row = day_df.iloc[entry_idx]
            entry_price = entry_row['open']
            entry_time = entry_row['ts']
            
            # Get data after entry
            future_df = day_df[day_df.index > entry_idx]
            if len(future_df) < 10: continue
            
            # MFE/MAE in 60 minutes (from entry bar onwards)
            future_60 = future_df.head(60)
            if len(future_60) > 0:
                mfe_60 = (future_60['high'].max() / entry_price - 1) * 100
                mae_60 = (future_60['low'].min() / entry_price - 1) * 100
            else:
                mfe_60 = 0
                mae_60 = 0
            
            # EOD Return
            eod_close = day_df.iloc[-1]['close']
            eod_return = (eod_close / entry_price - 1) * 100
            
            # FIX 2: Peak Before EXCLUDES signal bar
            past_df = day_df[day_df.index < signal_idx].tail(30)
            if len(past_df) < 5:
                peak_before_30 = signal_high  # Fallback
            else:
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
            
            # FIX 4: Stop/TP by HIGH/LOW (intrabar judgment)
            stop_pct = -1.0  # -1% stop
            tp_pct = 5.0     # 5% TP
            
            exit_type = 'EOD'
            exit_price = eod_close
            
            for fidx, frow in future_df.iterrows():
                # Check if LOW hit stop first
                low_pnl = (frow['low'] / entry_price - 1) * 100
                high_pnl = (frow['high'] / entry_price - 1) * 100
                
                if low_pnl <= stop_pct:
                    exit_type = 'STOP'
                    exit_price = entry_price * (1 + stop_pct / 100)
                    break
                elif high_pnl >= tp_pct:
                    exit_type = 'TP'
                    exit_price = entry_price * (1 + tp_pct / 100)
                    break
            
            realized_pnl = (exit_price / entry_price - 1) * 100
            
            all_trades.append({
                'date': date,
                'symbol': sym,
                'signal_time': signal_time,
                'entry_time': entry_time,
                'entry_price': entry_price,
                'exit_price': exit_price,
                'exit_type': exit_type,
                'realized_pnl': realized_pnl,
                'mfe_60': mfe_60,
                'mae_60': mae_60,
                'eod_return': eod_return,
                'entry_vs_peak': entry_vs_peak,
                'entry_to_peak_after': entry_to_peak_after,
            })
    
    trades_df = pd.DataFrame(all_trades)
    print(f"\nTotal ACTUAL trades analyzed: {len(trades_df)}")
    
    return trades_df

def generate_report_x4b(trades_df):
    """Generate the 4 forensic tables with precision fixes"""
    
    print("\n" + "="*70)
    print("PHASE X-4b: PRECISION FORENSICS (COURT-LEVEL EVIDENCE)")
    print("="*70)
    print(f"Total Trades: {len(trades_df)} (One-Shot: 1 per symbol per day)")
    
    print("\n" + "="*70)
    print("TABLE 1: ENTRY SLIPPAGE MAP (MFE/MAE) - Entry = Next Bar Open")
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
    
    stop_count = len(trades_df[trades_df['exit_type'] == 'STOP'])
    tp_count = len(trades_df[trades_df['exit_type'] == 'TP'])
    eod_count = len(trades_df[trades_df['exit_type'] == 'EOD'])
    
    stop_rate = stop_count / len(trades_df) * 100
    tp_rate = tp_count / len(trades_df) * 100
    eod_rate = eod_count / len(trades_df) * 100
    
    print(f"\nStop (-1%) hit first: {stop_rate:.1f}% ({stop_count} trades)")
    print(f"TP (+5%) hit first:   {tp_rate:.1f}% ({tp_count} trades)")
    print(f"Neither (EOD exit):   {eod_rate:.1f}% ({eod_count} trades)")
    
    print("\n" + "="*70)
    print("TABLE 2: PEAK PROXIMITY SCORE - Peak EXCLUDES Signal Bar")
    print("="*70)
    
    print("\nEntry vs Peak (Before Entry, EXCLUDING signal bar):")
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
    if len(near_peak) > 0:
        print(f"  Avg Realized PnL: {near_peak['realized_pnl'].mean():.2f}%")
    print(f"Below Peak (<-0.5%): {len(below_peak)} trades ({len(below_peak)/len(trades_df)*100:.1f}%)")
    if len(below_peak) > 0:
        print(f"  Avg Realized PnL: {below_peak['realized_pnl'].mean():.2f}%")
    
    print("\n" + "="*70)
    print("TABLE 3: LOSS ATTRIBUTION - Realized PnL by Exit Type")
    print("="*70)
    
    for exit_type in ['STOP', 'TP', 'EOD']:
        subset = trades_df[trades_df['exit_type'] == exit_type]
        if len(subset) > 0:
            avg_pnl = subset['realized_pnl'].mean()
            total_pnl = subset['realized_pnl'].sum()
            print(f"  {exit_type}: {len(subset)} trades, Avg PnL: {avg_pnl:.2f}%, Total: {total_pnl:.1f}%")
    
    total_pnl = trades_df['realized_pnl'].sum()
    avg_pnl = trades_df['realized_pnl'].mean()
    win_rate = (trades_df['realized_pnl'] > 0).mean() * 100
    
    print(f"\nOVERALL:")
    print(f"  Total PnL: {total_pnl:.1f}%")
    print(f"  Avg PnL:   {avg_pnl:.2f}%")
    print(f"  Win Rate:  {win_rate:.1f}%")
    
    print("\n" + "="*70)
    print("TABLE 4: REGIME CONDITIONING (by Entry Hour)")
    print("="*70)
    
    trades_df['hour'] = pd.to_datetime(trades_df['entry_time']).dt.hour
    
    for hour in sorted(trades_df['hour'].unique()):
        subset = trades_df[trades_df['hour'] == hour]
        if len(subset) > 10:
            stop_r = (subset['exit_type'] == 'STOP').mean() * 100
            avg_pnl = subset['realized_pnl'].mean()
            print(f"  Hour {hour}:00 - {len(subset)} trades, Avg PnL: {avg_pnl:+.2f}%, Stop Rate: {stop_r:.1f}%")
    
    print("\n" + "="*70)
    print("FINAL VERDICT (X-4b)")
    print("="*70)
    
    if stop_rate > tp_rate * 2:
        print(f"✗ STOP hits ({stop_rate:.0f}%) >> TP hits ({tp_rate:.0f}%)")
        print("  → Entry quality is structurally poor")
        verdict = "CONFIRMED"
    else:
        print(f"? STOP ({stop_rate:.0f}%) vs TP ({tp_rate:.0f}%) - not overwhelmingly biased")
        verdict = "INCONCLUSIVE"
    
    if trades_df['entry_vs_peak'].median() >= 0:
        print(f"✗ Median Entry vs Peak = {trades_df['entry_vs_peak'].median():.2f}% (at/above peak)")
        verdict = "CONFIRMED"
    elif trades_df['entry_vs_peak'].median() >= -1.0:
        print(f"? Median Entry vs Peak = {trades_df['entry_vs_peak'].median():.2f}% (near peak)")
    else:
        print(f"✓ Median Entry vs Peak = {trades_df['entry_vs_peak'].median():.2f}% (below peak)")
    
    if avg_pnl < 0:
        print(f"✗ Average PnL = {avg_pnl:.2f}% (negative expectancy)")
    else:
        print(f"✓ Average PnL = {avg_pnl:.2f}% (positive expectancy)")
    
    print(f"\n→ BREAKOUT CONFIRMATION = PEAK ENTRY: **{verdict}**")
    
    print("\n" + "="*70)
    
    # Save to CSV
    trades_df.to_csv("GARAM_Data/phase_x4b_trades.csv", index=False)
    print("Saved detailed trades to GARAM_Data/phase_x4b_trades.csv")
    
    return verdict

def main():
    print("="*70)
    print("PHASE X-4b: PRECISION FORENSICS")
    print("="*70)
    print("Fixes Applied:")
    print("  1. One-Shot: First signal only per symbol/day")
    print("  2. Peak Before: Excludes signal bar")
    print("  3. Entry Price: Next bar OPEN")
    print("  4. Stop/TP: HIGH/LOW intrabar judgment")
    print("="*70)
    
    trades_df = analyze_entries_x4b()
    
    if len(trades_df) > 0:
        verdict = generate_report_x4b(trades_df)
        return verdict
    else:
        print("No trades found!")
        return "ERROR"

if __name__ == "__main__":
    main()
