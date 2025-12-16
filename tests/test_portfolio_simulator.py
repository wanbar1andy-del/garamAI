"""
Test Portfolio Simulator
Verify unified portfolio backtest functionality.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sim.portfolio_simulator import PortfolioSimulator, AllocationDecision
from sim.test_account import TestAccount
from strategies.kr_intraday.gap_reversal import GapReversalStrategy
from strategies.kr_intraday.momentum_breakout import MomentumBreakoutStrategy
from alpha_lab.us_academic.strategies.momentum_strategy import MomentumStrategy
from alpha_lab.us_academic.strategies.low_vol_strategy import LowVolStrategy

def test_portfolio_simulator():
    """Test portfolio simulator initialization and basic functionality"""
    print("=" * 60)
    print("Testing Portfolio Simulator")
    print("=" * 60)
    
    # Create strategies
    kr_account1 = TestAccount()
    kr_account2 = TestAccount()
    us_account1 = TestAccount()
    us_account2 = TestAccount()
    
    kr_strategies = [
        GapReversalStrategy(kr_account1, {}),
        MomentumBreakoutStrategy(kr_account2, {})
    ]
    
    us_strategies = [
        MomentumStrategy(us_account1),
        LowVolStrategy(us_account2)
    ]
    
    # Create portfolio simulator
    simulator = PortfolioSimulator(
        kr_strategies=kr_strategies,
        us_strategies=us_strategies,
        surfing_brain=None,  # Use default allocation
        base_capital=100_000_000
    )
    
    print(f"\nPortfolio Simulator created:")
    print(f"  KR Strategies: {len(simulator.kr_strategies)}")
    print(f"  US Strategies: {len(simulator.us_strategies)}")
    print(f"  Base Capital: {simulator.base_capital:,.0f} KRW")
    
    # Test allocation
    from datetime import datetime
    allocation = simulator.get_allocation(datetime.now())
    
    print(f"\nDefault Allocation:")
    print(f"  KR: {allocation.kr_pct:.1%}")
    print(f"  US: {allocation.us_pct:.1%}")
    print(f"  Cash: {allocation.cash_pct:.1%}")
    
    # Test backtest (simplified)
    results = simulator.run_backtest(
        start_date="2024-01-01",
        end_date="2024-12-31"
    )
    
    print(f"\nBacktest Results:")
    for key, value in results.items():
        print(f"  {key}: {value}")
    
    # Test metrics
    metrics = simulator.get_portfolio_metrics()
    
    print(f"\nPortfolio Metrics:")
    for key, value in metrics.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.2f}")
        else:
            print(f"  {key}: {value}")
    
    return simulator

if __name__ == "__main__":
    print("\nPortfolio Simulator Test\n")
    
    simulator = test_portfolio_simulator()
    
    print("\n" + "=" * 60)
    print("Test completed successfully!")
    print("=" * 60)
