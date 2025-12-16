import pandas as pd
import numpy as np
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

from garam.research.ai.labeling import add_forward_R_label
from garam.research.ai.feature_pipeline import build_features

# Mock Loader
class MockLoader:
    def load(self, symbol, interval):
        # Return a dummy dataframe with price increasing
        dates = pd.date_range(start='2025-11-25 09:00', periods=60, freq='1min')
        prices = np.linspace(100, 110, 60) # 10% increase
        df = pd.DataFrame({
            'open': prices, 'high': prices+1, 'low': prices-1, 'close': prices, 'volume': 1000
        }, index=dates)
        return df

def test_pipeline():
    # 1. Create Dummy Signals
    signals = pd.DataFrame({
        'timestamp': [pd.Timestamp('2025-11-25 09:10')],
        'symbol': ['005930'],
        'price': [102.0], # Entry at 102
        'signal': [1],
        'strategy_id': ['TrendFollow'],
        'regime_ml': ['BULL_LOW_VOL'],
        'features_json': ['{"rsi": 60, "ma_20": 100}']
    })
    
    print("Original Signals:")
    print(signals)
    
    # 2. Test Labeling
    loader = MockLoader()
    df_labeled = add_forward_R_label(signals, price_loader=loader, horizon_bars=10)
    
    print("\nLabeled Data:")
    print(df_labeled[['label_max_return', 'label_good_trade']])
    
    # Check Label
    # Price goes 100->110 over 60 mins. 
    # At 09:10 (idx 10), price is ~101.6. 
    # Horizon 10 mins -> 09:20. Price ~103.3.
    # Max High in future should be > 102.
    # Return should be positive.
    assert df_labeled['label_max_return'].iloc[0] > 0
    assert df_labeled['label_good_trade'].iloc[0] == 1
    
    # 3. Test Feature Pipeline
    df_features = build_features(df_labeled)
    print("\nFeature Matrix:")
    print(df_features.columns)
    print(df_features.iloc[0])
    
    assert 'feat_rsi' in df_features.columns
    assert df_features['feat_rsi'].iloc[0] == 60
    
    print("\nTest Passed!")

if __name__ == "__main__":
    test_pipeline()
