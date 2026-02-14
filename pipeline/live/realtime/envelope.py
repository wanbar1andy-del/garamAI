from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Any, Optional
import uuid

class EventType(Enum):
    BAR = "BAR"
    TICK = "TICK"
    ORDER_UPDATE = "ORDER_UPDATE"
    HEARTBEAT = "HEARTBEAT"
    CONTROL = "CONTROL"

def _utcnow():
    return datetime.now(timezone.utc)

@dataclass
class RealtimeEvent:
    event_type: EventType
    event_time: datetime                 # source/exchange time
    payload: Dict[str, Any]

    event_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    ingest_time: datetime = field(default_factory=_utcnow)
    symbol: Optional[str] = None
    seq: Optional[int] = None            # per-partition ordering/recovery hook
    # partition: Optional[int] = None    # Reserved for Kafka
    # offset: Optional[int] = None       # Reserved for Kafka

    def validate(self) -> bool:
        """
        Strict validation for Phase 30-2.
        """
        if not self.event_id:
            raise ValueError("Missing event_id")

        if not isinstance(self.event_type, EventType):
            raise ValueError(f"Invalid event_type: {self.event_type}")

        if not isinstance(self.event_time, datetime):
            raise ValueError("event_time must be datetime")

        if not isinstance(self.ingest_time, datetime):
            raise ValueError("ingest_time must be datetime")

        if not isinstance(self.payload, dict):
            raise ValueError("payload must be dict")

        if self.event_type == EventType.BAR:
            if not self.symbol:
                raise ValueError("BAR requires symbol")

            required = {"open", "high", "low", "close", "volume"}
            missing = required - set(self.payload.keys())
            if missing:
                raise ValueError(f"BAR payload missing keys: {missing}")
                
        # Optional: Sanity check (Event time should not be significantly in future)
        # diff = (self.event_time - self.ingest_time).total_seconds()
        # if diff > 3600:
        #    raise ValueError(f"Event time is too far in future: {diff}s")

        return True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "event_time": self.event_time.isoformat(),
            "ingest_time": self.ingest_time.isoformat(),
            "symbol": self.symbol,
            "seq": self.seq,
            "payload": self.payload
        }
