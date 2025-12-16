"""
KR Intraday Performance Runner
Orchestrates backtests for KR intraday strategies and generates performance reports.
"""

import argparse
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import sys
import json
import logging

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import PATHS
from data.loaders.kr_minute_loader import KRMinuteLoader
from sim.test_account import TestAccount
from sim.cost_model import CostModel
from strategies.kr_intraday.backtest_runner import IntradayBacktestRunner
from strategies.kr_intraday.gap_reversal import GapReversalStrategy
from strategies.kr_intraday.momentum_breakout import MomentumBreakoutStrategy

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(PATHS.LOGS_DIR / "performance_runner.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("PerformanceRunner")

class PerformanceRunner:
    def __init__(self, top_n: int = 20):
        self.top_n = top_n
        self.loader = KRMinuteLoader()
        self.strategies = {
            "GAP_REVERSAL": GapReversalStrategy,
            "MOMENTUM_BREAKOUT": MomentumBreakoutStrategy
        }
        
    def get_universe(self) -> list:
        """
        Get top N symbols by turnover.
        For now, returning a static list of top liquid KR stocks for testing.
        TODO: Implement dynamic selection based on turnover data.
        """
        # Top liquid stocks (Samsung, SK Hynix, POSCO, etc.)
        return [
            "005930", "000660", "005490", "035420", "006400", 
            "051910", "000270", "068270", "005380", "105560",
            "035720", "012330", "028260", "096770", "011170",
            "032830", "003550", "034020", "015760", "017670"
        ][:self.top_n]

    def run(self, start_date: str, end_date: str, strategy_names: list = None):
        """
        Run backtests for specified strategies and date range.
        """
        if strategy_names is None:
            strategy_names = list(self.strategies.keys())
            
        universe = self.get_universe()
        results = []
        
        logger.info(f"Starting performance run from {start_date} to {end_date}")
        logger.info(f"Strategies: {strategy_names}")
        logger.info(f"Universe: {len(universe)} symbols")
        
        combined_daily_pnl = {} # Date -> PnL
        
        for symbol in universe:
            # Check if data exists first
            df = self.loader.load(symbol)
            if df is None or df.empty:
                logger.warning(f"No data for {symbol}, skipping")
                continue
                
            for strat_name in strategy_names:
                if strat_name not in self.strategies:
                    logger.warning(f"Unknown strategy {strat_name}, skipping")
                    continue
                    
                logger.info(f"Running {strat_name} on {symbol}...")
                
                # Initialize strategy and runner
                # Note: We create a fresh account for each run to isolate metrics per strategy/symbol
                # We will aggregate PnL later for the combined report
                account = TestAccount(base_capital=100_000_000) 
                config = {} # Default config
                strategy = self.strategies[strat_name](account, config)
                runner = IntradayBacktestRunner(strategy, symbol)
                
                # Run backtest
                res = runner.run(start_date=start_date, end_date=end_date)
                
                if "error" in res:
                    logger.warning(f"Backtest failed for {symbol} {strat_name}: {res['error']}")
                    continue
                    
                # Collect daily PnL for aggregation
                # We need to extract daily PnL from equity history
                equity_history = strategy.account.equity_history
                if equity_history:
                    # Convert to daily series
                    eq_df = pd.DataFrame([
                        {'timestamp': ep.timestamp, 'pnl': ep.pnl_balance} 
                        for ep in equity_history
                    ])
                    eq_df['date'] = eq_df['timestamp'].dt.date
                    # Get last PnL of each day (cumulative)
                    daily_cum_pnl = eq_df.groupby('date')['pnl'].last()
                    
                    # Calculate daily change (daily PnL)
                    daily_change = daily_cum_pnl.diff().fillna(daily_cum_pnl.iloc[0])
                    
                    for date, pnl in daily_change.items():
                        date_str = str(date)
                        combined_daily_pnl[date_str] = combined_daily_pnl.get(date_str, 0.0) + pnl
                
                results.append(res)
                
        # Generate Reports
        self._generate_reports(results, combined_daily_pnl, start_date, end_date)
        
    def _generate_reports(self, results: list, combined_daily_pnl: dict, start_date: str, end_date: str):
        """Generate JSON and Markdown reports"""
        run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = PATHS.EXPERIMENTS_DIR / "kr_intraday"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 1. Combined Metrics
        sorted_dates = sorted(combined_daily_pnl.keys())
        daily_pnls = [combined_daily_pnl[d] for d in sorted_dates]
        
        if not daily_pnls:
            logger.warning("No trades executed, cannot generate report.")
            return

        total_pnl = sum(daily_pnls)
        # Assuming 100M capital allocation for the "bucket" (or sum of allocations?)
        # For simplicity, let's assume the combined portfolio has 100M base capital
        base_capital = 100_000_000 
        
        daily_returns = [pnl / base_capital for pnl in daily_pnls]
        
        # Metrics
        win_days = sum(1 for r in daily_returns if r > 0)
        total_days = len(daily_returns)
        win_rate = win_days / total_days if total_days > 0 else 0
        
        # Hit rate (>= 0.4%)
        hit_days = sum(1 for r in daily_returns if r >= 0.004)
        hit_rate = hit_days / total_days if total_days > 0 else 0
        
        avg_daily_return = np.mean(daily_returns) if daily_returns else 0
        std_daily_return = np.std(daily_returns) if daily_returns else 0
        sharpe = (avg_daily_return / std_daily_return * np.sqrt(252)) if std_daily_return > 0 else 0
        
        # Max Drawdown (on daily PnL cumsum)
        cum_pnl = np.cumsum(daily_pnls)
        peak = np.maximum.accumulate(cum_pnl)
        drawdown = peak - cum_pnl
        max_dd = np.max(drawdown) if len(drawdown) > 0 else 0
        max_dd_pct = max_dd / base_capital
        
        summary = {
            "run_id": run_id,
            "start_date": start_date,
            "end_date": end_date,
            "total_pnl": total_pnl,
            "total_return_pct": (total_pnl / base_capital) * 100,
            "win_rate": win_rate,
            "hit_rate_0.4pct": hit_rate,
            "avg_daily_return_pct": avg_daily_return * 100,
            "sharpe_ratio": sharpe,
            "max_drawdown_pct": max_dd_pct * 100,
            "total_days": total_days
        }
        
        # Save JSON
        with open(output_dir / f"performance_{run_id}.json", "w") as f:
            json.dump(summary, f, indent=2)
            
        # Save Daily PnL CSV
        pd.DataFrame({
            "date": sorted_dates, 
            "pnl": daily_pnls,
            "return_pct": [r * 100 for r in daily_returns]
        }).to_csv(output_dir / f"daily_pnl_{run_id}.csv", index=False)
        
        # Generate Markdown Report
        report_path = output_dir / f"report_{run_id}.md"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(f"# KR Intraday Performance Report ({run_id})\n\n")
            f.write(f"**Period:** {start_date} to {end_date}\n")
            f.write(f"**Strategies:** {', '.join(self.strategies.keys())}\n\n")
            
            f.write("## 1. Executive Summary\n")
            f.write(f"- **Total P&L:** {total_pnl:,.0f} KRW\n")
            f.write(f"- **Return:** {(total_pnl/base_capital)*100:.2f}%\n")
            f.write(f"- **Hit Rate (>= 0.4%):** {hit_rate*100:.1f}%\n")
            f.write(f"- **Win Rate:** {win_rate*100:.1f}%\n")
            f.write(f"- **Max Drawdown:** {max_dd_pct*100:.2f}%\n")
            f.write(f"- **Sharpe Ratio:** {sharpe:.2f}\n\n")
            
            f.write("## 2. Daily Performance\n")
            f.write("| Date | P&L (KRW) | Return (%) | Target Met? |\n")
            f.write("|------|-----------|------------|-------------|\n")
            for date, pnl, ret in zip(sorted_dates, daily_pnls, daily_returns):
                met = "✅" if ret >= 0.004 else "❌"
                f.write(f"| {date} | {pnl:,.0f} | {ret*100:.2f}% | {met} |\n")
                
        logger.info(f"Reports generated in {output_dir}")
        print(f"Report saved to {report_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run KR Intraday Performance Test")
    parser.add_argument("--start", type=str, required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", type=str, required=True, help="End date (YYYY-MM-DD)")
    parser.add_argument("--top_n", type=int, default=20, help="Number of top symbols to test")
    parser.add_argument("--strategies", nargs="+", help="List of strategies to run")
    
    args = parser.parse_args()
    
    runner = PerformanceRunner(top_n=args.top_n)
    runner.run(args.start, args.end, args.strategies)
