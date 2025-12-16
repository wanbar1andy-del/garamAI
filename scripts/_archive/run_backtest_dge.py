"""
Run Backtest for DGE ORB Aggressive Strategy
"""

import sys
from pathlib import Path
import pandas as pd
import json
from datetime import datetime, timedelta

# Add project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import PATHS
from sim.test_account import TestAccount
from strategies.kr_intraday.dge_orb_aggressive import DGEOrbAggressiveStrategy
from strategies.kr_intraday.backtest_runner import IntradayBacktestRunner

def load_daily_data(symbol: str) -> pd.DataFrame:
    """Load daily data for trend calculation"""
    # Try various patterns
    patterns = [
        PATHS.DAILY_DIR / f"{symbol}_daily.csv",
        PATHS.DAILY_DIR / f"{symbol}.csv",
        PATHS.HISTORY_DIR / f"{symbol}_daily.csv",
        PATHS.HISTORY_DIR / "daily" / f"{symbol}.csv"
    ]
    
    # Add glob search in history
    if PATHS.HISTORY_DIR.exists():
        for p in PATHS.HISTORY_DIR.glob(f"KR_{symbol}_*_daily_*.csv"):
            patterns.append(p)
    
    print(f"Searching for daily data in: {PATHS.DAILY_DIR}")
    if PATHS.DAILY_DIR.exists():
        print(f"Files in {PATHS.DAILY_DIR}:")
        for p in list(PATHS.DAILY_DIR.glob("*"))[:5]:
            print(f" - {p.name}")

    print(f"Searching for daily data in: {PATHS.HISTORY_DIR}")
    if PATHS.HISTORY_DIR.exists():
        print(f"Files in {PATHS.HISTORY_DIR}:")
        for p in list(PATHS.HISTORY_DIR.glob("*"))[:5]:
            print(f" - {p.name}")
            
    for path in patterns:
        if path.exists():
            print(f"Loading daily data from {path}")
            df = pd.read_csv(path)
            # ... (rest of loading logic)
            # Standardize columns
            df.columns = [c.lower() for c in df.columns]
            
            # Parse date
            date_col = None
            for col in ['date', 'timestamp', '일자']:
                if col in df.columns:
                    date_col = col
                    break
            
            if date_col:
                df['timestamp'] = pd.to_datetime(df[date_col])
                df.set_index('timestamp', inplace=True)
                df.sort_index(inplace=True)
                return df
                
    print(f"Warning: Daily data not found for {symbol}")
    return None

def main():
    symbol = "005930" # Samsung Electronics
    print(f"Starting Backtest for {symbol}...")
    
    # 1. Load Daily Data
    daily_df = load_daily_data(symbol)
    
    # 2. Configure Strategy
    config = {
        "orb_minutes": 30,
        "orb_buffer": 0.2,
        "fs_thresh_long": 0.3,
        "fs_thresh_short": -0.3,
        "fm_thresh_long": -0.1,
        "fm_thresh_short": 0.0,
        "rr_init": 2.5,
        "trail_start_R": 1.5,
        "time_stop_bars": 16,
        "risk_per_trade": 0.015
    }
    
    account = TestAccount(base_capital=100_000_000)
    strategy = DGEOrbAggressiveStrategy(account, config, daily_df)
    
    # 3. Run Backtest
    runner = IntradayBacktestRunner(strategy, symbol)
    
    # Recent 1 Year (365 days)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    
    print(f"Period: {start_date.date()} ~ {end_date.date()}")
    
    results = runner.run(
        start_date=start_date.strftime("%Y-%m-%d"),
        end_date=end_date.strftime("%Y-%m-%d")
    )
    
    if "error" in results:
        print(f"Backtest Failed: {results['error']}")
    else:
        print("\nBacktest Complete!")
        print("-" * 50)
        metrics = results['metrics']
        print(f"Total Return: {metrics['total_return_pct']:.2f}%")
        print(f"Total PnL: {metrics['total_pnl']:,.0f} KRW")
        print(f"Max Drawdown: {metrics['max_drawdown_pct']:.2f}%")
        print(f"Trades: {metrics['num_trades']}")
        print(f"Final Equity: {metrics['final_equity']:,.0f} KRW")
        print("-" * 50)
        
        # Save detailed results
        runner.save_results(results)

if __name__ == "__main__":
    main()
