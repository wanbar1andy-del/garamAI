"""
Test KR Intraday Strategies
Quick verification script for strategy implementation.
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sim.test_account import TestAccount
from strategies.kr_intraday.gap_reversal import GapReversalStrategy
from strategies.kr_intraday.momentum_breakout import MomentumBreakoutStrategy
from strategies.kr_intraday.backtest_runner import IntradayBacktestRunner

def create_mock_data(num_days=5):
    """Create mock 1-minute data for testing"""
    dates = []
    data = []
    
    base_price = 50000
    
    for day in range(num_days):
        day_date = datetime.now() - timedelta(days=num_days-day)
        
        # Create gap at open
        if day > 0:
            gap = np.random.choice([-0.03, -0.02, 0, 0.02, 0.03])
            base_price = base_price * (1 + gap)
        
        # Generate intraday bars (9:00 - 15:30, 390 minutes)
        for minute in range(390):
            hour = 9 + minute // 60
            min_val = minute % 60
            
            timestamp = day_date.replace(hour=hour, minute=min_val, second=0, microsecond=0)
            
            # Random walk
            change = np.random.normal(0, 0.002)
            base_price = base_price * (1 + change)
            
            # OHLCV
            open_price = base_price
            high_price = base_price * (1 + abs(np.random.normal(0, 0.001)))
            low_price = base_price * (1 - abs(np.random.normal(0, 0.001)))
            close_price = base_price
            volume = np.random.randint(1000, 10000)
            
            dates.append(timestamp)
            data.append({
                'open': open_price,
                'high': high_price,
                'low': low_price,
                'close': close_price,
                'volume': volume
            })
    
    df = pd.DataFrame(data, index=dates)
    return df

def test_gap_reversal():
    """Test Gap Reversal strategy"""
    print("=" * 60)
    print("Testing Gap Reversal Strategy")
    print("=" * 60)
    
    account = TestAccount()
    config = {
        'risk_per_trade': 0.01,
        'max_positions': 3,
        'min_gap_pct': 0.02,
        'wait_minutes': 30,
        'retrace_pct': 0.5,
        'target_r': 1.5,
        'max_holding_minutes': 120
    }
    
    strategy = GapReversalStrategy(account, config)
    
    # Create mock data
    df = create_mock_data(num_days=5)
    
    # Simulate
    for timestamp, bar in df.iterrows():
        # Check for signals
        signal = strategy.on_bar(bar, timestamp)
        if signal:
            print(f"\n[SIGNAL] {timestamp}: {signal.direction} @ {signal.entry_price:.0f}")
            print(f"  Stop: {signal.stop_price:.0f}, Target: {signal.target_price:.0f}")
            print(f"  Reason: {signal.reason}")
            strategy.open_position(signal, "TEST", bar)
        
        # Update positions
        for position in list(strategy.positions):
            action = strategy.on_position_update(position, bar)
            if action:
                print(f"\n[EXIT] {timestamp}: {position.trade_id} @ {action.price:.0f}")
                print(f"  Reason: {action.reason}")
                strategy.close_position(position, action.price, timestamp, action.reason)
    
    # Results
    print(f"\n\nResults:")
    print(f"  Final PnL: {account.pnl_balance:,.0f} KRW")
    print(f"  Trades: {len([ep for ep in account.equity_history if ep.pnl_balance != 0])}")
    print(f"  Anomalies: {len(account.anomalies)}")
    
    return account

def test_momentum_breakout():
    """Test Momentum Breakout strategy"""
    print("\n" + "=" * 60)
    print("Testing Momentum Breakout Strategy")
    print("=" * 60)
    
    account = TestAccount()
    config = {
        'risk_per_trade': 0.01,
        'max_positions': 2,
        'consolidation_bars': 15,
        'max_range_pct': 0.01,
        'volume_multiplier': 1.5,
        'target_r': 2.0,
        'trailing_trigger_r': 1.5,
        'max_holding_minutes': 180
    }
    
    strategy = MomentumBreakoutStrategy(account, config)
    
    # Create mock data
    df = create_mock_data(num_days=5)
    
    # Simulate
    for timestamp, bar in df.iterrows():
        # Check for signals
        signal = strategy.on_bar(bar, timestamp)
        if signal:
            print(f"\n[SIGNAL] {timestamp}: {signal.direction} @ {signal.entry_price:.0f}")
            print(f"  Stop: {signal.stop_price:.0f}, Target: {signal.target_price:.0f}")
            print(f"  Reason: {signal.reason}")
            strategy.open_position(signal, "TEST", bar)
        
        # Update positions
        for position in list(strategy.positions):
            action = strategy.on_position_update(position, bar)
            if action:
                print(f"\n[EXIT] {timestamp}: {position.trade_id} @ {action.price:.0f}")
                print(f"  Reason: {action.reason}")
                strategy.close_position(position, action.price, timestamp, action.reason)
    
    # Results
    print(f"\n\nResults:")
    print(f"  Final PnL: {account.pnl_balance:,.0f} KRW")
    print(f"  Trades: {len([ep for ep in account.equity_history if ep.pnl_balance != 0])}")
    print(f"  Anomalies: {len(account.anomalies)}")
    
    return account

if __name__ == "__main__":
    print("\nKR Intraday Strategies Test\n")
    
    # Test both strategies
    account1 = test_gap_reversal()
    account2 = test_momentum_breakout()
    
    print("\n" + "=" * 60)
    print("All tests completed successfully!")
    print("=" * 60)
