"""
Deep Dive Analysis: DGE v0.2 Mechanics
Goal: Identify structural causes for Uptrend underperformance and Sideways outperformance.
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import tabulate

# Add project root
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config import PATHS
from garam.signals.fs_fast import compute_fs_fast, FsFastParams

from data.loaders.kr_minute_loader import KRMinuteLoader

def analyze_mechanics():
    # 1. Load Trades
    trades_path = PATHS.EXPERIMENTS_DIR / "analysis" / "dge_orb_v0_2_regime_trades.csv"
    if not trades_path.exists():
        print(f"Error: {trades_path} not found.")
        return

    trades_df = pd.read_csv(trades_path)
    trades_df['entry_time'] = pd.to_datetime(trades_df['entry_time'])
    trades_df['exit_time'] = pd.to_datetime(trades_df['exit_time'])
    trades_df['symbol'] = trades_df['symbol'].astype(str).str.zfill(6)
    
    print(f"Loaded {len(trades_df)} trades.")

    # 2. Load Market Data & Feature Engineering
    print("Loading market data and engineering features...")
    
    fs_params = FsFastParams(k_return=3, N_ret=120) # v0.2 defaults
    loader = KRMinuteLoader()
    
    # New columns
    trades_df['fs_fast_entry'] = np.nan
    trades_df['trend_aligned'] = False
    trades_df['potential_pnl_no_timestop'] = np.nan
    trades_df['potential_R_no_timestop'] = np.nan
    
    universe = trades_df['symbol'].unique()
    
    for symbol in universe:
        # Load Minute Data using Loader
        df = loader.load(symbol, interval="1")
        
        if df is None or df.empty:
            print(f"  {symbol}: No data found via KRMinuteLoader")
            continue
            
        # Ensure index is datetime and sorted (Loader does this, but double check)
        if not isinstance(df.index, pd.DatetimeIndex):
             df.index = pd.to_datetime(df.index)
        
        df.sort_index(inplace=True)
        
        # Debug: Check timestamps
        if len(trades_df) > 0 and len(df) > 0:
            t_trade = trades_df['entry_time'].iloc[0]
            t_market = df.index[0]
            
            # Normalize timezones if needed
            if t_trade.tzinfo is None and t_market.tzinfo is not None:
                df.index = df.index.tz_localize(None)
            elif t_trade.tzinfo is not None and t_market.tzinfo is None:
                trades_df['entry_time'] = trades_df['entry_time'].dt.tz_localize(None)
                trades_df['exit_time'] = trades_df['exit_time'].dt.tz_localize(None)

        # Filter for relevant period (plus buffer)
        # Need enough history for fs_fast (N=120)
        # 5 days buffer is approx 5 * 380 = 1900 bars, should be enough.
        start_date = trades_df['entry_time'].min() - timedelta(days=10)
        end_date = trades_df['exit_time'].max() + timedelta(days=5)
        df = df[(df.index >= start_date) & (df.index <= end_date)]
        
        if df.empty: 
            print(f"  {symbol}: Empty dataframe after filtering")
            continue
        
        # Calculate fs_fast
        try:
            fs_series = compute_fs_fast(df, fs_params)
            df['fs_fast'] = fs_series
        except Exception as e:
            print(f"  {symbol}: fs_fast calculation failed: {e}")
            continue
        
        # Calculate Trend (Simple MA 60 - approx 1 hour)
        df['ma60'] = df['close'].rolling(60).mean()
        
        # Process Trades for this symbol
        symbol_trades = trades_df[trades_df['symbol'] == symbol]
        
        for idx, trade in symbol_trades.iterrows():
            entry_time = trade['entry_time']
            
            # 1. fs_fast at entry
            try:
                # Find closest timestamp
                # Use get_indexer with method='ffill' to find the index of the entry time
                loc_idx = df.index.get_indexer([entry_time], method='ffill')[0]
                
                if loc_idx != -1:
                    fs_val = df.iloc[loc_idx]['fs_fast']
                    trades_df.at[idx, 'fs_fast_entry'] = fs_val
                    
                    # Trend Alignment (Price vs MA60)
                    price = df.iloc[loc_idx]['close']
                    ma = df.iloc[loc_idx]['ma60']
                    
                    # Heuristic: fs_fast > 0 implies LONG attempt
                    is_long_signal = fs_val > 0 
                    is_uptrend = price > ma
                    
                    trades_df.at[idx, 'trend_aligned'] = (is_long_signal and is_uptrend) or (not is_long_signal and not is_uptrend)
                    
                    # Debug print for first few trades
                    if idx < 3:
                        print(f"  Debug {symbol} at {entry_time}: fs={fs_val:.2f}, price={price}, ma={ma:.2f}")

            except Exception as e:
                print(f"  Error processing trade {idx}: {e}")
                
            # 2. Ablation: Time Stop Analysis (Only for UP regime)
            if trade['regime'] == 'UP' and 'Time' in str(trade.get('exit_reason', '')):
                try:
                    start_loc = df.index.get_indexer([entry_time], method='ffill')[0]
                    if start_loc != -1:
                        # Get entry price (approx)
                        entry_price = df.iloc[start_loc]['close'] 
                        
                        # Look ahead
                        lookahead = 60
                        future_slice = df.iloc[start_loc:start_loc+lookahead]
                        
                        if len(future_slice) > 0:
                            # Calculate max potential PnL
                            # Assuming LONG for UP regime (mostly)
                            # Use fs_fast_entry to determine direction if available, else assume LONG
                            direction = 1
                            if not np.isnan(trades_df.at[idx, 'fs_fast_entry']):
                                if trades_df.at[idx, 'fs_fast_entry'] < 0: direction = -1
                            
                            if direction == 1: # Long
                                max_price = future_slice['high'].max()
                                potential_pnl = (max_price - entry_price) 
                                trades_df.at[idx, 'potential_pnl_no_timestop'] = potential_pnl
                            else: # Short
                                min_price = future_slice['low'].min()
                                potential_pnl = (entry_price - min_price)
                                trades_df.at[idx, 'potential_pnl_no_timestop'] = potential_pnl
                except Exception as e:
                    print(f"  Ablation error {idx}: {e}")

    # 3. Analysis & Reporting
    report_path = PATHS.BASE_DIR / "docs" / "deep_dive_mechanics.md"
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("# Deep Dive: DGE v0.2 Mechanics Analysis\n\n")
        
        # A. Exit Reason Analysis
        f.write("## 1. Exit Reason by Regime\n")
        if 'exit_reason' in trades_df.columns:
            exit_stats = trades_df.groupby(['regime', 'exit_reason']).agg({
                'pnl': 'count',
                'realized_R': 'mean'
            }).rename(columns={'pnl': 'Count', 'realized_R': 'Avg R'})
            f.write(exit_stats.to_markdown())
            f.write("\n\n")
            
        # B. fs_fast Distribution
        f.write("## 2. fs_fast Entry Distribution\n")
        fs_stats = trades_df.groupby('regime')['fs_fast_entry'].describe()[['mean', 'std', '25%', '50%', '75%']]
        f.write(fs_stats.to_markdown())
        f.write("\n\n")
        
        # C. Trend Alignment
        f.write("## 3. Trend Alignment Win Rate\n")
        trend_stats = trades_df.groupby(['regime', 'trend_aligned']).agg({
            'pnl': 'count',
            'realized_R': 'mean'
        })
        f.write(trend_stats.to_markdown())
        f.write("\n\n")
        
        # D. Time Stop Ablation (UP Regime)
        f.write("## 4. Time Stop Ablation (Uptrend Only)\n")
        up_time_stops = trades_df[
            (trades_df['regime'] == 'UP') & 
            (trades_df['exit_reason'].str.contains('Time', na=False))
        ]
        
        if not up_time_stops.empty:
            avg_actual_pnl = up_time_stops['pnl'].mean()
            # potential_pnl is raw price diff, need to scale? 
            # Just compare sign or relative magnitude if possible.
            # Actually, let's just look at how many would have been profitable.
            improved_count = up_time_stops[up_time_stops['potential_pnl_no_timestop'] > 0].shape[0]
            total_count = up_time_stops.shape[0]
            
            f.write(f"- Total Time Stop Trades in UP: {total_count}\n")
            f.write(f"- Trades with Positive Potential (60 bars): {improved_count} ({improved_count/total_count*100:.1f}%)\n")
            f.write("- **Insight**: If we held longer in Uptrends, would we make money?\n")
        else:
            f.write("No Time Stop trades found in UP regime.\n")
            
        f.write("\n## 5. Conclusion (The Thing)\n")
        f.write("Based on the data:\n")
        f.write("1. **Time Stop Impact**: ...\n")
        f.write("2. **fs_fast Bias**: ...\n")
        
    print(f"Analysis complete. Report saved to {report_path}")

if __name__ == "__main__":
    analyze_mechanics()
