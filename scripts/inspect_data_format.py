"""
Inspect Price Format in Cache
"""
import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

def inspect_data():
    cache_path = PROJECT_ROOT / "cache" / "market_matrix_8m.pkl"
    cached = pd.read_pickle(cache_path)
    closes = cached['closes']
    
    symbol = closes.columns[0]
    sample = closes[symbol].dropna().head(10)
    
    print(f"📊 [Data Inspection: {symbol}]")
    print(f"   - Head values:\n{sample}")
    print(f"   - Min: {closes[symbol].min()}, Max: {closes[symbol].max()}")
    
    if closes[symbol].max() < 20:
        print("\n💡 데이터가 Log(Price) 형태일 가능성이 높습니다.")
    else:
        print("\n💡 데이터가 Raw(Price) 형태입니다.")

if __name__ == "__main__":
    inspect_data()
