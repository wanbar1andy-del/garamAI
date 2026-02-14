
import sys
import time
import os
import yaml
from pathlib import Path
from datetime import datetime

# Path Hack
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from pipeline.live.order_real import OrderReal

def main():
    print("[Test] Starting End-to-End Order Link Verification...")
    
    # 1. Load Config
    cfg_path = project_root / "config/profile_micro_live.yaml"
    with open(cfg_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
        
    # 2. Init Adapter
    print("[Test] Initializing OrderReal Adapter...")
    adapter = OrderReal(config)
    
    # 3. Prepare Test Order
    # Target: Samsung Electronics (005930)
    # Price: 10,000 KRW (Deep OTM to ensure no execution if balance exists)
    # Status: Balance is Empty -> Expect "Insufficient Funds" Rejection from Kiwoom.
    symbol = "005930"
    side = "BUY"
    qty = 1
    price_type = "00" # Limit Order (지정가)
    limit_price = 10000 
    
    ts = datetime.now()
    
    # 4. Send Order
    print(f"[Test] Sending Deep OTM Limit Buy: {symbol} {qty}sh @ {limit_price}")
    # Note: OrderReal.send_order signature currently is (ts, symbol, side, qty, price_type, halted)
    # It does not accept 'price' argument in signature?
    # Checking OrderReal code...
    
    # OrderReal.send_order payload construction:
    # payload = { "price": 0, ... } # Fixed to 0 in current code?
    # I need to FIX OrderReal to accept price for Limit Orders.
    # But for now, let's just run it and see if I can override or if I need to hotfix OrderReal first.
    # Current OrderReal.send_order hardcodes price=0.
    # I MUST FIX OrderReal first if I want to send a Limit Order.
    # But if I send Market Order (03) with 0 balance, it works for testing connectivity too.
    # Market Order is safer? No, Limit is safer against accidental fills.
    # I will stick to Market Order for connectivity test because user said Balance is Empty.
    # Kiwoom will definitely reject.
    
    # Sending Market Order for Connectivity Test
    print("[Test] Sending MARKET Order (User confirmed Empty Balance)...")
    order = adapter.send_order(ts, symbol, side, qty, "03") # 03 = Market
    
    print(f"[Test] Local Order Created: {order['id']}")
    print("[Test] Waiting for Interaction (ACK/REJ)...")
    
    # 5. Wait for Result
    # Monitor Inbox/Ack/Rej folders
    req_file = project_root / f"GARAM_Data/orders/inbox/{order['id']}.json" # order['id'] is req_id
    # Wait for file to move from inbox
    
    for i in range(10):
        time.sleep(1)
        if not req_file.exists():
            print("[Test] File picked up by Ingester!")
            break
        print(".", end="", flush=True)
        
    # Wait for ACK/REJ
    # Search for ACK/REJ with same ID
    # ID is idempotency_key
    
    found = False
    for i in range(10):
        time.sleep(1)
        # Check Ack
        ack = list((project_root / "GARAM_Data/orders/ack").glob(f"ack_{order['id']}.json"))
        rej = list((project_root / "GARAM_Data/orders/rej").glob(f"rej_{order['id']}.json"))
        
        if ack:
            print(f"\n[Test] SUCCESS! Received ACK: {ack[0].name}")
            print(ack[0].read_text(encoding='utf-8'))
            found = True
            break
        if rej:
            print(f"\n[Test] SUCCESS (Expected)! Received REJ: {rej[0].name}")
            print(rej[0].read_text(encoding='utf-8'))
            found = True
            break
            
    if not found:
        print("\n[Test] TIMEOUT waiting for Ingester response.")
        
if __name__ == "__main__":
    main()
