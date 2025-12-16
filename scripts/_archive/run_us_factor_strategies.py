"""
Run US Factor Strategies
Execute backtests for all US factor strategies with TestAccount integration.
"""

import sys
from pathlib import Path
import pandas as pd
import logging
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import PATHS
from sim.test_account import TestAccount
from alpha_lab.us_academic.strategies.momentum_strategy import MomentumStrategy
from alpha_lab.us_academic.strategies.low_vol_strategy import LowVolStrategy
from alpha_lab.us_academic.strategies.multi_factor_strategy import MultiFactorStrategy

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_us_price_data():
    """Load US S&P 500 price data"""
    logger.info("Loading US price data...")
    
    prices_dir = PATHS.US_SP500_ROOT / "prices_daily"
    
    if not prices_dir.exists():
        logger.error(f"Price directory not found: {prices_dir}")
        return None
        
    csv_files = list(prices_dir.glob("*.csv"))
    if not csv_files:
        logger.warning("No CSV files found")
        return None
        
    prices_dict = {}
    
    for file_path in csv_files:
        symbol = file_path.stem
        try:
            df = pd.read_csv(file_path)
            
            # Parse date
            date_col = None
            for col in ['Date', 'date', 'Datetime', 'datetime']:
                if col in df.columns:
                    date_col = col
                    break
            
            if date_col:
                df[date_col] = pd.to_datetime(df[date_col])
                df.set_index(date_col, inplace=True)
                
                # Get close price
                close_col = None
                for col in ['Close', 'close', 'Adj Close', 'adj_close']:
                    if col in df.columns:
                        close_col = col
                        break
                        
                if close_col:
                    prices_dict[symbol] = df[close_col]
        except Exception as e:
            logger.warning(f"Error loading {symbol}: {e}")
            
    if prices_dict:
        price_df = pd.DataFrame(prices_dict)
        price_df.sort_index(inplace=True)
        logger.info(f"Loaded price data for {len(price_df.columns)} symbols")
        logger.info(f"Date range: {price_df.index[0]} to {price_df.index[-1]}")
        return price_df
    else:
        logger.error("Failed to load any price data")
        return None

def run_strategy(strategy_class, strategy_name, prices, start_date=None, end_date=None):
    """Run a single strategy backtest"""
    logger.info(f"\n{'='*60}")
    logger.info(f"Running {strategy_name}")
    logger.info(f"{'='*60}")
    
    # Create account and strategy
    account = TestAccount()
    strategy = strategy_class(account)
    
    # Run backtest
    results = strategy.run_backtest(prices, start_date, end_date)
    
    if 'error' in results:
        logger.error(f"Error: {results['error']}")
        return None
        
    # Print results
    metrics = results.get('metrics', {})
    logger.info(f"\nResults for {strategy_name}:")
    logger.info(f"  Period: {results.get('start_date')} to {results.get('end_date')}")
    logger.info(f"  Total Return: {metrics.get('total_return', 0):.2%}")
    logger.info(f"  Annual Return: {metrics.get('annualized_return', 0):.2%}")
    logger.info(f"  Sharpe Ratio: {metrics.get('sharpe_ratio', 0):.2f}")
    logger.info(f"  Max Drawdown: {metrics.get('max_drawdown', 0):.2%}")
    logger.info(f"  Win Rate: {metrics.get('win_rate', 0):.2%}")
    
    # Save results
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = PATHS.EXPERIMENTS_DIR / "us_factors" / f"{strategy.strategy_name}_{run_id}"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save metrics
    pd.Series(metrics).to_csv(output_dir / "metrics.csv")
    
    # Save equity curve
    equity_data = [
        {
            'timestamp': str(ep.timestamp),
            'equity': ep.equity,
            'pnl_balance': ep.pnl_balance
        }
        for ep in account.equity_history
    ]
    pd.DataFrame(equity_data).to_csv(output_dir / "equity.csv", index=False)
    
    # Save anomalies
    account.save_anomalies(strategy.strategy_name, run_id)
    account.save_summary(strategy.strategy_name, run_id)
    
    logger.info(f"\nResults saved to: {output_dir}")
    
    return results

def main():
    """Main execution"""
    logger.info("US Factor Strategies Runner")
    logger.info("="*60)
    
    # Load data
    prices = load_us_price_data()
    
    if prices is None:
        logger.error("Failed to load price data. Exiting.")
        return
        
    # Define strategies
    strategies = [
        (MomentumStrategy, "US_MOM_12_1"),
        (LowVolStrategy, "US_LOWVOL"),
        (MultiFactorStrategy, "US_MULTI_MVQL")
    ]
    
    # Run all strategies
    results_summary = []
    
    for strategy_class, strategy_name in strategies:
        result = run_strategy(
            strategy_class,
            strategy_name,
            prices,
            start_date="2015-01-01",  # 10-year backtest
            end_date=None
        )
        
        if result:
            results_summary.append({
                'strategy': strategy_name,
                **result.get('metrics', {})
            })
    
    # Print summary
    if results_summary:
        logger.info(f"\n\n{'='*60}")
        logger.info("SUMMARY OF ALL STRATEGIES")
        logger.info(f"{'='*60}")
        
        summary_df = pd.DataFrame(results_summary)
        logger.info(f"\n{summary_df.to_string()}")
        
        # Save summary
        summary_path = PATHS.EXPERIMENTS_DIR / "us_factors" / "summary.csv"
        summary_df.to_csv(summary_path, index=False)
        logger.info(f"\nSummary saved to: {summary_path}")
    
    logger.info(f"\n{'='*60}")
    logger.info("All backtests completed!")
    logger.info(f"{'='*60}")

if __name__ == "__main__":
    main()
