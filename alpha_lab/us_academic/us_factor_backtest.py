"""
US Factor Backtest Runner
Long-horizon backtest runner for US academic factor strategies.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import sys
import yaml
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config import PATHS
from data.loaders.us_sp500_loader import USSP500DataLoader
from sim.test_account import TestAccount, TradeExpectation, TradeOutcome
from alpha_lab.us_academic.factor_portfolios import (
    build_factor_portfolio, 
    calculate_performance_metrics
)
# Assuming academic_factors functions are available or we mock them for now if not fully integrated
# from alpha_lab.us_academic.academic_factors import ... 

@dataclass
class StrategyEvaluation:
    name: str
    metrics: Dict[str, float]
    approved: bool
    failed_criteria: List[str]

class USFactorBacktestRunner:
    """
    Long-horizon backtest runner for US academic factor strategies.
    """
    
    def __init__(self, config_path: Optional[Path] = None):
        self.loader = USSP500DataLoader()
        self.config_path = config_path or PATHS.CONFIG_DIR / "us_factor_approval_rules.yaml"
        self.approval_rules = self._load_rules()
        
    def _load_rules(self) -> dict:
        if not self.config_path.exists():
            return {}
        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f)

    def run_backtest(self, 
                     strategy_name: str, 
                     start_date: str, 
                     end_date: str, 
                     cost_bp: float = 20.0) -> StrategyEvaluation:
        """
        Run a backtest for a specific strategy.
        For v1, we simulate the 'backtest' by calculating factor returns 
        and applying them to the TestAccount.
        """
        
        # 1. Load Data (Mocking for now as we don't have full factor logic connected to loader yet)
        # In real impl: 
        # universe, prices = self.loader.get_universe_and_prices(start_date, end_date)
        # factor_scores = calculate_factor_scores(prices, strategy_name)
        # portfolio_returns = build_factor_portfolio(factor_scores, ...)
        
        # For prototype/test, we'll generate synthetic returns if no real data
        # This allows the runner to be tested structurally without full data
        
        dates = pd.date_range(start=start_date, end=end_date, freq='D')
        
        # Synthetic daily returns for demonstration (Mean 8% annual, 15% vol)
        np.random.seed(42) # For reproducibility
        daily_vol = 0.15 / np.sqrt(252)
        daily_ret_mean = 0.08 / 252
        returns = np.random.normal(daily_ret_mean, daily_vol, len(dates))
        
        # Apply costs (simplified: assume daily rebalance for worst case, or 1/20 for monthly)
        # Let's assume monthly rebalancing turnover approx 20% -> daily avg cost
        # This is a placeholder. Real impl needs actual turnover.
        daily_cost = (cost_bp / 10000) * 0.01 # Very rough approx
        net_returns = returns - daily_cost
        
        # 2. Run Accounting
        account = TestAccount()
        
        for r, date in zip(net_returns, dates):
            # Daily PnL = Capital * Return (Constant Notional)
            # Note: In constant notional, we always trade on base_capital
            daily_pnl = account.base_capital * r
            account.on_trade_closed(daily_pnl, date)
            
        # 3. Compute Metrics
        # We can use account.equity_history to compute metrics
        equity_df = pd.DataFrame([
            {'date': ep.timestamp, 'equity': ep.equity} 
            for ep in account.equity_history
        ])
        equity_df.set_index('date', inplace=True)
        
        # Calculate basic metrics
        total_ret = (equity_df['equity'].iloc[-1] / account.base_capital) - 1
        days = (equity_df.index[-1] - equity_df.index[0]).days
        years = days / 365.25
        cagr = (1 + total_ret) ** (1/years) - 1 if years > 0 else 0
        
        # Volatility
        daily_rets = equity_df['equity'].pct_change().dropna()
        vol = daily_rets.std() * np.sqrt(252)
        
        # Sharpe (Rf=0 for simplicity)
        sharpe = (cagr / vol) if vol > 0 else 0
        
        # Max DD
        cum_max = equity_df['equity'].cummax()
        drawdown = (equity_df['equity'] - cum_max) / cum_max
        max_dd = abs(drawdown.min())
        
        metrics = {
            "total_return": total_ret,
            "cagr": cagr,
            "volatility": vol,
            "sharpe": sharpe,
            "max_drawdown": max_dd,
            "years": years
        }
        
        # 4. Evaluate
        approved, failed = self._evaluate_strategy(strategy_name, metrics)
        
        # 5. Save Results (Placeholder for file writing)
        self._save_results(strategy_name, metrics, account)
        
        return StrategyEvaluation(
            name=strategy_name,
            metrics=metrics,
            approved=approved,
            failed_criteria=failed
        )

    def _evaluate_strategy(self, name: str, metrics: Dict[str, float]) -> Tuple[bool, List[str]]:
        defaults = self.approval_rules.get('defaults', {})
        specific = self.approval_rules.get('strategies', {}).get(name, {})
        
        # Merge rules
        rules = {**defaults, **specific}
        
        failed = []
        if metrics['sharpe'] < rules.get('min_sharpe', 0):
            failed.append(f"Sharpe {metrics['sharpe']:.2f} < {rules.get('min_sharpe')}")
            
        if metrics['max_drawdown'] > rules.get('max_drawdown', 1.0):
            failed.append(f"MaxDD {metrics['max_drawdown']:.2f} > {rules.get('max_drawdown')}")
            
        if metrics['cagr'] < rules.get('min_cagr', -1.0):
            failed.append(f"CAGR {metrics['cagr']:.2f} < {rules.get('min_cagr')}")
            
        return (len(failed) == 0), failed

    def _save_results(self, name: str, metrics: Dict, account: TestAccount):
        run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = PATHS.EXPERIMENTS_DIR / "us_factors" / f"{name}_{run_id}"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save metrics
        pd.Series(metrics).to_csv(output_dir / "metrics.csv")
        
        # Save equity curve
        equity_data = [
            {'date': ep.timestamp, 'equity': ep.equity, 'pnl': ep.pnl_balance} 
            for ep in account.equity_history
        ]
        pd.DataFrame(equity_data).to_csv(output_dir / "equity.csv", index=False)
        
        # Save summary report
        with open(output_dir / "report.md", "w") as f:
            f.write(f"# Backtest Report: {name}\n")
            f.write(f"Run ID: {run_id}\n\n")
            f.write("## Metrics\n")
            for k, v in metrics.items():
                f.write(f"- {k}: {v:.4f}\n")

