import sys
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from config import PATHS
from sim.test_account import TestAccount
from strategies.kr_intraday.dge_hybrid_v1 import DGEHybridStrategyV1

def run_hybrid_backtest():
    print(">>> Running DGE Hybrid Engine v1.0 Backtest...")
    
    # 1. Configuration
    initial_capital = 100_000_000
    start_date = datetime(2025, 9, 26)
    end_date = datetime(2025, 11, 25)
    
    symbols = [
        "005930", "000660", "005380", "005490", "035420", 
        "000270", "051910", "068270", "105560", "006400"
    ]
    
    account = TestAccount(initial_capital)
    config = {
        'fs_params': {'N_ret': 20, 'N_fs': 10},
        'orb_minutes': 30,
        'mode': 'Hybrid'
    }
    
    # 2. Load Data
    data_map = {}
    daily_map = {}
    strategies = {}
    
    print("Loading Data...")
    for symbol in symbols:
        # Intraday
        # Use real data path
        file_path = PATHS.DATA_DIR / "kr/intraday/1m" / f"{symbol}_1m.csv"
        if not file_path.exists():
            print(f"Warning: No intraday data for {symbol} at {file_path}")
            continue
            
        df = pd.read_csv(file_path)
        if 'timestamp' not in df.columns and 'date' in df.columns:
             df.rename(columns={'date': 'timestamp'}, inplace=True)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)
        df.sort_index(inplace=True)
        
        # Filter Date Range
        mask = (df.index >= start_date) & (df.index <= end_date)
        df_slice = df[mask].copy()
        
        if df_slice.empty: continue
        data_map[symbol] = df_slice
        
        # Resample to Daily (Simulated)
        daily_df = df_slice.resample('D').agg({
            'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'
        }).dropna()
        
        # Calculate Indicators for Regime
        daily_df['ma20'] = daily_df['close'].rolling(20).mean()
        daily_df['fm'] = (daily_df['close'] - daily_df['ma20']) / daily_df['ma20']
        daily_df['trend_20d'] = daily_df['close'].pct_change(20)
        
        # ATR Calculation
        high_low = daily_df['high'] - daily_df['low']
        high_close = (daily_df['high'] - daily_df['close'].shift()).abs()
        low_close = (daily_df['low'] - daily_df['close'].shift()).abs()
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        daily_df['atr'] = tr.rolling(14).mean()
        
        # ATR Z-Score (Simple Percentile Proxy)
        # We need a rolling window for percentile, but for simplicity we use rolling max/min normalization
        daily_df['atr_min'] = daily_df['atr'].rolling(60).min()
        daily_df['atr_max'] = daily_df['atr'].rolling(60).max()
        daily_df['atr_z'] = (daily_df['atr'] - daily_df['atr_min']) / (daily_df['atr_max'] - daily_df['atr_min'])
        
        daily_df = daily_df.fillna(0)
        daily_map[symbol] = daily_df
        
        # Init Strategy
        strategies[symbol] = DGEHybridStrategyV1(account, config, daily_df=daily_df)

    # 3. Simulation Loop
    print(f"Simulating {start_date.date()} to {end_date.date()}...")
    
    # Get all unique timestamps
    all_timestamps = sorted(list(set(t for df in data_map.values() for t in df.index)))
    
    regime_log = []
    
    for ts in all_timestamps:
        # Filter Market Hours
        if ts.time() < datetime.strptime("09:00", "%H:%M").time() or \
           ts.time() >= datetime.strptime("15:30", "%H:%M").time():
            continue
            
        for symbol in symbols:
            strategy = strategies.get(symbol)
            if not strategy: continue
            
            if symbol in data_map and ts in data_map[symbol].index:
                bar = data_map[symbol].loc[ts]
                
                # Update Positions
                for pos in list(strategy.positions):
                    action = strategy.on_position_update(pos, bar)
                    if action:
                        strategy.close_position(pos, action.price, ts, action.reason)
                
                # Check Entry & Regime
                strategy.on_bar(bar, ts)
                
                # Log Regime Switch (Sample)
                if ts.minute == 0 and ts.second == 0 and symbol == symbols[0]: # Hourly log for first symbol
                    regime_log.append({
                        'timestamp': ts,
                        'symbol': symbol,
                        'regime': strategy.current_regime,
                        'module': strategy.current_module,
                        'intensity': strategy.current_intensity
                    })

    # 4. Results
    final_equity = account.base_capital + account.pnl_balance
    total_return = (final_equity - initial_capital) / initial_capital * 100
    
    print("\n" + "="*50)
    print(">>> Hybrid Engine Simulation Results")
    print("="*50)
    print(f"Initial Capital : {initial_capital:,.0f} KRW")
    print(f"Final Equity    : {final_equity:,.0f} KRW")
    print(f"Net Profit      : {account.pnl_balance:,.0f} KRW")
    print(f"Total Return    : {total_return:.2f}%")
    print(f"Total Trades    : {len(account.trade_history)}")
    
    if account.trade_history:
        wins = [t for t in account.trade_history if t['pnl'] > 0]
        win_rate = len(wins) / len(account.trade_history) * 100
        print(f"Win Rate        : {win_rate:.2f}%")
    
    print("\n[Regime Log Sample (Hourly)]")
    for log in regime_log[::10]: # Print every 10th log
        print(f"[{log['timestamp']}] {log['symbol']} -> {log['regime']} ({log['module']}) Int: {log['intensity']}")

if __name__ == "__main__":
    run_hybrid_backtest()
