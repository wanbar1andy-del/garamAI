"""
Base Intraday Strategy
Abstract base class for all KR intraday strategies.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime
import pandas as pd
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sim.test_account import TestAccount, TradeExpectation, TradeOutcome

@dataclass
class Signal:
    """Trading signal"""
    direction: str  # "LONG" or "SHORT"
    entry_price: float
    stop_price: float
    target_price: float
    timestamp: datetime
    reason: str = ""

@dataclass
class Position:
    """Open position"""
    trade_id: str
    symbol: str
    direction: str
    entry_price: float
    stop_price: float
    target_price: float
    quantity: int
    entry_time: datetime
    current_price: float = 0.0
    mfe_r: float = 0.0  # Max Favorable Excursion in R
    mae_r: float = 0.0  # Max Adverse Excursion in R

@dataclass
class Action:
    """Position action (exit or modify)"""
    action_type: str  # "EXIT", "MODIFY_STOP", "MODIFY_TARGET"
    price: float
    reason: str = ""

class BaseIntradayStrategy(ABC):
    """
    Abstract base class for intraday strategies.
    Handles position sizing, R-based risk, and TestAccount integration.
    """
    
    def __init__(self, 
                 account: TestAccount,
                 config: dict,
                 strategy_name: str,
                 broker=None):
        """
        Initialize strategy.
        
        Args:
            account: TestAccount instance
            config: Strategy configuration dict
            strategy_name: Unique strategy identifier
            broker: Optional broker instance for execution (Paper/Live)
        """
        self.account = account
        self.config = config
        self.strategy_name = strategy_name
        self.broker = broker
        
        # Position tracking
        self.positions: List[Position] = []
        self.trade_counter = 0
        
        # Config defaults
        self.risk_per_trade = config.get('risk_per_trade', 0.01)  # 1% of capital
        self.max_positions = config.get('max_positions', 3)
        
    @abstractmethod
    def on_bar(self, bar: pd.Series, timestamp: datetime) -> Optional[Signal]:
        """
        Process new bar and generate signal.
        
        Args:
            bar: OHLCV bar data
            timestamp: Bar timestamp
            
        Returns:
            Signal if entry condition met, None otherwise
        """
        pass
    
    @abstractmethod
    def on_position_update(self, position: Position, bar: pd.Series) -> Optional[Action]:
        """
        Update open position and check exit conditions.
        
        Args:
            position: Current position
            bar: Current bar data
            
        Returns:
            Action if exit/modify needed, None otherwise
        """
        pass
    
    @abstractmethod
    def create_expectation(self, trade_id: str, signal: Signal) -> TradeExpectation:
        """
        Create trade expectation for anomaly tracking.
        
        Args:
            trade_id: Unique trade identifier
            signal: Entry signal
            
        Returns:
            TradeExpectation with expected R-range and holding period
        """
        pass
    
    def calculate_position_size(self, entry_price: float, stop_price: float) -> int:
        """
        Calculate position size based on R-based risk.
        Enforces 1% Cash Buffer Rule.
        """
        # 1. Calculate Risk Amount (e.g. 2% of Capital)
        base_capital = self.account.base_capital if hasattr(self.account, 'base_capital') else 100_000_000
        risk_amount = base_capital * self.risk_per_trade
        
        price_risk = abs(entry_price - stop_price)
        if price_risk == 0:
            return 0
            
        # 2. Initial Quantity based on Risk
        quantity = int(risk_amount / price_risk)
        
        # 3. Safety Cap: Max Position Size (e.g. 25% of capital)
        max_position_val = base_capital * 0.25
        if quantity * entry_price > max_position_val:
            quantity = int(max_position_val / entry_price)
            
        # 4. [NEW] 1% Cash Buffer Rule
        # We must ensure we have at least 1% of Total Equity as CASH after this trade.
        # Required Cash = Total Equity * 0.01
        # Available for Trade = Current Cash - Required Cash
        
        current_cash = self.account.get_balance()
        required_buffer = base_capital * 0.01
        max_trade_cost = current_cash - required_buffer
        
        if max_trade_cost <= 0:
            # Not enough cash to maintain buffer
            return 0
            
        current_trade_cost = quantity * entry_price
        if current_trade_cost > max_trade_cost:
            # Reduce quantity to fit budget
            quantity = int(max_trade_cost / entry_price)
            
        return max(0, quantity)
    
    def open_position(self, signal: Signal, symbol: str, bar: pd.Series):
        """Open a new position"""
        if len(self.positions) >= self.max_positions:
            return
            
        self.trade_counter += 1
        trade_id = f"{self.strategy_name}_{self.trade_counter:04d}"
        
        quantity = self.calculate_position_size(signal.entry_price, signal.stop_price)
        
        position = Position(
            trade_id=trade_id,
            symbol=symbol,
            direction=signal.direction,
            entry_price=signal.entry_price,
            stop_price=signal.stop_price,
            target_price=signal.target_price,
            quantity=quantity,
            entry_time=signal.timestamp,
            current_price=signal.entry_price
        )
        
        self.positions.append(position)
        
        # Execute via Broker if available
        if self.broker:
            action = "BUY" if signal.direction == "LONG" else "SELL"
            self.broker.send_order(symbol, action, quantity, signal.entry_price)
        
    def close_position(self, position: Position, exit_price: float, 
                      exit_time: datetime, reason: str):
        """Close a position and record to TestAccount"""
        # Calculate P&L
        if position.direction == "LONG":
            pnl = (exit_price - position.entry_price) * position.quantity
        else:
            pnl = (position.entry_price - exit_price) * position.quantity
            
        # Calculate realized R
        risk_per_share = abs(position.entry_price - position.stop_price)
        realized_r = pnl / (risk_per_share * position.quantity) if risk_per_share > 0 else 0
        
        # Create expectation and outcome
        expectation = self.create_expectation(position.trade_id, 
                                              Signal(position.direction,
                                                    position.entry_price,
                                                    position.stop_price,
                                                    position.target_price,
                                                    position.entry_time))
        
        holding_bars = int((exit_time - position.entry_time).total_seconds() / 60)
        
        outcome = TradeOutcome(
            trade_id=position.trade_id,
            realized_R=realized_r,
            actual_holding_period=holding_bars,
            realized_pnl=pnl,
            regime_at_entry="UNKNOWN",  # Can be enhanced with regime tracking
            regime_at_exit="UNKNOWN",
            max_favorable_excursion_R=position.mfe_r,
            max_adverse_excursion_R=position.mae_r,
            exit_reason=reason
        )
        
        # Record to TestAccount
        self.account.on_trade_closed(pnl, exit_time, expectation, outcome, entry_time=position.entry_time, symbol=position.symbol)
        
        # Execute via Broker if available
        if self.broker:
            action = "SELL" if position.direction == "LONG" else "BUY"
            self.broker.send_order(position.symbol, action, position.quantity, exit_price)
        
        # Remove from positions
        self.positions.remove(position)

    def update_position_excursions(self, position: Position, current_price: float):
        """Update MFE and MAE for position"""
        risk_per_share = abs(position.entry_price - position.stop_price)
        
        if position.direction == "LONG":
            current_r = (current_price - position.entry_price) / risk_per_share
        else:
            current_r = (position.entry_price - current_price) / risk_per_share
            
        position.mfe_r = max(position.mfe_r, current_r)
        position.mae_r = min(position.mae_r, current_r)
        position.current_price = current_price
