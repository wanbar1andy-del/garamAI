"""
Portfolio Simulator
Unified backtesting framework combining KR and US strategies with Surfing Brain allocation.
"""

from typing import List, Dict, Optional
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import logging
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sim.test_account import TestAccount
from strategies.kr_intraday.base_strategy import BaseIntradayStrategy
from alpha_lab.us_academic.strategies.base_factor_strategy import BaseFactorStrategy
from surfing_brain.surfing_brain_v1 import SurfingBrain, MarketState

logger = logging.getLogger(__name__)

class AllocationDecision:
    """Portfolio allocation decision"""
    def __init__(self, kr_pct: float, us_pct: float, cash_pct: float):
        self.kr_pct = kr_pct
        self.us_pct = us_pct
        self.cash_pct = cash_pct
        self.timestamp = datetime.now()

class PortfolioSimulator:
    """
    Unified portfolio simulator.
    
    Combines KR Intraday and US Factor strategies with Surfing Brain allocation logic.
    """
    
    def __init__(self,
                 kr_strategies: List[BaseIntradayStrategy],
                 us_strategies: List[BaseFactorStrategy],
                 surfing_brain: Optional[SurfingBrain] = None,
                 base_capital: float = 100_000_000):
        """
        Initialize portfolio simulator.
        
        Args:
            kr_strategies: List of KR intraday strategies
            us_strategies: List of US factor strategies
            surfing_brain: Surfing Brain for allocation (optional)
            base_capital: Base capital in KRW
        """
        self.kr_strategies = kr_strategies
        self.us_strategies = us_strategies
        self.surfing_brain = surfing_brain
        self.base_capital = base_capital
        
        # Create separate accounts for tracking
        self.kr_account = TestAccount(base_capital=base_capital)
        self.us_account = TestAccount(base_capital=base_capital)
        self.portfolio_account = TestAccount(base_capital=base_capital)
        
        # Allocation history
        self.allocation_history: List[AllocationDecision] = []
        
        logger.info(f"Portfolio Simulator initialized with {len(kr_strategies)} KR and {len(us_strategies)} US strategies")
        
    def get_allocation(self, date: datetime) -> AllocationDecision:
        """
        Get portfolio allocation for a given date.
        
        Args:
            date: Current date
            
        Returns:
            AllocationDecision with KR%, US%, Cash%
        """
        if self.surfing_brain is None:
            # Default allocation: 50% KR, 50% US
            return AllocationDecision(kr_pct=0.5, us_pct=0.5, cash_pct=0.0)
        
        # Get market state (simplified for now)
        state = MarketState(
            regime="EAT",  # TODO: Implement regime detection
            uncertainty=0.3,
            recent_expectancy_r=0.1,
            recent_drawdown=0.05
        )
        
        # Get Surfing Brain decision
        decision = self.surfing_brain.decide(state)
        
        # Convert to allocation percentages
        # Simplified: use risk multiplier to adjust allocations
        risk_mult = decision.risk_multiplier
        
        if decision.mode == "AGGRESSIVE":
            kr_pct = 0.4 * risk_mult
            us_pct = 0.5 * risk_mult
        elif decision.mode == "CONSERVATIVE":
            kr_pct = 0.2 * risk_mult
            us_pct = 0.3 * risk_mult
        else:  # DEFENSIVE
            kr_pct = 0.1 * risk_mult
            us_pct = 0.2 * risk_mult
        
        cash_pct = 1.0 - kr_pct - us_pct
        
        allocation = AllocationDecision(kr_pct, us_pct, cash_pct)
        self.allocation_history.append(allocation)
        
        return allocation
    
    def run_backtest(self, 
                    start_date: str,
                    end_date: str,
                    kr_data: Optional[pd.DataFrame] = None,
                    us_data: Optional[pd.DataFrame] = None) -> Dict:
        """
        Run unified portfolio backtest.
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            kr_data: KR price data (optional, for intraday strategies)
            us_data: US price data (optional, for factor strategies)
            
        Returns:
            Dict with backtest results and metrics
        """
        logger.info(f"Running portfolio backtest from {start_date} to {end_date}")
        
        # Convert dates
        start_dt = pd.to_datetime(start_date)
        end_dt = pd.to_datetime(end_date)
        
        # Generate daily schedule
        dates = pd.date_range(start=start_dt, end=end_dt, freq='B')
        
        # Initialize results containers
        daily_metrics = []
        
        # Main Loop
        for date in dates:
            # 1. Get Allocation
            allocation = self.get_allocation(date)
            
            # 2. Calculate P&L for this day
            # KR P&L
            kr_pnl = 0.0
            if kr_data is not None and not kr_data.empty:
                # Look for P&L in provided data (assuming it's a daily P&L series)
                # If kr_data is a DataFrame with index as date and 'pnl' column
                try:
                    if date in kr_data.index:
                        kr_pnl = kr_data.loc[date]['pnl']
                except KeyError:
                    pass
            
            # US P&L
            us_pnl = 0.0
            if us_data is not None and not us_data.empty:
                try:
                    if date in us_data.index:
                        us_pnl = us_data.loc[date]['pnl']
                except KeyError:
                    pass
            
            # Apply Allocation Weights (Simplified)
            # We assume the strategies return raw P&L on their base capital.
            # We scale this by our allocation.
            # Example: If KR strategy made 1M on 100M base (1%), and we allocate 40% (40M),
            # we should make 0.4M.
            
            # However, our input data might be raw P&L from a 100M test account.
            # So we scale: (Raw P&L / Strategy Base) * (Portfolio Base * Allocation)
            
            kr_strategy_base = 100_000_000 # Assumption from NP-1
            us_strategy_base = 100_000_000 # Assumption
            
            weighted_kr_pnl = (kr_pnl / kr_strategy_base) * (self.base_capital * allocation.kr_pct)
            weighted_us_pnl = (us_pnl / us_strategy_base) * (self.base_capital * allocation.us_pct)
            
            # Cash return (assume 0 for now, or risk-free rate)
            cash_pnl = 0.0
            
            total_daily_pnl = weighted_kr_pnl + weighted_us_pnl + cash_pnl
            
            # Update Accounts
            self.kr_account.pnl_balance += weighted_kr_pnl
            self.us_account.pnl_balance += weighted_us_pnl
            self.portfolio_account.pnl_balance += total_daily_pnl
            
            # Record Equity
            self.kr_account._record_equity(date)
            self.us_account._record_equity(date)
            self.portfolio_account._record_equity(date)
            
            daily_metrics.append({
                'date': date,
                'kr_pnl': weighted_kr_pnl,
                'us_pnl': weighted_us_pnl,
                'total_pnl': total_daily_pnl,
                'allocation_kr': allocation.kr_pct,
                'allocation_us': allocation.us_pct,
                'equity': self.base_capital + self.portfolio_account.pnl_balance
            })
            
        results = {
            "start_date": start_date,
            "end_date": end_date,
            "kr_strategies": len(self.kr_strategies),
            "us_strategies": len(self.us_strategies),
            "base_capital": self.base_capital,
            "final_equity": self.base_capital + self.portfolio_account.pnl_balance,
            "total_pnl": self.portfolio_account.pnl_balance,
            "daily_metrics": daily_metrics
        }
        
        logger.info("Portfolio backtest completed")
        
        return results
    
    def get_portfolio_metrics(self) -> Dict:
        """
        Calculate portfolio-level metrics.
        
        Returns:
            Dict with portfolio metrics
        """
        # Calculate combined metrics
        kr_pnl = self.kr_account.pnl_balance
        us_pnl = self.us_account.pnl_balance
        total_pnl = kr_pnl + us_pnl
        
        total_return = total_pnl / self.base_capital
        
        # Calculate allocation statistics
        if self.allocation_history:
            avg_kr_alloc = np.mean([a.kr_pct for a in self.allocation_history])
            avg_us_alloc = np.mean([a.us_pct for a in self.allocation_history])
            avg_cash_alloc = np.mean([a.cash_pct for a in self.allocation_history])
        else:
            avg_kr_alloc = avg_us_alloc = avg_cash_alloc = 0.0
        
        return {
            "total_pnl": total_pnl,
            "total_return_pct": total_return * 100,
            "kr_pnl": kr_pnl,
            "us_pnl": us_pnl,
            "avg_kr_allocation": avg_kr_alloc,
            "avg_us_allocation": avg_us_alloc,
            "avg_cash_allocation": avg_cash_alloc,
            "num_allocations": len(self.allocation_history)
        }
