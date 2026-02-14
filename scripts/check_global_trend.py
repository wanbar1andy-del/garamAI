"""
Check Global Trend of 8-Month Dataset
"""
import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

def check_trend():
    cache_path = PROJECT_ROOT / "cache" / "market_matrix_8m.pkl"
    cached = pd.read_pickle(cache_path)
    closes = cached['closes']
    
    # Calculate global mean return for all symbols
    start_prices = closes.iloc[0]
    end_prices = closes.iloc[-1]
    returns = (end_prices / start_prices - 1) * 100
    
    print(f"📊 [Global Dataset Trend (8 Months)]")
    print(f"   - Average Return (All Symbols): {returns.mean():+.2f}%")
    print(f"   - Median Return: {returns.median():+.2f}%")
    print(f"   - Positive Symbols: {(returns > 0).sum()} / {len(returns)}")
    print(f"   - Negative Symbols: {(returns < 0).sum()} / {len(returns)}")
    
    # Check Samsung Electronics Specifically
    if "005930" in returns:
        print(f"   - Samsung Elec (005930) 8m Return: {returns['005930']:+.2f}%")

if __name__ == "__main__":
    check_trend()
