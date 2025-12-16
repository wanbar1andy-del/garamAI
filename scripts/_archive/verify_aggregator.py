import sys
import pandas as pd
import numpy as np
from pathlib import Path

# Setup Path to allow 'import garam'
sys.path.append("C:\\garam")

try:
    from garam.core.alpha_aggregator import AlphaAggregator
except ImportError as e:
    print(f"Import Error: {e}")
    print(f"Current sys.path: {sys.path}")
    sys.exit(1)

def create_dummy_data():
    dates = pd.date_range(start="2023-01-01", periods=200, freq="D")
    symbols = ["005930", "000660", "035420"]
    
    # Random Prices
    close = pd.DataFrame(np.random.randn(200, 3) + 100, index=dates, columns=symbols)
    high = close + 2
    low = close - 2
    volume = pd.DataFrame(np.random.randint(1000, 5000, size=(200, 3)), index=dates, columns=symbols)
    
    return {
        "daily_close": close,
        "daily_high": high,
        "daily_low": low,
        "daily_volume": volume
    }

def main():
    print("Initializing AlphaAggregator...")
    agg = AlphaAggregator()
    print(f"Loaded Alphas: {list(agg.alphas.keys())}")
    
    if not agg.alphas:
        print("No active alphas found. Check alpha_catalog.yaml state.")
        return

    print("\nCreating Dummy Data...")
    market_data = create_dummy_data()
    universe = ["005930", "000660", "035420"]
    
    regime = "R3_UP_BOX"
    print(f"\nComputing Scores for Regime: {regime}")
    
    final_score, breakdown = agg.compute_final_score(market_data, universe, regime)
    
    if not final_score.empty:
        print("\nFinal Scores (Last 5 days):")
        print(final_score.tail())
        print("\nBreakdown (Raw Scores):")
        for aid, df in breakdown.items():
            print(f"--- {aid} ---")
            print(df.tail())
    else:
        print("No scores computed.")

if __name__ == "__main__":
    main()
