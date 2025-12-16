"""
Comparison Backtest: v0.2 vs v0.3 (Attack Engine)
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np

# Add project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import PATHS
from strategies.kr_intraday.backtest_runner import IntradayBacktestRunner
from strategies.kr_intraday.dge_orb_v0_2 import DGEOrbStrategyV2
from strategies.kr_intraday.dge_orb_v0_3 import DGEOrbStrategyV3
from sim.test_account import TestAccount

def run_comparison():
    # Universe (same as before)
    universe = [
        "000270", "000660", "005380", "005490", "005930", 
        "006400", "035420", "051910", "068270", "105560"
    ]
    
    # Load Daily Data (needed for both)
    daily_data = {}
    print("Loading daily data...")
    for symbol in universe:
        files = list(PATHS.HISTORY_DIR.glob(f"KR_{symbol}_*_daily_20y.csv"))
        if files:
            df = pd.read_csv(files[0])
            df.columns = [c.lower() for c in df.columns]
            date_col = next((c for c in df.columns if c in ['date', 'timestamp', '일자']), None)
            df['timestamp'] = pd.to_datetime(df[date_col])
            df.set_index('timestamp', inplace=True)
            df.sort_index(inplace=True)
            
            # Calc ATR for v0.3
            df['tr'] = np.maximum(df['high'] - df['low'], 
                                  np.maximum(abs(df['high'] - df['close'].shift(1)), 
                                             abs(df['low'] - df['close'].shift(1))))
            df['atr_20'] = df['tr'].rolling(20).mean()
            
            daily_data[symbol] = df

    # Config
    base_config = {
        'initial_capital': 100_000_000,
        'risk_per_trade': 0.015,
        'orb_minutes': 30,
        'fs_k': 3,
        'fs_N': 120,
        'start_date': '2025-09-01',
        'end_date': '2025-11-30'
    }
    
    results = []
    
    for version, strategy_cls in [("v0.2", DGEOrbStrategyV2), ("v0.3", DGEOrbStrategyV3)]:
        print(f"\nRunning {version}...")
        
        total_pnl = 0
        total_trades = 0
        wins = 0
        
        for symbol in universe:
            if symbol not in daily_data: continue
            
            account = TestAccount(base_config['initial_capital'])
            strategy = strategy_cls(account, base_config, daily_df=daily_data[symbol])
            runner = IntradayBacktestRunner(strategy, symbol)
            
            res = runner.run(start_date=base_config['start_date'], end_date=base_config['end_date'])
            
            if 'metrics' in res:
                m = res['metrics']
                total_pnl += m.get('total_pnl', 0)
                total_trades += m.get('num_trades', 0)
                # Need win count from account history
                wins += len([t for t in account.trade_history if t['pnl'] > 0])
                
        win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
        avg_pnl = (total_pnl / total_trades) if total_trades > 0 else 0
        
        results.append({
            "Version": version,
            "Total PnL": total_pnl,
            "Trades": total_trades,
            "Win Rate": win_rate,
            "Avg PnL": avg_pnl
        })
        
    # Report
    df_res = pd.DataFrame(results)
    print("\nComparison Results:")
    print(df_res.to_markdown(index=False))
    
    # Save
    df_res.to_csv(PATHS.EXPERIMENTS_DIR / "analysis" / "v0.2_vs_v0.3_comparison.csv", index=False)

if __name__ == "__main__":
    run_comparison()
