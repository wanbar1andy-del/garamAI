
import sys
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from garam.research.regime.miracle_engine import Trade, TradeComparator

def test_trade_comparator():
    print("Testing TradeComparator...")
    
    # Setup Mock Trades
    base_time = datetime(2024, 1, 1)
    
    # 1. Matched Trade (Baseline slightly later)
    t1_m = Trade(
        entry_time=base_time, 
        entry_price=100, 
        exit_time=base_time + timedelta(days=5), 
        exit_price=110, 
        side=1, pnl=10, pnl_pct=0.10, duration=5, exit_reason="Target", regime="GREEN"
    )
    
    t1_b = Trade(
        entry_time=base_time + timedelta(days=1), 
        entry_price=101, 
        exit_time=base_time + timedelta(days=5), 
        exit_price=110, 
        side=1, pnl=9, pnl_pct=0.09, duration=4, exit_reason="Target", regime="GREEN"
    )
    
    # 2. Missed Opportunity (Miracle only)
    t2_m = Trade(
        entry_time=base_time + timedelta(days=10), 
        entry_price=100, 
        exit_time=base_time + timedelta(days=12), 
        exit_price=105, 
        side=1, pnl=5, pnl_pct=0.05, duration=2, exit_reason="Target", regime="GREEN"
    )
    
    miracle_trades = [t1_m, t2_m]
    baseline_trades = [t1_b]
    
    comparator = TradeComparator(baseline_trades, miracle_trades)
    df_res = comparator.run_comparison()
    
    print("\nComparison Result:")
    print(df_res[['type', 'entry_gap_days', 'pnl_gap']])
    
    # Assertions
    assert len(df_res) == 2
    
    # Check Match
    match = df_res[df_res['type'] == 'MATCHED'].iloc[0]
    assert match['entry_gap_days'] == 1 # Baseline was 1 day late
    assert abs(match['pnl_gap'] - 0.01) < 0.0001 # 10% - 9% = 1%
    
    # Check Miss
    miss = df_res[df_res['type'] == 'MISSED_OPPORTUNITY'].iloc[0]
    assert miss['pnl_gap'] == 0.05
    
    print("\nTradeComparator Test Passed!")

if __name__ == "__main__":
    test_trade_comparator()
