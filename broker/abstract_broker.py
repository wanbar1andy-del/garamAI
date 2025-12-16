from abc import ABC, abstractmethod
from typing import Dict, Optional

class AbstractBroker(ABC):
    """
    Abstract base class for all brokers (Real, Paper, Simulation).
    """
    
    is_live: bool = False

    @abstractmethod
    def get_balance(self) -> float:
        """Get current cash balance."""
        pass

    @abstractmethod
    def get_position(self, symbol: str) -> Optional[Dict]:
        """Get current position for a symbol."""
        pass

    @abstractmethod
    def send_order(self, symbol: str, action: str, qty: int, price: float) -> str:
        """Send an order and return order ID."""
        pass

    @abstractmethod
    def cancel_order(self, order_id: str) -> bool:
        """Cancel an order."""
        pass
