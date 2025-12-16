# garam_core/live/pnl_tracker.py
from dataclasses import dataclass, field
from typing import List, Dict, Optional
import pandas as pd

@dataclass
class TradeRecord:
    ts: pd.Timestamp
    symbol: str
    side: str
    price: float
    qty: float
    pnl: float = 0.0
    commission: float = 0.0

@dataclass
class PnLState:
    initial_balance: float
    cash: float
    closed_pnl: float = 0.0
    
    # Position tracking for PnL calc
    # symbol -> {qty, avg_price}
    positions: Dict[str, Dict[str, float]] = field(default_factory=dict)
    
    peak_equity: float = 0.0
    current_equity: float = 0.0
    drawdown: float = 0.0
    
    trade_history: List[TradeRecord] = field(default_factory=list)

class PnLTracker:
    def __init__(self, initial_balance: float = 100_000_000.0):
        self.state = PnLState(
            initial_balance=initial_balance,
            cash=initial_balance,
            peak_equity=initial_balance,
            current_equity=initial_balance
        )

    def on_fill(self, ts: pd.Timestamp, symbol: str, side: str, price: float, qty: float, commission: float = 0.0) -> float:
        """
        Updates state on fill. Returns realized PnL for this fill (if any).
        """
        realized_pnl = 0.0
        cost = price * qty
        
        pos = self.state.positions.get(symbol, {"qty": 0.0, "avg_price": 0.0})
        
        if side == "BUY":
            # Avg Price Update
            old_qty = pos["qty"]
            old_avg = pos["avg_price"]
            new_qty = old_qty + qty
            if new_qty > 0:
                new_avg = (old_qty * old_avg + qty * price) / new_qty
            else:
                new_avg = 0.0
            
            pos["qty"] = new_qty
            pos["avg_price"] = new_avg
            
            self.state.cash -= (cost + commission)
            
        elif side == "SELL":
            # Realize PnL
            avg_price = pos["avg_price"]
            # FIFO/Avg matching: PnL = (Exit - Entry) * Qty
            pnl_gross = (price - avg_price) * qty
            realized_pnl = pnl_gross - commission
            
            self.state.closed_pnl += realized_pnl
            self.state.cash += (cost - commission)
            
            pos["qty"] = max(0.0, pos["qty"] - qty)
            if pos["qty"] == 0:
                pos["avg_price"] = 0.0
        
        self.state.positions[symbol] = pos
        
        # Record
        self.state.trade_history.append(TradeRecord(
            ts=ts, symbol=symbol, side=side, price=price, qty=qty, 
            pnl=realized_pnl if side == "SELL" else 0.0,
            commission=commission
        ))
        
        self.update_equity(current_prices={symbol: price}) # Estimate using fill price
        return realized_pnl

    def update_equity(self, current_prices: Dict[str, float]):
        """
        Updates Mark-to-Market Equity based on current prices.
        """
        m2m_value = 0.0
        for sym, pos_data in self.state.positions.items():
            qty = pos_data["qty"]
            if qty > 0:
                px = current_prices.get(sym, pos_data["avg_price"]) # Fallback to cost
                m2m_value += qty * px
        
        total = self.state.cash + m2m_value
        self.state.current_equity = total
        self.state.peak_equity = max(self.state.peak_equity, total)
        
        dd = 0.0
        if self.state.peak_equity > 0:
            dd = (self.state.peak_equity - total) / self.state.peak_equity
        self.state.drawdown = dd

    def get_equity(self) -> float:
        return self.state.current_equity

    def get_drawdown(self) -> float:
        return self.state.drawdown
