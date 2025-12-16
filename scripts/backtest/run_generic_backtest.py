import sys
from pathlib import Path
import pandas as pd
from datetime import datetime
import argparse

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from config import PATHS
from sim.test_account import TestAccount
from strategies.kr_intraday.dge_hybrid_v1 import DGEHybridStrategyV1
from strategies.kr_intraday.dge_hybrid_v3 import DGEHybridStrategyV3

def run_backtest(strategy_name, playbook_filename, start_date=None, end_date=None, symbol_filter=None):
    print(f">>> Running Backtest: {strategy_name} using {playbook_filename}")
    
    # 1. Setup
    initial_capital = 100_000_000
    account = TestAccount(initial_capital)
    
    # Load Playbook Path
    playbook_path = None
    if playbook_filename:
        playbook_path = PATHS.CONFIG_DIR / playbook_filename
        if not playbook_path.exists():
            print(f"Error: Playbook not found at {playbook_path}")
            return
        
    # Config for Strategy
    config = {
        'fs_params': {'N_ret': 20, 'N_fs': 10},
        'orb_minutes': 30,
        'mode': 'Hybrid',
        'playbook_path': playbook_path # Pass playbook path to strategy
    }
    
    # Output Dir
    results_dir = PATHS.BASE_DIR / f"results/{strategy_name}"
    results_dir.mkdir(parents=True, exist_ok=True)
    
    symbols = [
        "005930", "000660", "005380", "005490", "035420", 
        "000270", "051910", "068270", "105560", "006400"
    ]
    
    if symbol_filter:
        if symbol_filter in symbols:
            symbols = [symbol_filter]
        else:
            print(f"Warning: Symbol {symbol_filter} not in default list. Using only {symbol_filter}.")
            symbols = [symbol_filter]
    
    strategies = {}
    
    # 2. Load Tagged Data & Initialize
    print("Loading Data...")
    for symbol in symbols:
        # Load Tagged CSV
        file_path = PATHS.BASE_DIR / "analysis/regimes" / f"intraday_with_regime_{symbol}.csv"
        if not file_path.exists():
            print(f"Warning: No tagged data for {symbol}")
            continue
            
        df = pd.read_csv(file_path)
        
        # Parse timestamp
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.set_index('timestamp', inplace=True)
        elif 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            
        # Filter Date Range
        if start_date:
            df = df[df.index >= start_date]
        if end_date:
            df = df[df.index <= end_date]
            
        if df.empty:
            print(f"Warning: No data for {symbol} in range")
            continue
            
        # Initialize Strategy
        # We need daily_df for some internal logic? 
        # DGEHybridStrategyV1 uses daily_df for _update_indicators.
        # But here we already have tagged indicators in the dataframe!
        # We should modify DGEHybridStrategyV1 to use indicators from the bar if available, 
        # or we just pass a dummy daily_df and ensure the strategy reads from the bar.
        # DGEHybridStrategyV1.on_bar calls _calculate_market_state.
        # _calculate_market_state uses self.daily_df for trend/atr if not provided.
        # But wait, DGEHybridStrategyV1 logic is:
        # on_bar -> _update_indicators (daily) -> _calculate_market_state -> router.classify
        # If we want to use PRE-TAGGED regime, we should bypass classification or ensure classification yields the same result.
        # Actually, the user wants to use the Tagged Regime.
        # So we should modify DGEHybridStrategyV1 to accept 'regime' from the bar row if present.
        
        # For now, let's assume DGEHybridStrategyV1 will re-calculate.
        # To ensure consistency, we should pass the same daily data logic.
        # But we don't have daily_df easily here (we have 1m with daily cols).
        # We can reconstruct daily_df from 1m or just pass None and hope strategy handles it?
        # DGEHybridStrategyV1 requires daily_df in __init__.
        
        # Let's create a dummy daily_df from the tagged data (resample again).
        daily_df = df.resample('D').last().dropna(how='all') # Only drop if all cols are NaN
        daily_df.index = pd.to_datetime(daily_df.index).normalize()
        if daily_df.index.tz is not None:
            daily_df.index = daily_df.index.tz_localize(None)
            
        # Fill NaNs for short history
        daily_df.fillna({
            'atr_z': 0.5,
            'trend_20d': 0.0,
            'fm': 0.0
        }, inplace=True)
            
        print(f"Debug: {symbol} daily_df shape: {daily_df.shape}")
        if not daily_df.empty:
            print(f"Debug: {symbol} daily_df index sample: {daily_df.index[:3]}")
            print(f"Debug: {symbol} daily_df index dtype: {daily_df.index.dtype}")
        
        if "v3" in strategy_name.lower() and "hybrid" in strategy_name.lower():
            strategy = DGEHybridStrategyV3(account, config, daily_df=daily_df, symbol=symbol)
        elif "sharpened" in strategy_name.lower():
            from strategies.kr_intraday.dge_v3_sharpened import DGEV3Sharpened
            strategy = DGEV3Sharpened(account, config, daily_df=daily_df, symbol=symbol)
        elif "maxprofit" in strategy_name.lower():
            from strategies.kr_intraday.dge_v3_max_profit import DGEV3MaxProfit
            strategy = DGEV3MaxProfit(account, config, daily_df=daily_df, symbol=symbol)
        elif "hybrid_v1_max" in strategy_name.lower():
            from strategies.kr_intraday.dge_hybrid_v1_max import DGEHybridV1Max
            strategy = DGEHybridV1Max(account, config, daily_df=daily_df, symbol=symbol)
        elif "final" in strategy_name.lower():
            from strategies.kr_intraday.dge_final import DGEFinalStrategy
            strategy = DGEFinalStrategy(account, config, daily_df=daily_df, symbol=symbol)
        elif "orb_v3" in strategy_name.lower():
            from strategies.kr_intraday.dge_orb_v0_3 import DGEOrbStrategyV3
            strategy = DGEOrbStrategyV3(account, config, daily_df=daily_df, symbol=symbol)
        else:
            strategy = DGEHybridStrategyV1(account, config, daily_df=daily_df, symbol=symbol)
        # Override router with specific playbook
        # Strategy init creates router with default playbook if not specified in config?
        # DGEHybridStrategyV1.__init__ calls RegimeRouter().
        # We need to pass playbook_path to Strategy so it passes to Router.
        # I need to update DGEHybridStrategyV1 to accept playbook_path in config.
        
        strategies[symbol] = strategy
        strategies[symbol].data = df # Store data for simulation loop
        
    print(f"Initialized {len(strategies)} strategies.")
    
    # 3. Simulation Loop
    # We need to iterate through time.
    # Merge all timestamps
    all_timestamps = sorted(list(set().union(*[s.data.index for s in strategies.values()])))
    
    print(f"Simulating {len(all_timestamps)} bars...")
    
    for i, ts in enumerate(all_timestamps):
        if i % 1000 == 0:
            print(f"Processing bar {i}/{len(all_timestamps)} ({ts})")
            
        for symbol, strategy in strategies.items():
            if ts not in strategy.data.index:
                continue
                
            bar = strategy.data.loc[ts]
            
            # Update Positions
            for pos in list(strategy.positions):
                action = strategy.on_position_update(pos, bar)
                if action:
                    strategy.close_position(pos, action.price, ts, action.reason)
                    
            # Check Entry
            strategy.on_bar(bar, ts)
            
    # 4. Save Results
    print("Saving Results...")
    
    # Save Trades
    trades_list = []
    for trade in account.trade_history:
        trades_list.append({
            'trade_id': trade.get('trade_id', 'UNKNOWN'),
            'symbol': trade.get('symbol', 'UNKNOWN'),
            'entry_time': trade['entry_time'],
            'exit_time': trade['timestamp'],
            'pnl': trade['pnl'],
            'return_r': trade['realized_R'],
            'holding_bars': trade['holding_period'],
            'exit_reason': trade['exit_reason']
        })
        
    trades_df = pd.DataFrame(trades_list)
    trades_df.to_csv(results_dir / "trades.csv", index=False)
    
    # Save Equity Curve
    # TestAccount doesn't track daily equity automatically?
    # We can reconstruct it from trades.
    # Or just save final summary.
    
    print(f"Results saved to {results_dir}")
    print(f"Total PnL: {account.pnl_balance}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--strategy", required=True)
    parser.add_argument("--playbook", required=False, default=None)
    parser.add_argument("--symbol", required=False, default=None)
    args = parser.parse_args()
    
    run_backtest(args.strategy, args.playbook, symbol_filter=args.symbol)
