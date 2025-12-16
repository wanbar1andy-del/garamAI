"""
Optimize Regime Strategies
Finds optimal strategy parameters for each market regime (GREEN, YELLOW, RED).
"""

import pandas as pd
import numpy as np
import yaml
from pathlib import Path
import sys
import itertools

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root.parent))

from garam.config import PATHS

class SimpleBacktester:
    """
    Fast vectorized backtester for parameter optimization.
    """
    def __init__(self, data: pd.DataFrame):
        self.data = data
        
    def run(self, strategy_func, params) -> float:
        """
        Returns Sharpe Ratio
        """
        signals = strategy_func(self.data, **params)
        
        # Shift signals to align with next day's return
        # Signal today executes at Close (or Open next day). 
        # For simplicity, assume Close-to-Close return next day.
        returns = self.data['close'].pct_change().shift(-1)
        
        strategy_returns = signals * returns
        
        # Calculate Sharpe
        if strategy_returns.std() == 0:
            return 0.0
            
        sharpe = (strategy_returns.mean() / strategy_returns.std()) * np.sqrt(252)
        return sharpe

def trend_following_strategy(df, window_fast, window_slow):
    """
    Simple MA Crossover
    """
    fast_ma = df['close'].rolling(window=window_fast).mean()
    slow_ma = df['close'].rolling(window=window_slow).mean()
    
    signals = pd.Series(0, index=df.index)
    signals[fast_ma > slow_ma] = 1
    signals[fast_ma < slow_ma] = -1 # Or 0 for long-only
    return signals

def mean_reversion_strategy(df, window, std_dev):
    """
    Bollinger Band Reversion
    """
    ma = df['close'].rolling(window=window).mean()
    std = df['close'].rolling(window=window).std()
    upper = ma + (std * std_dev)
    lower = ma - (std * std_dev)
    
    signals = pd.Series(0, index=df.index)
    # Buy below lower band
    signals[df['close'] < lower] = 1
    # Sell above upper band
    signals[df['close'] > upper] = -1 # Or 0
    return signals

def optimize():
    # Load labeled data (Use KR for now)
    # data_path = PATHS.DATA_DIR / "history" / "labeled_KR_daily_20y.csv"
    data_path = Path("g:/내 드라이브/garamdata/history/labeled_KR_KOSPI_daily_20y.csv")
    if not data_path.exists():
        print("Data not found.")
        return
        
    df = pd.read_csv(data_path)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.set_index('timestamp').sort_index()
    
    regimes = ['GREEN', 'YELLOW', 'RED']
    best_configs = {}
    
    # Define search space
    # Trend Following for GREEN/RED (Directional)
    trend_params = list(itertools.product(
        [3, 5, 10, 15, 20, 30], # fast
        [20, 40, 50, 60, 100, 120, 200] # slow
    ))
    
    # Mean Reversion for YELLOW (Choppy)
    mr_params = list(itertools.product(
        [5, 10, 20, 40], # window
        [1.0, 1.5, 2.0, 2.5, 3.0] # std_dev
    ))
    
    for regime in regimes:
        print(f"\nOptimizing for {regime}...")
        
        # Filter data for this regime
        # Note: This is "In-Sample" optimization on the regime slices.
        # In reality, we trade only when regime is active.
        # We concatenate all chunks of this regime to form a continuous series for simplified testing.
        regime_data = df[df['state'] == regime].copy()
        
        if len(regime_data) < 100:
            print("Not enough data.")
            continue
            
        tester = SimpleBacktester(regime_data)
        
        best_score = -999
        best_param = None
        best_strategy = ""
        
        # Test Trend Following
        for fast, slow in trend_params:
            if fast >= slow: continue
            score = tester.run(trend_following_strategy, {'window_fast': fast, 'window_slow': slow})
            if score > best_score:
                best_score = score
                best_param = {'window_fast': fast, 'window_slow': slow}
                best_strategy = "TrendFollowing"
                
        # Test Mean Reversion
        for win, std in mr_params:
            score = tester.run(mean_reversion_strategy, {'window': win, 'std_dev': std})
            if score > best_score:
                best_score = score
                best_param = {'window': win, 'std_dev': std}
                best_strategy = "MeanReversion"
                
        print(f"Best: {best_strategy} {best_param} (Sharpe: {best_score:.2f})")
        
        best_configs[regime] = {
            'strategy': best_strategy,
            'params': best_param,
            'sharpe': float(round(best_score, 2))
        }
        
    # Save Matrix
    output_file = PATHS.CONFIG_DIR / "regime_strategy_matrix.yaml"
    with open(output_file, 'w') as f:
        yaml.dump(best_configs, f)
    print(f"\nSaved matrix to {output_file}")

if __name__ == "__main__":
    optimize()
