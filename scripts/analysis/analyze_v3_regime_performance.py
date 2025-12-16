"""
Analyze v0.3 Performance by Regime
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config import PATHS
from strategies.kr_intraday.dge_orb_v0_3 import DGEOrbStrategyV3
from strategies.kr_intraday.backtest_runner import IntradayBacktestRunner
from sim.test_account import TestAccount

def analyze_v3_regime():
    # Re-run v0.3 to get trade history (since we didn't save it in comparison script)
    # Or modify comparison script to save it. 
    # Let's re-run quickly for a few symbols or just trust the logic?
    # Better: Re-run for all to get accurate data.
    
    universe = [
        "000270", "000660", "005380", "005490", "005930", 
        "006400", "035420", "051910", "068270", "105560"
    ]
    
    # Load Daily
    daily_data = {}
    for symbol in universe:
        files = list(PATHS.HISTORY_DIR.glob(f"KR_{symbol}_*_daily_20y.csv"))
        if files:
            df = pd.read_csv(files[0])
            df.columns = [c.lower() for c in df.columns]
            date_col = next((c for c in df.columns if c in ['date', 'timestamp', '일자']), None)
            df['timestamp'] = pd.to_datetime(df[date_col])
            df.set_index('timestamp', inplace=True)
            df.sort_index(inplace=True)
            
            df['tr'] = np.maximum(df['high'] - df['low'], 
                                  np.maximum(abs(df['high'] - df['close'].shift(1)), 
                                             abs(df['low'] - df['close'].shift(1))))
            df['atr_20'] = df['tr'].rolling(20).mean()
            daily_data[symbol] = df

    base_config = {
        'initial_capital': 100_000_000,
        'risk_per_trade': 0.015,
        'orb_minutes': 30,
        'fs_k': 3,
        'fs_N': 120,
        'start_date': '2025-09-01',
        'end_date': '2025-11-30',
        'mode': 'ATTACK'
    }
    
    all_trades = []
    
    print("Running v0.3 for detailed analysis...")
    for symbol in universe:
        if symbol not in daily_data: continue
        
        account = TestAccount(base_config['initial_capital'])
        strategy = DGEOrbStrategyV3(account, base_config, daily_df=daily_data[symbol])
        runner = IntradayBacktestRunner(strategy, symbol)
        runner.run(start_date=base_config['start_date'], end_date=base_config['end_date'])
        
        # Extract trades with regime info
        # We need to reconstruct regime since TestAccount doesn't store it by default?
        # Wait, DGEOrbStrategyV3 stores params in position_params, but that's lost after close.
        # But we can re-calculate regime from entry time.
        
        for t in account.trade_history:
            entry_time = t['entry_time']
            regime = strategy.regime_classifier.get_regime(strategy.daily_df, entry_time)
            t['regime'] = regime
            t['symbol'] = symbol
            all_trades.append(t)
            
    # Analyze
    df = pd.DataFrame(all_trades)
    if df.empty:
        print("No trades found.")
        return

    # Group by Regime
    summary = df.groupby('regime').agg({
        'pnl': ['count', 'sum', 'mean'],
        'realized_R': 'mean'
    })
    summary.columns = ['count', 'total_pnl', 'avg_pnl', 'avg_r']
    summary['win_rate'] = df.groupby('regime')['pnl'].apply(lambda x: (x > 0).sum() / len(x))
    
    print("\nv0.3 Performance by Regime:")
    print(summary.to_markdown())
    
    summary.to_csv(PATHS.EXPERIMENTS_DIR / "analysis" / "v0.3_regime_performance.csv")

if __name__ == "__main__":
    analyze_v3_regime()
