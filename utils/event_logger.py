"""
Unified Event Logger for GARAM Trading System
Provides structured JSON logging for all trading events
"""

import json
import logging
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
import uuid

# Import centralized paths
try:
    from garam.config import PATHS
    DEFAULT_LOG_DIR = str(PATHS.LOGS_DIR)
except ImportError:
    DEFAULT_LOG_DIR = "C:/garam/GARAM_Data/logs"


class EventLogger:
    """
    Unified event logger with structured JSON output.
    
    Supports 4 event types:
    - MarketEvent: Market data + computed features
    - DecisionEvent: Trading signals and strategy decisions
    - OrderEvent: Order submissions
    - FillEvent: Order executions
    """
    
    def __init__(self, mode: str = "SHADOW", log_dir: str = None):
        self.mode = mode
        self.log_dir = Path(log_dir) if log_dir else Path(DEFAULT_LOG_DIR)
        self.session_id = str(uuid.uuid4())[:8]
        
        # Create log directory
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup loggers
        self.setup_loggers()
        
    def setup_loggers(self):
        """Setup separate loggers for each event type"""
        
        # Main structured logger (JSON)
        self.structured_logger = logging.getLogger(f'garam.events.{self.mode}')
        self.structured_logger.setLevel(logging.INFO)
        self.structured_logger.handlers.clear()
        
        # File handler - one file per day
        log_file = self.log_dir / f"{self.mode.lower()}_events_{datetime.now().strftime('%Y%m%d')}.jsonl"
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=50*1024*1024,  # 50MB
            backupCount=10
        )
        file_handler.setLevel(logging.INFO)
        
        # Console handler for development
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatters
        class JSONFormatter(logging.Formatter):
            def format(self, record):
                return record.getMessage()
        
        file_handler.setFormatter(JSONFormatter())
        console_handler.setFormatter(JSONFormatter())
        
        self.structured_logger.addHandler(file_handler)
        self.structured_logger.addHandler(console_handler)
        
    def _log_event(self, event: Dict[str, Any]):
        """Internal method to log event as JSON"""
        # Add common fields
        event['session_id'] = self.session_id
        event['mode'] = self.mode
        
        # Ensure timestamp
        if 'timestamp' not in event:
            event['timestamp'] = datetime.now().isoformat()
        
        # Log as JSON line
        self.structured_logger.info(json.dumps(event, ensure_ascii=False))
    
    def log_market_event(
        self,
        symbol: str,
        market_data: Dict[str, float],
        computed_features: Optional[Dict[str, float]] = None,
        tags: Optional[Dict[str, Any]] = None
    ):
        """
        Log market data event
        
        Args:
            symbol: Trading symbol
            market_data: Price, volume, bid, ask
            computed_features: Trend, volatility, fear scores
            tags: Additional metadata
        """
        event = {
            'event_type': 'market_event',
            'timestamp': datetime.now().isoformat(),
            'symbol': symbol,
            'market_data': market_data,
            'computed_features': computed_features or {},
            'tags': tags or {}
        }
        self._log_event(event)
    
    def log_decision_event(
        self,
        symbol: str,
        market_state: Dict[str, str],
        condition_set_id: str,
        strategy_id: str,
        signal: str,
        confidence: float,
        reason: List[str],
        tags: Optional[Dict[str, Any]] = None
    ):
        """
        Log trading decision event
        
        Args:
            symbol: Trading symbol
            market_state: Trend, volatility, regime
            condition_set_id: Active condition set
            strategy_id: Strategy identifier
            signal: BUY/SELL/HOLD
            confidence: Decision confidence (0-1)
            reason: List of reasoning factors
            tags: Additional metadata
        """
        event = {
            'event_type': 'decision_event',
            'timestamp': datetime.now().isoformat(),
            'symbol': symbol,
            'market_state': market_state,
            'condition_set_id': condition_set_id,
            'strategy_id': strategy_id,
            'signal': signal,
            'confidence': confidence,
            'reason': reason,
            'tags': tags or {}
        }
        self._log_event(event)
    
    def log_order_event(
        self,
        order_id: str,
        symbol: str,
        action: str,
        order_type: str,
        quantity: int,
        target_price: Optional[float] = None,
        status: str = "SUBMITTED",
        strategy_id: Optional[str] = None,
        condition_set_id: Optional[str] = None,
        tags: Optional[Dict[str, Any]] = None
    ):
        """
        Log order submission event
        
        Args:
            order_id: Unique order identifier
            symbol: Trading symbol
            action: BUY/SELL
            order_type: MARKET/LIMIT
            quantity: Order quantity
            target_price: Target price for limit orders
            status: Order status
            strategy_id: Strategy that generated the order
            condition_set_id: Active condition set
            tags: Additional metadata
        """
        event = {
            'event_type': 'order_event',
            'timestamp': datetime.now().isoformat(),
            'order_id': order_id,
            'symbol': symbol,
            'action': action,
            'order_type': order_type,
            'quantity': quantity,
            'target_price': target_price,
            'status': status,
            'strategy_id': strategy_id,
            'condition_set_id': condition_set_id,
            'tags': tags or {}
        }
        self._log_event(event)
    
    def log_fill_event(
        self,
        order_id: str,
        fill_id: str,
        symbol: str,
        filled_qty: int,
        fill_price: float,
        commission: float,
        slippage: float = 0,
        pnl: Optional[float] = None,
        tags: Optional[Dict[str, Any]] = None
    ):
        """
        Log order fill event
        
        Args:
            order_id: Original order ID
            fill_id: Unique fill identifier
            symbol: Trading symbol
            filled_qty: Filled quantity
            fill_price: Execution price
            commission: Trading commission
            slippage: Price slippage
            pnl: Realized P&L (for closing trades)
            tags: Additional metadata
        """
        event = {
            'event_type': 'fill_event',
            'timestamp': datetime.now().isoformat(),
            'order_id': order_id,
            'fill_id': fill_id,
            'symbol': symbol,
            'filled_qty': filled_qty,
            'fill_price': fill_price,
            'commission': commission,
            'slippage': slippage,
            'pnl': pnl,
            'tags': tags or {}
        }
        self._log_event(event)
    
    def log_error(
        self,
        error_type: str,
        message: str,
        severity: str = "WARNING",
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Log error/exception event
        
        Args:
            error_type: Type of error
            message: Error message
            severity: CRITICAL/WARNING/INFO
            context: Additional context
        """
        event = {
            'event_type': 'error_event',
            'timestamp': datetime.now().isoformat(),
            'error_type': error_type,
            'message': message,
            'severity': severity,
            'context': context or {}
        }
        self._log_event(event)
    
    def get_session_summary(self) -> Dict[str, Any]:
        """
        Get summary of current session
        
        Returns:
            Session metadata and statistics
        """
        return {
            'session_id': self.session_id,
            'mode': self.mode,
            'log_dir': str(self.log_dir),
            'started_at': datetime.now().isoformat()
        }


# Convenience function
def get_event_logger(mode: str = "SHADOW") -> EventLogger:
    """Get or create event logger for specified mode"""
    return EventLogger(mode=mode)


if __name__ == "__main__":
    # Test the logger
    logger = EventLogger(mode="SHADOW")
    
    # Test market event
    logger.log_market_event(
        symbol="005930",
        market_data={'price': 75000, 'volume': 1000},
        computed_features={'trend_score': 0.8, 'volatility': 0.015}
    )
    
    # Test decision event
    logger.log_decision_event(
        symbol="005930",
        market_state={'trend': 'UP', 'volatility': 'NORMAL'},
        condition_set_id="UP_NORMAL_v1",
        strategy_id="S1_D1",
        signal="BUY",
        confidence=0.85,
        reason=["MA crossover", "Vol normalized"]
    )
    
    print(f"Logger test complete. Session: {logger.session_id}")
