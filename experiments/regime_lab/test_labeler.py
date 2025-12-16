import pandas as pd
import numpy as np
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

from garam.research.regime.labeler import RegimeLabeler

def test_labeler():
    # Create dummy data (2 years)
    dates = pd.date_range(start='2020-01-01', periods=500, freq='D')
    prices = [100]
    
    # Simulate Bull Market
    for _ in range(200):
        prices.append(prices[-1] * (1 + np.random.normal(0.001, 0.01)))
        
    # Simulate Bear Market / Crisis
    for _ in range(100):
        prices.append(prices[-1] * (1 + np.random.normal(-0.005, 0.03))) # High Vol Drop
        
    # Simulate Recovery
    for _ in range(199):
        prices.append(prices[-1] * (1 + np.random.normal(0.001, 0.01)))
        
    df = pd.DataFrame({'close': prices}, index=dates)
    
    labeler = RegimeLabeler()
    df_labeled = labeler.label_regimes(df)
    
    print("Regime Counts:")
    print(df_labeled['regime'].value_counts())
    
    # Check if we have different regimes
    unique_regimes = df_labeled['regime'].unique()
    print(f"Unique Regimes Found: {unique_regimes}")
    
    assert 'BULL_LOW_VOL' in unique_regimes or 'BULL_HIGH_VOL' in unique_regimes
    assert 'UNCERTAIN' in unique_regimes # First 200 days might be uncertain due to MA200
    
    print("Test Passed!")

if __name__ == "__main__":
    test_labeler()
