"""
Test PaperBroker
Verifies that PaperBroker correctly handles orders and logs them.
"""

import sys
from pathlib import Path
import time
import json

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from broker.paper_broker import PaperBroker
from config import PATHS

def test_paper_broker():
    print(">>> Testing PaperBroker...")
    
    # 1. Init
    broker = PaperBroker(initial_balance=100_000_000, log_dir=PATHS.PAPER_LOGS)
    print(f"Initial Balance: {broker.get_balance():,.0f}")
    
    # 2. Buy Order
    symbol = "005930"
    price = 70000
    qty = 10
    
    print(f"\nSending BUY {symbol} {qty} @ {price}")
    broker.send_order(symbol, "BUY", qty, price)
    
    # Check Position
    pos = broker.get_position(symbol)
    print(f"Position: {pos}")
    assert pos['qty'] == 10
    assert pos['avg_price'] == 70000
    
    # Check Balance
    expected_balance = 100_000_000 - (70000 * 10)
    print(f"Balance: {broker.get_balance():,.0f} (Expected: {expected_balance:,.0f})")
    assert broker.get_balance() == expected_balance
    
    # 3. Sell Order (Partial)
    print(f"\nSending SELL {symbol} 5 @ 71000")
    broker.send_order(symbol, "SELL", 5, 71000)
    
    pos = broker.get_position(symbol)
    print(f"Position: {pos}")
    assert pos['qty'] == 5
    
    # Check Balance
    expected_balance += (71000 * 5)
    print(f"Balance: {broker.get_balance():,.0f} (Expected: {expected_balance:,.0f})")
    assert broker.get_balance() == expected_balance
    
    # 4. Check Log File
    log_file = list(PATHS.PAPER_LOGS.glob("paper_trades_*.json"))[-1]
    print(f"\nChecking Log File: {log_file}")
    
    with open(log_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        print(f"Trades logged: {len(data['trades'])}")
        assert len(data['trades']) == 2
        
    print("\n>>> PaperBroker Test Passed!")

if __name__ == "__main__":
    test_paper_broker()
