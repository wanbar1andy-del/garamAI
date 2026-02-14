from abc import ABC, abstractmethod
from typing import Optional
from .envelope import RealtimeEvent

class RealtimeQueueConsumer(ABC):
    """
    Abstract Base Class for Realtime Data Consumption.
    Implementations (Kafka, RabbitMQ, FileTail) must follow this contract.
    """
    
    @abstractmethod
    def poll(self, timeout: float = 1.0) -> Optional[RealtimeEvent]:
        """
        Fetch the next valid event from the queue.
        - Must handle deserialization used in Envelope.
        - Must handle loss prevention (at-least-once).
        - Returns None if no event is available within timeout.
        """
        pass
        
    @abstractmethod
    def commit(self) -> None:
        """
        Commit the processed offset/state.
        MUST be called only after the Engine has successfully updated its state.
        """
        pass
        
    @abstractmethod
    def close(self) -> None:
        """
        Clean shutdown of connections.
        """
        pass
