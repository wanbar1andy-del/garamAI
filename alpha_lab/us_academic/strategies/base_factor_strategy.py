"""
Base Factor Strategy
Abstract base class for US factor strategies with TestAccount integration.
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional
from datetime import datetime
import pandas as pd
import numpy as np
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from config import PATHS
from sim.test_account import TestAccount, TradeExpectation, TradeOutcome
from alpha_lab.us_academic.factor_portfolios import (
    build_factor_portfolio,
    calculate_performance_metrics
)

class BaseFactorStrategy(ABC):
    """
    Abstract base class for US factor strategies.
    
    Unlike intraday strategies, factor strategies:
    - Rebalance monthly (not individual trades)
    - Track portfolio-level returns
    - Use Sharpe/DD expectations (not R-multiples)
    """
    
    def __init__(self, 
                 account: TestAccount,
                 config: dict,
                 strategy_name: str):
        """
        Initialize strategy.
        
        Args:
            account: TestAccount instance
            config: Strategy configuration
            strategy_name: Unique strategy identifier
        """
        self.account = account
        self.config = config
        self.strategy_name = strategy_name
        
        # Portfolio config
        self.rebalance_freq = config.get('rebalance_freq', 'M')
        self.long_only = config.get('long_only', False)
        self.long_quantile = config.get('long_quantile', 0.8)
        self.short_quantile = config.get('short_quantile', 0.2)
        
        # Performance tracking
        self.period_counter = 0
        
    @abstractmethod
    def calculate_scores(self, prices: pd.DataFrame) -> pd.Series:
        """
        Calculate factor scores for all symbols.
        
        Args:
            prices: DataFrame with prices (index=date, columns=symbols)
            
        Returns:
            Series of factor scores (index=symbols)
        """
        pass
    
    @abstractmethod
    def get_expected_metrics(self) -> Dict[str, tuple]:
        """
        Get expected performance metric ranges.
        
        Returns:
            Dict with keys: 'sharpe', 'max_dd', 'annual_return'
            Values are tuples: (min, max)
        """
        pass
    
    def build_portfolio(self, prices: pd.DataFrame, scores: pd.Series) -> pd.Series:
        """
        Build portfolio from scores.
        
        Args:
            prices: Price DataFrame
            scores: Factor scores
            
        Returns:
            Series of daily portfolio returns
        """
        return build_factor_portfolio(
            prices=prices,
            scores=scores,
            long_quantile=self.long_quantile,
            short_quantile=self.short_quantile,
            rebalance_freq=self.rebalance_freq,
            long_only=self.long_only,
            equal_weight=True
        )
    
    def run_backtest(self, 
                    prices: pd.DataFrame,
                    start_date: str = None,
                    end_date: str = None) -> Dict:
        """
        Run backtest and log to TestAccount.
        
        Args:
            prices: Price DataFrame
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            
        Returns:
            Dict with backtest results
        """
        # Filter by date range
        if start_date:
            prices = prices[prices.index >= start_date]
        if end_date:
            prices = prices[prices.index <= end_date]
            
        if prices.empty:
            return {"error": "No data in date range"}
            
        # Calculate scores
        scores = self.calculate_scores(prices)
        
        if scores.empty or scores.isna().all():
            return {"error": "Failed to calculate scores"}
            
        # Build portfolio
        portfolio_returns = self.build_portfolio(prices, scores)
        
        if portfolio_returns.empty:
            return {"error": "Failed to build portfolio"}
            
        # Log to TestAccount (treat entire backtest as one "trade")
        self._log_to_account(portfolio_returns)
        
        # Calculate metrics
        metrics = calculate_performance_metrics(portfolio_returns)
        
        return {
            "strategy": self.strategy_name,
            "start_date": str(portfolio_returns.index[0].date()),
            "end_date": str(portfolio_returns.index[-1].date()),
            "metrics": metrics
        }
    
    def _log_to_account(self, returns: pd.Series):
        """Log portfolio returns to TestAccount"""
        # Calculate total P&L
        cumulative_return = (1 + returns).prod() - 1
        total_pnl = self.account.base_capital * cumulative_return
        
        # Create expectation
        expected_metrics = self.get_expected_metrics()
        
        self.period_counter += 1
        trade_id = f"{self.strategy_name}_{self.period_counter:04d}"
        
        expectation = TradeExpectation(
            trade_id=trade_id,
            expected_direction="LONG",  # Portfolio direction
            expected_R_range=expected_metrics['sharpe'],  # Use Sharpe as proxy
            expected_holding_period=len(returns),
            expected_regime="UNKNOWN",
            notes=f"Portfolio backtest {returns.index[0].date()} to {returns.index[-1].date()}"
        )
        
        # Calculate actual metrics
        actual_metrics = calculate_performance_metrics(returns)
        
        outcome = TradeOutcome(
            trade_id=trade_id,
            realized_R=actual_metrics.get('sharpe_ratio', 0),
            actual_holding_period=len(returns),
            realized_pnl=total_pnl,
            regime_at_entry="UNKNOWN",
            regime_at_exit="UNKNOWN",
            max_favorable_excursion_R=actual_metrics.get('max_drawdown', 0),
            max_adverse_excursion_R=actual_metrics.get('max_drawdown', 0)
        )
        
        # Log to account
        self.account.on_trade_closed(
            total_pnl,
            returns.index[-1],
            expectation,
            outcome
        )
