import pandas as pd
import numpy as np
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

from garam.research.regime.backtester import RegimeBacktester
from garam.research.regime.labeler import RegimeLabeler

def simple_strategy(row):
    # Simple Trend Following
    # Buy if Price > MA20
    # Sell if Price < MA20
    price = row.get('close')
    ma = row.get('ma_20')
    if not ma or np.isnan(ma):
        return 0
        
    if price > ma:
        return 1
    elif price < ma:
        return -1
    return 0

def test_backtester():
    # Create dummy data
    dates = pd.date_range(start='2020-01-01', periods=500, freq='D')
    prices = [100]
    for _ in range(499):
        prices.append(prices[-1] * (1 + np.random.normal(0.0005, 0.01)))
        
    df = pd.DataFrame({'close': prices}, index=dates)
    
    # Add features for strategy
    df['ma_20'] = df['close'].rolling(window=20).mean()
    
    # Label Regimes
    labeler = RegimeLabeler()
    df = labeler.label_regimes(df)
    
    # Run Backtest
    backtester = RegimeBacktester()
    trades = backtester.run(df, simple_strategy)
    
    print(f"Total Trades: {len(trades)}")
    
    # Analyze
    stats = backtester.analyze_by_regime(trades)
    print("\nPerformance by Regime:")
    print(stats)
    
    assert len(trades) > 0
    assert not stats.empty
    
    print("Test Passed!")

if __name__ == "__main__":
    test_backtester()
