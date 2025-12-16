import json
import pandas as pd
from datetime import datetime
from pathlib import Path
import sys

# Add project root
sys.path.insert(0, 'C:/garam/garam')
from config import PATHS

def inject_trade():
    symbol = "005930"
    price = 72500
    qty = 10
    side = "BUY"
    
    # 1. Update Trades Log
    today = datetime.now().strftime('%Y%m%d')
    trade_file = PATHS.KR_ROOT / "paper_trading" / f"trades_{today}.csv"
    trade_file.parent.mkdir(parents=True, exist_ok=True)
    
    trade = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'symbol': symbol,
        'side': side,
        'quantity': qty,
        'price': price,
        'order_id': f"MOCK_{int(datetime.now().timestamp())}",
        'pnl': 0, # Entry has 0 realized pnl
        'realized_pnl': 0
    }
    
    if trade_file.exists():
        df = pd.read_csv(trade_file)
        df = pd.concat([df, pd.DataFrame([trade])], ignore_index=True)
    else:
        df = pd.DataFrame([trade])
        
    df.to_csv(trade_file, index=False)
    print(f"Injected trade to {trade_file}")
    
    # 2. Update Positions
    pos_file = PATHS.KR_ROOT / "paper_trading" / "positions.json"
    
    positions = []
    if pos_file.exists():
        with open(pos_file, 'r') as f:
            data = json.load(f)
            positions = data.get('positions', [])
            
    # Check if exists
    found = False
    for p in positions:
        if p['symbol'] == symbol:
            p['quantity'] += qty
            p['current_price'] = price # Update current price too
            found = True
            break
            
    if not found:
        positions.append({
            'symbol': symbol,
            'quantity': qty,
            'entry_price': price,
            'current_price': price,
            'pnl': 0
        })
        
    with open(pos_file, 'w') as f:
        json.dump({'positions': positions}, f, indent=4)
    print(f"Updated positions in {pos_file}")

if __name__ == "__main__":
    inject_trade()
