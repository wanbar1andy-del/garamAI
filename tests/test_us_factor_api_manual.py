
import sys
from pathlib import Path
import json

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from api.server import app

def test_api():
    client = app.test_client()
    
    print("Testing /api/us/symbols...")
    response = client.get('/api/us/symbols')
    if response.status_code == 200:
        data = response.get_json()
        print(f"Success! Found {data.get('count')} symbols.")
        symbols = data.get('symbols', [])
        if symbols:
            print(f"First 5 symbols: {symbols[:5]}")
            
            # Test price for the first symbol
            symbol = symbols[0]
            print(f"\nTesting /api/us/price/{symbol}...")
            price_response = client.get(f'/api/us/price/{symbol}')
            if price_response.status_code == 200:
                price_data = price_response.get_json()
                points = price_data.get('points', [])
                print(f"Success! Found {len(points)} data points for {symbol}.")
                if points:
                    print(f"Latest point: {points[-1]}")
            else:
                print(f"Failed to get price for {symbol}: {price_response.status_code}")
                print(price_response.get_json())
        else:
            print("No symbols found in response.")
    else:
        print(f"Failed to get symbols: {response.status_code}")
        print(response.get_json())

if __name__ == "__main__":
    test_api()
