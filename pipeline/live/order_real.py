import os
import json
import uuid
import csv
import glob
from pathlib import Path
from datetime import datetime

class OrderReal:
    def __init__(self, config):
        self.config = config
        self.slippage = config['execution']['slippage_bps']
        self.fee = config['execution']['fee_bps']
        
        self.orders = [] # Active orders (local state)
        self.fills = []  # Filled orders (history)
        self.positions = {} # sym -> {qty, cost_basis}
        
        # Initial Capital (loaded from config, but should ideally sync with Account)
        self.cash = config['execution']['capital']
        
        # Paths
        project_root = Path(__file__).resolve().parent.parent.parent
        self.orders_dir = project_root / "GARAM_Data/orders"
        self.inbox_dir = self.orders_dir / "inbox"
        self.fill_file = self.orders_dir / "chejan_fills.csv"
        
        self.processed_fill_ids = set()
        
        # Load existing fills to avoid double processing on restart
        self._load_existing_fills()
        
        print(f"[OrderReal] Initialized with Capital: {self.cash:,.0f} KRW")
        print(f"[OrderReal] Inbox: {self.inbox_dir}")
        print(f"[OrderReal] Fills: {self.fill_file}")

    def _load_existing_fills(self):
        """Load fill history to build state and ignore processed items"""
        if not self.fill_file.exists():
            return
            
        try:
            with open(self.fill_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Schema: ts, order_id, symbol, side, price, qty
                    fill_id = f"{row.get('order_id')}_{row.get('ts')}" # basic unique key
                    self.processed_fill_ids.add(fill_id)
        except Exception as e:
            print(f"[OrderReal] Error loading history: {e}")

    def send_order(self, ts, symbol, side, qty, price_type="MARKET", halted=False):
        # 1. Centralized Halt / Validation
        if halted and side == 'BUY':
             print(f"[OrderReal] REJECT (HALT): {side} {symbol}")
             return {
                'id': f"REJ_{symbol}_{ts}",
                'status': 'REJECTED',
                'reject_reason': 'HALT_ACTIVE'
            }
            
        if qty <= 0:
            return {
                'id': f"REJ_{symbol}_{ts}",
                'status': 'REJECTED',
                'reject_reason': 'QTY_ZERO'
            }

        # 2. Risk Check (Pre-Trade Cap)
        # Assuming simple Check here (more complex logic in RiskManager)
        # NOTE: run_live_paper.py already calls logic BEFORE send_order for sizing, 
        # but adapter should also be safe.
        
        # 3. Create Request File
        req_id = f"req_{uuid.uuid4().hex[:8]}" # short uuid
        order_id = req_id # Use req_id as internal ID until Kiwoom ID is assigned (async)
        
        payload = {
            "idempotency_key": req_id,
            "timestamp": int(ts.timestamp()),
            "symbol": symbol,
            "order_type": side.lower(), # buy/sell
            "qty": qty,
            "price": 0, # MARKET
            "price_type": "03" # 03=Market
        }
        
        file_path = self.inbox_dir / f"{req_id}.json"
        tmp_path = file_path.with_suffix(".json.tmp")
        
        try:
            with open(tmp_path, 'w', encoding='utf-8') as f:
                json.dump(payload, f, indent=4)
            # Atomic Move
            os.replace(tmp_path, file_path)
            
            print(f"[OrderReal] SENT {side} {symbol} {qty} -> {req_id}")
            
            order = {
                'id': order_id,
                'ts': ts,
                'symbol': symbol,
                'side': side,
                'qty': qty,
                'type': price_type,
                'status': 'OPEN' # SENT
            }
            self.orders.append(order)
            return order
            
        except Exception as e:
            print(f"[OrderReal] FAILED to write order: {e}")
            return {'status': 'ERROR', 'reject_reason': str(e)}

    def process_fills(self, current_dt, market_data):
        """
        Read chejan_fills.csv and update local state.
        Differs from Mock: uses Real Fills, not Market Price.
        """
        new_fills = []
        status_updates = []
        
        if not self.fill_file.exists():
            return new_fills, status_updates
            
        try:
            fills_to_process = []
            with open(self.fill_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Valid check
                    if not row.get('order_id'): continue
                    
                    fill_id = f"{row.get('order_id')}_{row.get('ts')}"
                    if fill_id in self.processed_fill_ids:
                        continue
                        
                    fills_to_process.append(row)
                    self.processed_fill_ids.add(fill_id)
            
            for row in fills_to_process:
                # {ts, order_id, symbol, side, price, qty}
                sym = row['symbol']
                side = row['side'] # BUY/SELL
                qty = int(row['qty'])
                price = float(row['price'])
                oid = row['order_id']
                
                # Update Cash & Position
                cost = qty * price
                
                # Fee/Tax Calculation (Approximation for local tracking)
                # Real balance should come from Opw00018, but for now we mirror locally
                trade_fee = cost * (self.fee / 10000.0)
                
                if side == 'BUY':
                    self.cash -= (cost + trade_fee)
                    
                    if sym not in self.positions:
                        self.positions[sym] = {'qty': 0, 'cost_basis': 0}
                    
                    old_qty = self.positions[sym]['qty']
                    old_cost = self.positions[sym]['cost_basis'] * old_qty
                    
                    new_qty = old_qty + qty
                    if new_qty > 0:
                        self.positions[sym]['cost_basis'] = (old_cost + (price * qty)) / new_qty
                    self.positions[sym]['qty'] = new_qty
                    
                elif side == 'SELL':
                    # Tax usually only on Sell
                    proceeds = cost - trade_fee
                    self.cash += proceeds
                    
                    if sym in self.positions:
                        self.positions[sym]['qty'] -= qty
                        if self.positions[sym]['qty'] <= 0:
                            del self.positions[sym]
                            
                # Create Fill Record
                fill = {
                    'id': oid,
                    'order_id': oid,
                    'symbol': sym,
                    'side': side,
                    'qty': qty,
                    'fill_px': price,
                    'fill_ts': datetime.strptime(row['ts'], "%Y-%m-%d %H:%M:%S"),
                    'fee': trade_fee,
                    'ts': current_dt # Engine Time
                }
                new_fills.append(fill)
                self.fills.append(fill)
                
                # Update Matching Order Status
                # Heuristic: Find oldest OPEN order for sym/side
                # (Kiwoom req_id != order_id, so tricky to map precisely without map file)
                # For Phase 30-5, we just mark *any* open order for that symbol as Filled?
                # Or we assume 1-1 mapping if we only have 1 active.
                # Let's try to match by Side/Symbol
                matched = False
                for o in self.orders:
                    if o['status'] == 'OPEN' and o['symbol'] == sym and o['side'] == side:
                        o['status'] = 'FILLED' # Logic: Assume FIFO fill
                        o['kiwoom_id'] = oid
                        status_updates.append(o)
                        matched = True
                        break
                        
                if not matched:
                    # Unsolicited Fill? (Manual Trade?)
                    print(f"[OrderReal] Unsolicited Fill: {side} {sym} {qty}")
                    
        except Exception as e:
            print(f"[OrderReal] Fill Process Error: {e}")
            
        return new_fills, status_updates

    def get_equity(self, market_data):
        eq = self.cash
        for sym, pos in self.positions.items():
            if sym in market_data:
                eq += pos['qty'] * market_data[sym]['close']
            else:
                # Use Cost Basis if no market data (fallback)
                eq += pos['qty'] * pos['cost_basis']
        return eq
