import sys
from pathlib import Path
import time
from datetime import datetime
import pandas as pd

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from config import PATHS
from broker.real_broker_sim import RealBrokerSim
from sim.test_account import TestAccount
from strategies.kr_intraday.dge_hybrid_v1 import DGEHybridStrategyV1

def run_paper_hybrid():
    print(">>> Starting DGE Hybrid Engine (Paper Trading)...")
    
    # 1. Configuration
    initial_capital = 100_000_000
    symbols = [
        "005930", "000660", "005380", "005490", "035420", 
        "000270", "051910", "068270", "105560", "006400"
    ]
    
    # 2. Initialize Broker & Account
    broker = RealBrokerSim(initial_capital)
    if not broker.connect():
        print("Error: Failed to connect to Broker.")
        return

    account = TestAccount(initial_capital)
    
    # 3. Initialize Strategy
    # We need daily data for regime classification.
    # Broker should provide history.
    
    strategies = {}
    print("Initializing Strategies...")
    
    for symbol in symbols:
        # Get Daily Data (Last 60 days for indicators)
        daily_df = broker.get_price_history(symbol, days=60, timeframe="D")
        if daily_df is None or daily_df.empty:
            print(f"Warning: No daily data for {symbol}")
            continue
            
        # Calculate Daily Indicators (Trend, ATR, FM)
        daily_df['ma20'] = daily_df['close'].rolling(20).mean()
        daily_df['fm'] = (daily_df['close'] - daily_df['ma20']) / daily_df['ma20']
        daily_df['trend_20d'] = daily_df['close'].pct_change(20)
        
        # ATR
        high_low = daily_df['high'] - daily_df['low']
        high_close = (daily_df['high'] - daily_df['close'].shift()).abs()
        low_close = (daily_df['low'] - daily_df['close'].shift()).abs()
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        daily_df['atr'] = tr.rolling(14).mean()
        
        # ATR Z (Simple)
        daily_df['atr_min'] = daily_df['atr'].rolling(60).min()
        daily_df['atr_max'] = daily_df['atr'].rolling(60).max()
        daily_df['atr_z'] = (daily_df['atr'] - daily_df['atr_min']) / (daily_df['atr_max'] - daily_df['atr_min'])
        daily_df = daily_df.fillna(0)
        
        config = {
            'fs_params': {'N_ret': 20, 'N_fs': 10},
            'orb_minutes': 30,
            'mode': 'Hybrid'
        }
        
        strategies[symbol] = DGEHybridStrategyV1(account, config, daily_df=daily_df)
        strategies[symbol].broker = broker # Attach broker for execution
        
    print(f"Initialized {len(strategies)} strategies.")
    print(">>> Waiting for market data...")
    
    # 4. Real-time Loop
    try:
        while True:
            now = datetime.now()
            
            # Market Hours Check (09:00 ~ 15:30)
            # For Paper Trading, we might run anytime if using Mock Data, 
            # but usually we want to respect market hours.
            # Assuming RealBrokerSim handles mock time or we run during day.
            # For now, we just loop.
            
            for symbol, strategy in strategies.items():
                # Get Real-time Bar (1m)
                # Broker should provide latest bar
                bar = broker.get_latest_bar(symbol) # Need to implement or use existing
                if bar is None: continue
                
                ts = bar.name
                
                # Update Positions
                for pos in list(strategy.positions):
                    action = strategy.on_position_update(pos, bar)
                    if action:
                        print(f"[{ts}] {symbol} EXIT: {action.reason} @ {action.price}")
                        strategy.close_position(pos, action.price, ts, action.reason)
                        
                # Check Entry
                strategy.on_bar(bar, ts)
                
                # Log Regime (Periodically)
                if ts.minute % 30 == 0 and ts.second == 0:
                     print(f"[{ts}] {symbol} Regime: {strategy.current_regime} ({strategy.current_module})")
            
            time.sleep(1) # 1 sec loop
            
    except KeyboardInterrupt:
        print("\n>>> Stopping Paper Trading...")
        
if __name__ == "__main__":
    run_paper_hybrid()
