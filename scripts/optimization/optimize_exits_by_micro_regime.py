"""
Regime-Specific Exit Optimization
Goal: Find optimal Time Stop & Target R for each Micro-Regime (Trend x Volatility).
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
from data.loaders.kr_minute_loader import KRMinuteLoader

def optimize_exits():
    print("Starting Regime-Specific Exit Optimization...")
    
    # 1. Load Trades
    trades_path = PATHS.EXPERIMENTS_DIR / "analysis" / "dge_orb_v0_2_regime_trades.csv"
    if not trades_path.exists():
        print(f"Error: {trades_path} not found.")
        return

    trades_df = pd.read_csv(trades_path)
    trades_df['entry_time'] = pd.to_datetime(trades_df['entry_time'])
    trades_df['symbol'] = trades_df['symbol'].astype(str).str.zfill(6)
    
    print(f"Loaded {len(trades_df)} trades.")

    # 2. Load Daily Data & Calculate Micro-Regimes
    print("Calculating Micro-Regimes...")
    daily_data = {}
    universe = trades_df['symbol'].unique()
    
    # Global Volatility Thresholds (to be calculated from all data)
    all_vol_metrics = []
    
    for symbol in universe:
        files = list(PATHS.HISTORY_DIR.glob(f"KR_{symbol}_*_daily_20y.csv"))
        if not files: continue
        
        df = pd.read_csv(files[0])
        df.columns = [c.lower() for c in df.columns]
        date_col = next((c for c in df.columns if c in ['date', 'timestamp', '일자']), None)
        df['timestamp'] = pd.to_datetime(df[date_col])
        df.set_index('timestamp', inplace=True)
        df.sort_index(inplace=True)
        
        # Metrics
        df['ret_20'] = df['close'].pct_change(20)
        
        # ATR 20 (Simple approximation: High-Low / Close)
        # Better: TR = max(H-L, abs(H-Cp), abs(L-Cp))
        df['tr'] = np.maximum(df['high'] - df['low'], 
                              np.maximum(abs(df['high'] - df['close'].shift(1)), 
                                         abs(df['low'] - df['close'].shift(1))))
        df['atr_20'] = df['tr'].rolling(20).mean()
        df['vol_ratio'] = df['atr_20'] / df['close'] # Normalized Volatility
        
        daily_data[symbol] = df
        all_vol_metrics.extend(df['vol_ratio'].dropna().tolist())

    # Define Volatility Thresholds (33%, 66%)
    vol_low_thresh = np.percentile(all_vol_metrics, 33)
    vol_high_thresh = np.percentile(all_vol_metrics, 66)
    print(f"Volatility Thresholds: Low < {vol_low_thresh:.4f}, High > {vol_high_thresh:.4f}")

    # Tag Trades with Micro-Regime
    def get_micro_regime(row):
        symbol = row['symbol']
        entry_date = row['entry_time'].normalize()
        
        if symbol not in daily_data: return "UNKNOWN"
        df = daily_data[symbol]
        
        # Find date
        idx = df.index.get_indexer([entry_date], method='ffill')[0]
        if idx == -1: return "UNKNOWN"
        
        ret_20 = df.iloc[idx]['ret_20']
        vol_ratio = df.iloc[idx]['vol_ratio']
        
        # Trend
        if ret_20 > 0.05: trend = "STRONG_UP"
        elif ret_20 > 0.01: trend = "WEAK_UP"
        elif ret_20 > -0.01: trend = "FLAT"
        elif ret_20 > -0.05: trend = "WEAK_DOWN"
        else: trend = "STRONG_DOWN"
        
        # Volatility
        if vol_ratio < vol_low_thresh: vol = "LOW_VOL"
        elif vol_ratio < vol_high_thresh: vol = "MED_VOL"
        else: vol = "HIGH_VOL"
        
        return f"{trend}_{vol}"

    trades_df['micro_regime'] = trades_df.apply(get_micro_regime, axis=1)
    print("Micro-Regime distribution:")
    print(trades_df['micro_regime'].value_counts())

    # 3. Simulation (Grid Search)
    print("\nRunning Simulation Grid Search...")
    
    # Params
    time_stops = [16, 30, 60, 120, 240] # Minutes
    target_rs = [2.0, 3.0, 5.0, 10.0]
    
    results = [] # List of dicts
    
    loader = KRMinuteLoader()
    
    for symbol in universe:
        # Load Minute Data
        df_min = loader.load(symbol, interval="1")
        if df_min is None or df_min.empty: continue
        if not isinstance(df_min.index, pd.DatetimeIndex):
             df_min.index = pd.to_datetime(df_min.index)
        df_min.sort_index(inplace=True)
        
        symbol_trades = trades_df[trades_df['symbol'] == symbol]
        
        for idx, trade in symbol_trades.iterrows():
            entry_time = trade['entry_time']
            micro_regime = trade['micro_regime']
            
            # Locate entry
            start_loc = df_min.index.get_indexer([entry_time], method='ffill')[0]
            if start_loc == -1: continue
            
            entry_price = df_min.iloc[start_loc]['close']
            
            # Determine direction (heuristic from fs_fast if available, else assume LONG)
            # In v0.2, fs_fast > 0 is LONG. If not available, assume LONG (majority).
            direction = 1
            
            # Determine direction (heuristic from fs_fast if available, else assume LONG)
            direction = 1
            
            # Dynamic Volatility Calculation from Minute Data
            # Use past 60 minutes to estimate volatility (High-Low range)
            # If not enough history, fallback to fixed %
            lookback = 60
            if start_loc >= lookback:
                past_slice = df_min.iloc[start_loc-lookback:start_loc]
                # Estimate hourly volatility -> approximate daily? 
                # Actually, we just need a reasonable unit for R.
                # Let's use Average True Range of minute bars * sqrt(60) or just StdDev * 2
                # Simpler: Average High-Low of last 60 bars * 5 (approx daily range?)
                # Or just use a fixed percentage of price if we want to be safe.
                # Let's use 20-bar Minute ATR * 10 (approx daily)
                
                # Calculate Minute ATR
                highs = past_slice['high'].values
                lows = past_slice['low'].values
                closes = past_slice['close'].values
                tr = np.maximum(highs - lows, np.abs(highs - np.roll(closes, 1))) # Simplified
                min_atr = np.mean(tr[-20:])
                
                # Daily ATR approx = Minute ATR * sqrt(380) approx * 20
                # Let's just use 1.5% of price as baseline, adjusted by recent volatility ratio
                # Baseline 1.5%
                baseline_vol = entry_price * 0.015
                
                # Realized Volatility (StdDev of returns)
                returns = past_slice['close'].pct_change().dropna()
                realized_vol = returns.std() * np.sqrt(380) # Annualized-ish to Daily
                
                # Risk Unit = Entry Price * Realized Daily Vol
                # If realized_vol is nan (flat), use fallback
                if np.isnan(realized_vol) or realized_vol == 0:
                     risk_unit = baseline_vol
                else:
                     risk_unit = entry_price * realized_vol
            else:
                risk_unit = entry_price * 0.015 # Fallback

            # Debug first trade
            if idx == symbol_trades.index[0]:
                print(f"DEBUG Trade {symbol} {entry_time}: Price={entry_price:.2f}, RiskUnit={risk_unit:.2f} ({(risk_unit/entry_price)*100:.2f}%)")

            # Simulation for each param set
            for ts in time_stops:
                # Slice for max duration
                end_loc = min(start_loc + ts, len(df_min))
                path = df_min.iloc[start_loc:end_loc]
                
                if len(path) == 0: continue
                
                # Check Targets
                for tr in target_rs:
                    target_price = entry_price + (risk_unit * tr * direction)
                    stop_price = entry_price - (risk_unit * 1.0 * direction) # Fixed 1R Stop
                    
                    # Check hit
                    if direction == 1:
                        highs = path['high'].values
                        lows = path['low'].values
                        hit_target_indices = np.where(highs >= target_price)[0]
                        hit_stop_indices = np.where(lows <= stop_price)[0]
                    else:
                        highs = path['high'].values
                        lows = path['low'].values
                        hit_target_indices = np.where(lows <= target_price)[0]
                        hit_stop_indices = np.where(highs >= stop_price)[0]
                        
                    first_target = hit_target_indices[0] if len(hit_target_indices) > 0 else 99999
                    first_stop = hit_stop_indices[0] if len(hit_stop_indices) > 0 else 99999
                    
                    exit_r = 0.0
                    outcome = "Time"
                    
                    if first_stop < first_target and first_stop < len(path):
                        exit_r = -1.0
                        outcome = "Stop"
                    elif first_target < first_stop and first_target < len(path):
                        exit_r = tr
                        outcome = "Target"
                    else:
                        # Time Stop
                        exit_price = path.iloc[-1]['close']
                        exit_r = (exit_price - entry_price) / risk_unit * direction
                        outcome = "Time"
                    
                    # Debug specific trade outcome
                    if idx == symbol_trades.index[0] and ts == 240 and tr == 2.0:
                         print(f"  TS={ts}, TR={tr} -> Outcome={outcome}, R={exit_r:.2f}")
                         print(f"  Target={target_price:.2f}, Stop={stop_price:.2f}")
                         print(f"  MaxHigh={path['high'].max():.2f}, MinLow={path['low'].min():.2f}")

                    results.append({
                        'micro_regime': micro_regime,
                        'time_stop': ts,
                        'target_r': tr,
                        'exit_r': exit_r,
                        'outcome': outcome
                    })

    # 4. Aggregation & Analysis
    results_df = pd.DataFrame(results)
    
    # Group by Regime + Params
    summary = results_df.groupby(['micro_regime', 'time_stop', 'target_r']).agg({
        'exit_r': ['mean', 'count'],
        'outcome': lambda x: (x == 'Target').sum() / len(x) # Win Rate (Target Hit) - rough proxy
    })
    summary.columns = ['avg_r', 'count', 'win_rate']
    summary = summary.reset_index()
    
    # Find Best per Regime
    best_attack = summary.loc[summary.groupby('micro_regime')['avg_r'].idxmax()]
    
    # Save Results
    output_dir = PATHS.EXPERIMENTS_DIR / "analysis"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    summary.to_csv(output_dir / "dge_orb_v0_2_exit_grid_results.csv", index=False)
    best_attack.to_csv(output_dir / "dge_orb_v0_2_exit_best_by_regime.csv", index=False)
    
    # Generate Report
    report_path = PATHS.BASE_DIR / "docs" / "deep_dive_mechanics_extended.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("# Regime-Specific Exit Optimization Report\n\n")
        f.write("## 1. Micro-Regime Definitions\n")
        f.write(f"- **Trend**: 20-day Return (Strong > 5%, Weak > 1%, Flat > -1%)\n")
        f.write(f"- **Volatility**: Normalized ATR (Low < {vol_low_thresh:.4f}, High > {vol_high_thresh:.4f})\n\n")
        
        f.write("## 2. Best 'Attack Mode' Parameters (Max Avg R)\n")
        f.write(best_attack.to_markdown(index=False))
        f.write("\n\n")
        
        f.write("## 3. Insights\n")
        f.write("- **Strong Up**: ...\n")
        f.write("- **Sideways**: ...\n")
        
    print(f"Optimization complete. Report saved to {report_path}")

if __name__ == "__main__":
    optimize_exits()
