"""
Regime Performance Analysis for DGE Strategy
Analyzes trade performance across different market regimes (Uptrend, Sideways, Downtrend).
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Add project root
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config import PATHS

def analyze_regime():
    # 1. Load Trades
    trades_path = PATHS.EXPERIMENTS_DIR / "trades_v0.2.csv"
    if not trades_path.exists():
        print(f"Error: {trades_path} not found.")
        return

    trades_df = pd.read_csv(trades_path)
    # Rename timestamp to exit_time if needed
    if 'timestamp' in trades_df.columns and 'exit_time' not in trades_df.columns:
        trades_df.rename(columns={'timestamp': 'exit_time'}, inplace=True)
        
    trades_df['entry_time'] = pd.to_datetime(trades_df['entry_time'])
    trades_df['exit_time'] = pd.to_datetime(trades_df['exit_time'])
    
    # Ensure symbol format matches (immediately)
    trades_df['symbol'] = trades_df['symbol'].astype(str).str.zfill(6)
    
    print(f"Loaded {len(trades_df)} trades from v0.2")

    # 2. Load Daily Data & Calculate Regimes
    universe = trades_df['symbol'].unique()
    daily_data = {}
    
    print("Loading daily data and calculating regimes...")
    for symbol in universe:
        # Try history first
        files = list(PATHS.HISTORY_DIR.glob(f"KR_{symbol}_*_daily_20y.csv"))
        if files:
            df = pd.read_csv(files[0])
            # Standardize
            df.columns = [c.lower() for c in df.columns]
            date_col = next((c for c in df.columns if c in ['date', 'timestamp', '일자']), None)
            if date_col:
                df['timestamp'] = pd.to_datetime(df[date_col])
                df.set_index('timestamp', inplace=True)
                df.sort_index(inplace=True)
                
                # Calculate Regime (20-day Return)
                # Ret_20 = (Close / Close_20_ago) - 1
                df['ret_20'] = df['close'].pct_change(20)
                
                # Define Regime
                # UP: > +3%, DOWN: < -3%, SIDEWAYS: else
                conditions = [
                    (df['ret_20'] > 0.03),
                    (df['ret_20'] < -0.03)
                ]
                choices = ['UP', 'DOWN']
                df['regime'] = np.select(conditions, choices, default='SIDEWAYS')
                
                daily_data[symbol] = df
                # print(f"  {symbol}: Loaded {len(df)} bars")
        else:
            print(f"Warning: No daily data for {symbol}")

    # 3. Tag Trades with Regime
    print("Tagging trades with regime...")
    
    def get_trade_regime(row):
        symbol = row['symbol'] # Already padded
        entry_time = row['entry_time']
        entry_date = entry_time.normalize() # Midnight
        
        if symbol not in daily_data:
            return "UNKNOWN"
            
        df = daily_data[symbol]
        
        # Find closest date on or before entry
        # Since daily data is usually 'date', we look for that date
        try:
            # Check if exact date exists
            if entry_date in df.index:
                return df.loc[entry_date, 'regime']
            else:
                # Fallback to previous available date
                idx = df.index.get_indexer([entry_date], method='ffill')
                if idx[0] != -1:
                    return df.iloc[idx[0]]['regime']
                return "UNKNOWN"
        except Exception as e:
            # print(f"Error tagging {symbol} at {entry_date}: {e}")
            return "UNKNOWN"

    trades_df['regime'] = trades_df.apply(get_trade_regime, axis=1)
    
    # 4. Analysis
    print("\nAnalyzing performance by regime...")
    
    # Summary Table
    summary = trades_df.groupby('regime').agg({
        'symbol': 'count',
        'pnl': 'sum',
        'realized_R': 'mean'
    }).rename(columns={'symbol': 'Count', 'pnl': 'Total PnL', 'realized_R': 'Avg R'})
    
    # Win Rate
    win_counts = trades_df[trades_df['pnl'] > 0].groupby('regime')['symbol'].count()
    summary['Win Rate'] = (win_counts / summary['Count']).fillna(0)
    
    print(summary)
    
    # 5. Deep Dive: Sideways/Down Profit
    target_regimes = ['SIDEWAYS', 'DOWN']
    profitable_choppy = trades_df[
        (trades_df['regime'].isin(target_regimes)) & 
        (trades_df['pnl'] > 0)
    ].sort_values('pnl', ascending=False)
    
    # 6. Deep Dive: Uptrend Loss
    losing_uptrend = trades_df[
        (trades_df['regime'] == 'UP') & 
        (trades_df['pnl'] < 0)
    ].sort_values('pnl', ascending=True)
    
    # 7. Save Results
    output_dir = PATHS.EXPERIMENTS_DIR / "analysis"
    output_dir.mkdir(exist_ok=True)
    
    # Save Tagged Trades
    tagged_path = output_dir / "dge_orb_v0_2_regime_trades.csv"
    trades_df.to_csv(tagged_path, index=False)
    print(f"\nSaved tagged trades to {tagged_path}")
    
    # Generate Report
    report_path = PATHS.BASE_DIR / "docs" / "walkthrough_regime_analysis.md"
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("# DGE v0.2 Regime Analysis Report\n\n")
        f.write(f"**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        f.write("**Strategy**: DGE_ORB v0.2 (fs_fast)\n")
        f.write("**Regime Definition**: 20-day Simple Return (UP > 3%, DOWN < -3%)\n\n")
        
        f.write("## 1. Performance by Regime\n")
        f.write(summary.to_markdown())
        f.write("\n\n")
        
        f.write("## 2. Profitable Trades in Sideways/Down Markets\n")
        f.write("Top 10 profitable trades when market was NOT trending up:\n\n")
        cols = ['symbol', 'entry_time', 'regime', 'pnl', 'realized_R', 'exit_reason']
        # Check if exit_reason exists
        if 'exit_reason' not in profitable_choppy.columns:
             cols = ['symbol', 'entry_time', 'regime', 'pnl', 'realized_R']
             
        f.write(profitable_choppy[cols].head(10).to_markdown(index=False))
        f.write("\n\n")
        
        f.write("## 3. Losing Trades in Uptrend Markets\n")
        f.write("Top 10 losing trades when market WAS trending up:\n\n")
        f.write(losing_uptrend[cols].head(10).to_markdown(index=False))
        f.write("\n\n")
        
        f.write("## 4. Key Insights\n")
        f.write("- **Sideways Profitability**: ...\n")
        f.write("- **Uptrend Weakness**: ...\n")
        
    print(f"Saved report to {report_path}")

if __name__ == "__main__":
    analyze_regime()
