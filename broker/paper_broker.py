"""
Paper Broker for GARAM
Simulates order execution for Paper Trading mode.
"""

import logging
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional
from uuid import uuid4
import numpy as np

from .abstract_broker import AbstractBroker

logger = logging.getLogger("PaperBroker")

class PaperBroker(AbstractBroker):
    """
    Paper Trading Broker
    - Simulates execution of orders.
    - Maintains virtual balance and positions.
    - Logs all trades to file.
    """
    
    is_live = False

    def __init__(self, initial_balance: float = 100_000_000, log_dir: Optional[Path] = None):
        self.balance = initial_balance
        self.positions: Dict[str, Dict] = {} # {symbol: {qty, avg_price, current_price}}
        self.orders: Dict[str, Dict] = {}
        self.trade_log = []
        
        # Logging Setup
        self.log_dir = log_dir
        if self.log_dir:
            self.log_dir.mkdir(parents=True, exist_ok=True)
            self.trade_log_path = self.log_dir / f"paper_trades_{datetime.now().strftime('%Y%m%d')}.json"
            self._load_existing_log()
            
        logger.info(f"📝 PaperBroker initialized. Balance: {self.balance:,.0f}")

    def _load_existing_log(self):
        if self.trade_log_path.exists():
            try:
                with open(self.trade_log_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.trade_log = data.get('trades', [])
                    # Restore state if needed? 
                    # For now, we start fresh session or need complex state restoration.
                    # Let's assume fresh session for simplicity, or just append logs.
            except Exception as e:
                logger.error(f"Failed to load trade log: {e}")

    def get_balance(self) -> float:
        return self.balance

    def get_position(self, symbol: str) -> Optional[Dict]:
        return self.positions.get(symbol)
        
    def get_positions(self) -> Dict[str, Dict]:
        return self.positions

    def get_total_equity(self) -> float:
        equity = self.balance
        for symbol, pos in self.positions.items():
            price = pos.get('current_price', pos['avg_price'])
            equity += pos['qty'] * price
        return equity

    def send_order(self, symbol: str, action: str, qty: int, price: float, **kwargs) -> str:
        """
        Simulate Order Execution.
        For Market Orders, 'price' should be the estimated fill price (current price +/- slippage).
        """
        order_id = f"PAPER-{uuid4().hex[:8]}"
        
        logger.info(f"[PAPER] Order Request: {action} {symbol} {qty} @ {price:,.0f}")
        
        # Immediate Fill Simulation (Market Order Assumption)
        # In real Paper Trading, we might want to delay fills for Limit orders,
        # but DGE strategy mostly uses Market orders (or marketable limits).
        self._execute_trade(order_id, symbol, action, qty, price, **kwargs)
        
        return order_id

    def cancel_order(self, order_id: str) -> bool:
        logger.info(f"[PAPER] Cancel Request: {order_id}")
        return True

    def _execute_trade(self, order_id: str, symbol: str, action: str, qty: int, price: float, **kwargs):
        timestamp = datetime.now().isoformat()
        
        # 1. Update State
        if action == 'BUY':
            cost = qty * price
            # Fee simulation could be added here
            if cost > self.balance:
                logger.warning(f"Insufficient balance for BUY {symbol}")
                return
                
            self.balance -= cost
            
            if symbol in self.positions:
                pos = self.positions[symbol]
                total_qty = pos['qty'] + qty
                avg_price = ((pos['qty'] * pos['avg_price']) + (qty * price)) / total_qty
                pos['qty'] = total_qty
                pos['avg_price'] = avg_price
                pos['current_price'] = price
            else:
                self.positions[symbol] = {'qty': qty, 'avg_price': price, 'current_price': price}
                
        elif action == 'SELL':
            if symbol not in self.positions or self.positions[symbol]['qty'] < qty:
                logger.warning(f"Insufficient position for SELL {symbol}")
                return
                
            proceeds = qty * price
            # Fee simulation could be added here
            
            self.balance += proceeds
            self.positions[symbol]['qty'] -= qty
            self.positions[symbol]['current_price'] = price
            
            if self.positions[symbol]['qty'] <= 0:
                del self.positions[symbol]

        # 2. Log Trade
        log_entry = {
            'timestamp': timestamp,
            'order_id': order_id,
            'symbol': symbol,
            'action': action,
            'qty': qty,
            'price': price,
            'equity': self.get_total_equity(),
            **kwargs
        }
        self.trade_log.append(log_entry)
        self._save_log()
        
        logger.info(f"[PAPER] Filled: {action} {symbol} {qty} @ {price:,.0f}")

    def _save_log(self):
        if not self.log_dir: return
        
        data = {
            'date': datetime.now().strftime('%Y%m%d'),
            'summary': {
                'balance': self.balance,
                'equity': self.get_total_equity(),
                'trade_count': len(self.trade_log)
            },
            'trades': self.trade_log
        }
        
        try:
            with open(self.trade_log_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save log: {e}")
