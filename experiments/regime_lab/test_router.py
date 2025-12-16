import pandas as pd
import numpy as np
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

from garam.live.regime_router import RegimeRouter

def test_router():
    router = RegimeRouter()
    
    # Create dummy data (Bull Market)
    dates = pd.date_range(start='2020-01-01', periods=300, freq='D')
    prices = [100]
    for _ in range(299):
        prices.append(prices[-1] * (1 + np.random.normal(0.001, 0.005))) # Low Vol Uptrend
        
    df = pd.DataFrame({'close': prices}, index=dates)
    
    # Update Regime
    router.update_regime(df)
    print(f"Detected Regime: {router.current_regime}")
    
    # Get Strategy
    strategy = router.get_active_strategy()
    print("Active Strategy:")
    print(strategy)
    
    assert router.current_regime in ['BULL_LOW_VOL', 'BULL_HIGH_VOL']
    assert strategy['strategy_id'] == 'TrendFollow_MA'
    
    print("Test Passed!")

if __name__ == "__main__":
    test_router()
