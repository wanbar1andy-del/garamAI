"""
A/B Backtest Comparison: DGE_ORB v0.1 vs v0.2
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Add project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import PATHS
from sim.test_account import TestAccount
from strategies.kr_intraday.backtest_runner import IntradayBacktestRunner
from strategies.kr_intraday.dge_orb_aggressive import DGEOrbAggressiveStrategy
from strategies.kr_intraday.dge_orb_v0_2 import DGEOrbStrategyV2

def run_comparison():
    # 1. Setup
    universe = [
        "000270", "000660", "005380", "005490", "005930", 
        "006400", "035420", "051910", "068270", "105560"
    ]
    
    # Load Daily Data for Universe (for fm signal)
    daily_data = {}
    print("Loading daily data...")
    for symbol in universe:
        # Try history first
        path = PATHS.HISTORY_DIR / f"KR_{symbol}_*_daily_20y.csv"
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
                daily_data[symbol] = df
                print(f"Loaded daily for {symbol}")
        else:
            print(f"Warning: No daily data for {symbol}")

    # Common Config
    base_config = {
        'initial_capital': 100_000_000,
        'risk_per_trade': 0.015,
        'max_daily_loss': 0.05,
        'start_date': '2025-09-01',
        'end_date': '2025-11-30'
    }

    # v0.1 Config
    config_v1 = base_config.copy()
    config_v1.update({
        'orb_minutes': 30,
        'fm_thresh': -0.1, # v0.1 logic
        # ... other v0.1 params
    })

    # v0.2 Config
    config_v2 = base_config.copy()
    config_v2.update({
        'orb_minutes': 30,
        'fs_orb_thresh': 0.5,
        'fs_fast_thresh': 0.8,
        'fm_thresh': 0.0,
        'fs_k': 3,
        'fs_N': 120
    })

    # Run Backtests
    results = []
    
    for version, strategy_cls, config in [
        ("v0.1", DGEOrbAggressiveStrategy, config_v1),
        ("v0.2", DGEOrbStrategyV2, config_v2)
    ]:
        print(f"\nRunning {version} Backtest...")
        
        # Aggregate results across universe
        total_trades = 0
        total_pnl = 0
        equity_curve = pd.Series(dtype=float)
        trade_list = []
        
        # Run per symbol (since runner is single symbol for now, we iterate)
        # Ideally we want portfolio simulation, but for A/B stats, sum of single symbol runs is okay approximation for "opportunity count" and "avg R".
        # For Portfolio Equity/DD, we need to merge equity curves.
        
        symbol_curves = []
        
        for symbol in universe:
            if symbol not in daily_data: continue
            
            print(f"  Testing {symbol}...")
            
            # Instantiate components
            account = TestAccount(base_capital=config['initial_capital'])
            strategy = strategy_cls(
                account=account,
                config=config,
                daily_df=daily_data.get(symbol)
            )
            
            runner = IntradayBacktestRunner(
                strategy=strategy,
                symbol=symbol
            )
            
            res = runner.run(
                start_date=config['start_date'],
                end_date=config['end_date']
            )
            
            metrics = res.get('metrics', {})
            if metrics.get('num_trades', 0) > 0:
                total_trades += metrics['num_trades']
                total_pnl += metrics['total_pnl']
                
                # Add symbol to trade history
                for t in strategy.account.trade_history:
                    t['symbol'] = symbol
                    
                trade_list.extend(strategy.account.trade_history)
                
                # Align equity curve to daily
                equity_data = {ep.timestamp: ep.equity for ep in strategy.account.equity_history}
                curve = pd.Series(equity_data)
                if not curve.empty:
                    curve.index = pd.to_datetime(curve.index)
                    # Resample to daily close
                    daily_curve = curve.resample('D').last().fillna(method='ffill')
                    symbol_curves.append(daily_curve)
        
        # Portfolio Stats
        if symbol_curves:
            # Sum PnL changes (assuming separate capital for each? No, let's assume 100m allocated to EACH for stress test sum)
            # Or better: Average return?
            # Let's just sum the PnL to see total "Engine Output"
            
            # Align all curves
            portfolio_df = pd.concat(symbol_curves, axis=1)
            portfolio_df = portfolio_df.fillna(method='ffill').fillna(100_000_000) # Fill start with initial
            
            # Calculate Portfolio Equity (Sum of PnL + Initial Base?)
            # Simplified: Sum of (Equity - Initial) + Initial
            pnl_df = portfolio_df - 100_000_000
            total_equity = pnl_df.sum(axis=1) + 100_000_000
            
            # Metrics
            start_eq = total_equity.iloc[0]
            end_eq = total_equity.iloc[-1]
            ret = (end_eq - start_eq) / start_eq
            mdd = (total_equity / total_equity.cummax() - 1).min()
            
            results.append({
                "Version": version,
                "Return": ret,
                "MDD": mdd,
                "Trades": total_trades,
                "PnL": total_pnl,
                "FinalEquity": end_eq
            })
            
            # Save trade list
            pd.DataFrame(trade_list).to_csv(PATHS.EXPERIMENTS_DIR / f"trades_{version}.csv")
            
    # Print Comparison
    print("\n=== A/B Test Results (Summed across 10 symbols) ===")
    if not results:
        print("No results generated.")
        return
        
    res_df = pd.DataFrame(results)
    res_df['Return'] = res_df['Return'].map('{:.2%}'.format)
    res_df['MDD'] = res_df['MDD'].map('{:.2%}'.format)
    res_df['PnL'] = res_df['PnL'].map('{:,.0f}'.format)
    res_df['FinalEquity'] = res_df['FinalEquity'].map('{:,.0f}'.format)
    print(res_df.to_string(index=False))

if __name__ == "__main__":
    run_comparison()
