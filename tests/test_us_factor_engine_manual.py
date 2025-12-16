
import sys
from pathlib import Path
import json
import pandas as pd

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from alpha_lab.us_academic.factor_engine import FactorEngine
from api.server import app

def test_engine():
    print("\n" + "="*50)
    print("Testing FactorEngine Direct Usage")
    print("="*50)
    
    engine = FactorEngine()
    
    print("1. Loading data...")
    engine.load_data()
    if engine.price_df is not None and not engine.price_df.empty:
        print(f"Success! Loaded prices for {len(engine.price_df.columns)} symbols.")
    else:
        print("Failed to load price data.")
        return

    print("\n2. Calculating factors...")
    rankings = engine.calculate_factors()
    if rankings is not None:
        print(f"Success! Calculated rankings for {len(rankings)} symbols.")
        print("\nTop 5 by Composite Score:")
        print(rankings.sort_values('composite_score', ascending=False).head(5)[['composite_score', 'momentum_rank', 'value_rank']])
    else:
        print("Failed to calculate factors.")
        return

    print("\n3. Testing get_top_opportunities()...")
    tops = engine.get_top_opportunities(n=3)
    print(json.dumps(tops, indent=2))

    print("\n4. Testing get_symbol_profile('AAPL')...")
    profile = engine.get_symbol_profile('AAPL')
    print(json.dumps(profile, indent=2))


def test_api():
    print("\n" + "="*50)
    print("Testing Factor API Endpoints")
    print("="*50)
    
    client = app.test_client()
    
    print("1. Testing /api/us/factors/rankings...")
    # Note: The first call might be slow as it triggers factor calculation
    response = client.get('/api/us/factors/rankings?limit=3')
    if response.status_code == 200:
        data = response.get_json()
        print(f"Success! Count: {data.get('count')}")
        print(json.dumps(data.get('opportunities'), indent=2))
    else:
        print(f"Failed: {response.status_code}")
        print(response.get_json())

    print("\n2. Testing /api/us/factors/AAPL...")
    response = client.get('/api/us/factors/AAPL')
    if response.status_code == 200:
        print("Success!")
        print(json.dumps(response.get_json(), indent=2))
    else:
        print(f"Failed: {response.status_code}")
        print(response.get_json())

if __name__ == "__main__":
    # Run engine test first to populate cache (optional, but good for debugging)
    test_engine()
    
    # Run API test
    test_api()
