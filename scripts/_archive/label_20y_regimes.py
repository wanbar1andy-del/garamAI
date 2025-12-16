"""
Label 20-Year Regimes
Uses MarketRegimeDetector to label 20 years of daily data.
"""

import pandas as pd
from pathlib import Path
import sys
import matplotlib.pyplot as plt

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root.parent))

from garam.config import PATHS
from garam.alpha_lab.regime.market_regime import MarketRegimeDetector

def label_regimes():
    # history_dir = PATHS.DATA_DIR / "history"
    history_dir = Path("g:/내 드라이브/garamdata/history")
    files = list(history_dir.glob("*_daily_20y.csv"))
    
    detector = MarketRegimeDetector()
    
    for file in files:
        print(f"Processing {file.name}...")
        df = pd.read_csv(file)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.set_index('timestamp').sort_index()
        
        # Compute Regime
        regime_df = detector.compute_regime(
            prices=df['close'],
            high=df['high'],
            low=df['low'],
            close=df['close']
        )
        
        # Merge back
        result = df.join(regime_df)
        
        # Save labeled data
        output_file = history_dir / f"labeled_{file.name}"
        result.to_csv(output_file)
        print(f"Saved labeled data to {output_file}")
        
        # Visualize (Optional - save plot)
        plt.figure(figsize=(15, 7))
        plt.plot(result.index, result['close'], label='Close', color='black', alpha=0.5)
        
        # Color background by regime
        # Green
        green_mask = result['state'] == 'GREEN'
        if green_mask.any():
            plt.fill_between(result.index, result['close'].min(), result['close'].max(), where=green_mask, color='green', alpha=0.1, label='GREEN (Bull)')
            
        # Red
        red_mask = result['state'] == 'RED'
        if red_mask.any():
            plt.fill_between(result.index, result['close'].min(), result['close'].max(), where=red_mask, color='red', alpha=0.1, label='RED (Bear)')
            
        # Yellow
        yellow_mask = result['state'] == 'YELLOW'
        if yellow_mask.any():
            plt.fill_between(result.index, result['close'].min(), result['close'].max(), where=yellow_mask, color='yellow', alpha=0.1, label='YELLOW (Choppy)')
            
        plt.title(f"Market Regimes - {file.name}")
        plt.legend()
        plt.savefig(history_dir / f"regime_plot_{file.stem}.png")
        print(f"Saved plot to regime_plot_{file.stem}.png")
        plt.close()

if __name__ == "__main__":
    label_regimes()
