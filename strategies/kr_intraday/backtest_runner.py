"""
KR Intraday Backtest Runner
Bar-by-bar simulation for intraday strategies.
"""

import pandas as pd
import numpy as np
from typing import List, Dict
from datetime import datetime
from pathlib import Path
import sys
import json

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config import PATHS
from data.loaders.kr_minute_loader import KRMinuteLoader
from sim.test_account import TestAccount
from strategies.kr_intraday.base_strategy import BaseIntradayStrategy

class IntradayBacktestRunner:
    """
    Backtest runner for intraday strategies.
    Simulates bar-by-bar execution with TestAccount integration.
    """
    
    def __init__(self, strategy: BaseIntradayStrategy, symbol: str):
        """
        Initialize backtest runner.
        
        Args:
            strategy: Strategy instance
            symbol: Stock symbol to backtest
        """
        self.strategy = strategy
        self.symbol = symbol
        self.loader = KRMinuteLoader()
        
    def run(self, start_date: str = None, end_date: str = None) -> Dict:
        """
        Run backtest.
        
        Args:
            start_date: Start date (YYYY-MM-DD), None for all data
            end_date: End date (YYYY-MM-DD), None for all data
            
        Returns:
            Dict with backtest results and metrics
        """
        # Load data
        df = self.loader.load(self.symbol, interval="1")
        
        if df is None or df.empty:
            return {"error": f"No data found for {self.symbol}"}
            
        # Filter by date range
        if start_date:
            df = df[df.index >= start_date]
        if end_date:
            df = df[df.index <= end_date]
            
        if df.empty:
            return {"error": "No data in date range"}
            
        print(f"Running backtest for {self.symbol}")
        print(f"Data: {df.index[0]} to {df.index[-1]} ({len(df)} bars)")
        
        # Run bar-by-bar simulation
        for timestamp, bar in df.iterrows():
            self._process_bar(bar, timestamp)
            
        # Close any remaining positions at end
        self._close_all_positions(df.iloc[-1], df.index[-1])
        
        # Calculate metrics
        metrics = self._calculate_metrics()
        
        return {
            "symbol": self.symbol,
            "strategy": self.strategy.strategy_name,
            "start_date": str(df.index[0]),
            "end_date": str(df.index[-1]),
            "total_bars": len(df),
            "metrics": metrics
        }
        
    def _process_bar(self, bar: pd.Series, timestamp: datetime):
        """Process a single bar"""
        # Update existing positions
        for position in list(self.strategy.positions):
            action = self.strategy.on_position_update(position, bar)
            
            if action and action.action_type == "EXIT":
                self.strategy.close_position(
                    position, 
                    action.price, 
                    timestamp, 
                    action.reason
                )
                
        # Check for new entry signal
        if len(self.strategy.positions) < self.strategy.max_positions:
            signal = self.strategy.on_bar(bar, timestamp)
            
            if signal:
                self.strategy.open_position(signal, self.symbol, bar)
                
    def _close_all_positions(self, last_bar: pd.Series, timestamp: datetime):
        """Force close all positions at end of backtest"""
        for position in list(self.strategy.positions):
            self.strategy.close_position(
                position,
                last_bar['close'],
                timestamp,
                "End of backtest"
            )
            
    def _calculate_metrics(self) -> Dict:
        """Calculate performance metrics"""
        account = self.strategy.account
        
        if not account.equity_history:
            return {}
            
        # Build equity DataFrame
        equity_df = pd.DataFrame([
            {
                'timestamp': ep.timestamp,
                'equity': ep.equity,
                'pnl_balance': ep.pnl_balance
            }
            for ep in account.equity_history
        ])
        
        # Basic metrics
        total_pnl = account.pnl_balance
        total_return = total_pnl / account.base_capital
        
        # Drawdown
        equity_df['cum_max'] = equity_df['equity'].cummax()
        equity_df['drawdown'] = (equity_df['equity'] - equity_df['cum_max']) / equity_df['cum_max']
        max_dd = abs(equity_df['drawdown'].min())
        
        # Trade statistics
        num_trades = len([ep for ep in account.equity_history if ep.pnl_balance != 0])
        
        # Anomaly stats
        num_anomalies = len(account.anomalies)
        unknown_anomalies = sum(1 for a in account.anomalies if a.root_cause == "UNKNOWN")
        
        return {
            "total_pnl": total_pnl,
            "total_return_pct": total_return * 100,
            "max_drawdown_pct": max_dd * 100,
            "num_trades": num_trades,
            "num_anomalies": num_anomalies,
            "unknown_anomalies": unknown_anomalies,
            "final_equity": equity_df['equity'].iloc[-1]
        }
        
    def save_results(self, results: Dict, run_id: str = None):
        """Save backtest results"""
        if run_id is None:
            run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            
        output_dir = PATHS.EXPERIMENTS_DIR / "kr_intraday" / f"{self.strategy.strategy_name}_{run_id}"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save metrics
        with open(output_dir / "metrics.json", "w") as f:
            json.dump(results, f, indent=2, default=str)
            
        # Save equity curve
        equity_data = [
            {
                'timestamp': str(ep.timestamp),
                'equity': ep.equity,
                'pnl_balance': ep.pnl_balance
            }
            for ep in self.strategy.account.equity_history
        ]
        pd.DataFrame(equity_data).to_csv(output_dir / "equity.csv", index=False)
        
        # Save anomalies
        self.strategy.account.save_anomalies(self.strategy.strategy_name, run_id)
        self.strategy.account.save_summary(self.strategy.strategy_name, run_id)
        
        print(f"\nResults saved to: {output_dir}")
