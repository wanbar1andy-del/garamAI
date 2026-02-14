
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Setup
PROJECT_ROOT = Path("C:/garam/garam")
DATA_DIR = PROJECT_ROOT / "GARAM_Data/60day_replay_kst"
TRADE_LOG = PROJECT_ROOT / "logs/phase4_sweep/trades_PYRAMID_0.7_AESTHETIC_INTELLIGENT_PM0.8_I40_T3-7.csv"

def analyze_losses():
    print("OSS Post-Mortem: Analyzing Casualties...")
    
    if not TRADE_LOG.exists():
        print(f"[X] Log not found: {TRADE_LOG}")
        return

    trades = pd.read_csv(TRADE_LOG)
    trades['date'] = pd.to_datetime(trades['date'])
    
    # 1. Identify Losers
    # Losers are SELLs with negative PnL? 
    # The current log stores 'pnl' on SELL rows.
    closed_trades = trades[trades['side'] == 'SELL'].copy()
    closed_trades['result'] = np.where(closed_trades['pnl'] > 0, 'WIN', 'LOSS')
    
    print(f"Stats: {len(closed_trades)} Closed Trades.")
    print(closed_trades['result'].value_counts())
    
    if closed_trades.empty:
        return

    # 2. Market Context (Vol Accel) at Entry
    # We need to find the ENTRY date for each exit.
    # This is tricky without a trade_id. We assume FIFO or map by ticker.
    # For simulation, we can reconstruct roughly.
    
    # Load Universe for Market Breadth Calculation
    print("loading market data for context...")
    market_vol = {}
    universe = {}
    
    files = list(DATA_DIR.glob("*.csv"))
    # Load a few random files to get market index?
    # Better: Load ALL to get breadth. (Slow but accurate).
    # Optimization: Just load 50 random files to approx market vol.
    
    sample_files = files[:50]
    dates = None
    pcts = pd.DataFrame()
    
    for f in sample_files:
        if 'K' in f.name: continue
        try:
             df = pd.read_csv(f)
             # Std col names
             cols = {c.lower(): c for c in df.columns}
             date_col = next((v for k,v in cols.items() if 'date' in k), None)
             close_col = next((v for k,v in cols.items() if 'close' in k), None)
             
             if date_col and close_col:
                 df[date_col] = pd.to_datetime(df[date_col])
                 df.set_index(date_col, inplace=True)
                 res = df[close_col].resample('1D').last().pct_change()
                 pcts[f.stem] = res
        except:
            pass
            
    # Calculate Market Volatility (Mean Absolute Deviation of Returns)
    market_vol_daily = pcts.abs().mean(axis=1)
    
    # Vol Accel = Current Vol / 20d MA Vol
    vol_ma = market_vol_daily.rolling(20).mean()
    vol_accel = (market_vol_daily / vol_ma).fillna(1.0)
    
    # Map back to trades
    # We need ENTRY date.
    # For each SELL, find the most recent BUY for that ticker before the sell date.
    
    entry_vols = []
    
    for idx, row in closed_trades.iterrows():
        # Find BUY
        # Find BUY
        ticker = row['ticker']
        
        # Look at trades df
        buys = trades[(trades['ticker'] == ticker) & (trades['side'] == 'BUY') & (trades['date'] < row['date'])]
        if not buys.empty:
            entry_date = buys.iloc[-1]['date']
            
            # Get Vol Accel
            if entry_date in vol_accel.index:
                va = vol_accel.loc[entry_date]
            else:
                va = 1.0
                
            entry_vols.append({
                'ticker': ticker,
                'result': row['result'],
                'pnl': row['pnl'],
                'entry_date': entry_date,
                'vol_accel': va
            })
            
    df_analysis = pd.DataFrame(entry_vols)
    
    if df_analysis.empty:
        print("Could not map entries.")
        return
        
    print("\n[Analysis Result]")
    print(df_analysis.groupby('result')['vol_accel'].describe())
    
    # Hypothesis Check & Pattern Generation
    loss_vol = df_analysis[df_analysis['result']=='LOSS']['vol_accel'].mean()
    win_vol = df_analysis[df_analysis['result']=='WIN']['vol_accel'].mean()
    
    print(f"\nAvg Vol_Accel when ENTERING Losers: {loss_vol:.2f}")
    print(f"Avg Vol_Accel when ENTERING Winners: {win_vol:.2f}")
    
    # Save Failure Patterns
    # If Loss Vol is significantly higher than Win Vol, we create a penalty rule.
    patterns = []
    
    if loss_vol > win_vol * 1.1: # 10% tolerance
        print("[OK] Hypothesis Proven: High Volatility kills Heroes.")
        threshold = win_vol * 1.2 # Set threshold slightly above Winner average
        patterns.append({
            "condition": "vol_accel_high",
            "threshold": threshold,
            "penalty_score": 10.0,
            "confidence": 0.8,
            "desc": f"VolAccel > {threshold:.2f} (LossAvg: {loss_vol:.2f})"
        })
    else:
        print("[?] Hypothesis Unproven: Volatility might not be the main killer.")
        # We might still want a safety guard for extreme vol
        if loss_vol > 1.5:
             patterns.append({
                "condition": "vol_accel_high",
                "threshold": 1.5,
                "penalty_score": 5.0,
                "confidence": 0.5,
                "desc": "Safety Guard for Extreme Vol > 1.5"
            })

    output_file = PROJECT_ROOT / "config/failure_patterns.json"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    import json
    existing_data = {}
    if output_file.exists():
        try:
            with open(output_file, 'r') as f:
                existing_data = json.load(f)
        except:
            pass
            
    # Merge patterns: If we found new ones, append/update. If none, KEEP existing.
    if not patterns:
        print("[Self-Learning] No new patterns found. Preserving existing knowledge.")
        final_patterns = existing_data.get('patterns', [])
    else:
        # Simple merge: Append new ones to old ones? 
        # Or if we have a robust way to identify duplicates? 
        # For now, let's keep it simple: New + Old.
        old_patterns = existing_data.get('patterns', [])
        final_patterns = old_patterns + patterns
        
    # Preserve other top-level keys like 'penalty_multiplier'
    data = existing_data.copy()
    data["last_updated"] = str(pd.Timestamp.now())
    data["patterns"] = final_patterns
    
    with open(output_file, "w") as f:
        json.dump(data, f, indent=4)
        print(f"[Self-Learning] Saved {len(final_patterns)} failure patterns to {output_file} (Preserved {len(existing_data.keys())} keys)")

if __name__ == "__main__":
    analyze_losses()
