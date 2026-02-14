import pandas as pd
from datetime import datetime

class OrderMock:
    def __init__(self, config):
        self.config = config
        self.slippage = config['execution']['slippage_bps']
        self.fee = config['execution']['fee_bps']
        self.orders = [] # Active orders
        self.fills = []  # Filled orders
        self.positions = {} # sym -> {qty, avg_px}
        self.cash = config['execution']['capital']
        self._seq = 0
        print(f"[OrderMock] Initialized with Capital: {self.cash}")
        
    def send_order(self, ts, symbol, side, qty, price_type="MARKET", halted=False):
        self._seq += 1
        order_id = f"ORD_{ts.strftime('%H%M%S')}_{symbol}_{side}_{self._seq}"
        
        # Centralized Halt Logic (Reject New Buys)
        if halted and side == 'BUY':
             print(f"[Order] REJECT (HALT): {side} {symbol}")
             return {
                'id': order_id,
                'ts': ts,
                'symbol': symbol,
                'side': side, 
                'qty': qty,
                'type': price_type,
                'status': 'REJECTED',
                'reject_reason': 'HALT_ACTIVE'
            }

        order = {
            'id': order_id,
            'ts': ts,
            'symbol': symbol,
            'side': side, # BUY/SELL
            'qty': qty,
            'type': price_type,
            'status': 'OPEN'
        }
        self.orders.append(order)
        print(f"[Order] Sending {side} {symbol} {qty} @ {price_type}")
        return order
        
    def process_fills(self, current_dt, market_data):
        """
        Check open orders against market_data.
        market_data: {symbol: {open, high, low, close, volume}}
        """
        filled_now = [] # List of fill dicts
        fills = [] 
        status_updates = [] # List of order dicts
        
        # Snapshot of orders to process (copy)
        open_orders = [o for o in self.orders if o['status'] == 'OPEN']
        
        for order in open_orders:
            sym = order['symbol']
            
            # Check market data
            if sym not in market_data:
                continue
                
            md = market_data[sym]
            market_price = md['open'] # Fill at Open
            
            # Apply Slippage (BPS)
            # slippage_bps = 20 -> 0.002
            slip_rate = self.config['execution']['slippage_bps'] / 10000.0
            
            if order['side'] == 'BUY':
                fill_px = market_price * (1 + slip_rate)
            else:
                fill_px = market_price * (1 - slip_rate)
                
            # Apply Fee (BPS)
            # fee_bps = 1.5 -> 0.00015
            fee_rate = self.config['execution']['fee_bps'] / 10000.0
            
            cost = 0
            proceeds = 0
            pre_cash = self.cash
            
            if order['side'] == 'BUY':
                cost = fill_px * order['qty'] * (1 + fee_rate)
                if self.cash >= cost:
                    self.cash -= cost
                    if sym not in self.positions:
                        self.positions[sym] = {'qty': 0, 'cost_basis': 0}
                    
                    # Avg Cost Update
                    old_qty = self.positions[sym]['qty']
                    old_cost = self.positions[sym]['cost_basis'] * old_qty
                    self.positions[sym]['qty'] += order['qty']
                    self.positions[sym]['cost_basis'] = (old_cost + (fill_px * order['qty'])) / self.positions[sym]['qty']
                    
                    fill = {
                        'id': order['id'],       # Legacy
                        'order_id': order['id'], # Standard (New Schema)
                        'symbol': sym,
                        'side': 'BUY',
                        'qty': order['qty'],
                        'fill_px': fill_px,      # Standard
                        'fill_ts': current_dt,   # Standard
                        'fee': cost - (fill_px * order['qty']),
                        'ts': current_dt         # Legacy overlap
                    }
                    fills.append(fill)
                    order['status'] = 'FILLED'
                    filled_now.append(fill)
                    status_updates.append(order)
                    print(f"[Fill] BUY {sym} {order['qty']} @ {fill_px:.2f} (Cost: {cost:.2f}) [Cash: {pre_cash:.0f} -> {self.cash:.0f} (Delta: {self.cash-pre_cash:.0f})]")
                else:
                    order['status'] = 'REJECTED' # Insufficient Funds
                    order['reject_reason'] = 'INSUFFICIENT_CASH'
                    status_updates.append(order)
                    print(f"[Order] REJECT: Insufficient Cash for {sym} (Req: {cost:.2f}, Avail: {self.cash:.2f})")
            
            elif order['side'] == 'SELL':
                proceeds = fill_px * order['qty'] * (1 - fee_rate)
                # Check position
                if sym in self.positions and self.positions[sym]['qty'] >= order['qty']:
                    self.cash += proceeds
                    self.positions[sym]['qty'] -= order['qty']
                    if self.positions[sym]['qty'] <= 1e-9:
                        del self.positions[sym]
                        
                    fill = {
                         'id': order['id'],
                        'symbol': sym,
                        'side': 'SELL',
                        'qty': order['qty'],
                        'fill_px': fill_px,
                        'fee': (fill_px * order['qty']) - proceeds,
                        'fill_ts': current_dt
                    }
                    fills.append(fill)
                    order['status'] = 'FILLED'
                    filled_now.append(fill) 
                    status_updates.append(order)
                    print(f"[Fill] SELL {sym} {order['qty']} @ {fill_px:.2f} (Proceeds: {proceeds:.2f}) [Cash: {pre_cash:.0f} -> {self.cash:.0f} (Delta: {self.cash-pre_cash:.0f})]")
                else:
                     order['status'] = 'REJECTED' # No Position
                     order['reject_reason'] = 'NO_POSITION'
                     status_updates.append(order)
                     print(f"[Order] REJECT: Insufficient Position for {sym} (Req: {order['qty']}, Avail: {self.positions.get(sym, {'qty':0})['qty']})")

        # Add newly processed fills to the main fills list
        self.fills.extend(fills)
        # Remove filled/rejected orders from the active orders list
        self.orders = [o for o in self.orders if o['status'] == 'OPEN']
        return filled_now, status_updates

    def _update_pos(self, sym, qty, sign):
        # This method is no longer directly used by process_fills,
        # but might be used elsewhere or kept for legacy.
        # The new fill logic updates positions directly.
        if sym not in self.positions:
            self.positions[sym] = {'qty': 0, 'avg_px': 0}
            
        curr = self.positions[sym]
        new_qty = curr['qty'] + (qty * sign)
        
        if new_qty <= 0:
            del self.positions[sym]
        else:
            self.positions[sym]['qty'] = new_qty
            
    def get_equity(self, market_data):
        eq = self.cash
        for sym, pos in self.positions.items():
            if sym in market_data:
                # Mark to Market (Close)
                eq += pos['qty'] * market_data[sym]['close']
            # If no market data, assume last known? (Simplification: Ignore in replay)
        return eq
