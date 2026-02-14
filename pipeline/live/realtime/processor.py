import heapq
from datetime import datetime, timedelta
from typing import Optional, List, Tuple, Set
from .envelope import RealtimeEvent
from .consumer import RealtimeQueueConsumer

class RealtimeProcessor:
    """
    Robust RealtimeProcessor (Phase 30-2)
    - Dedup: Set (TTL/LRU minimal impl).
    - Order: Min-Heap with Tie-Breaker (counter).
    - Watermark: Based on 'max_event_time_seen' (not wall clock).
    - Backpressure: Drop if buffer > max_buffer.
    """
    def __init__(
        self,
        consumer: RealtimeQueueConsumer,
        watermark_sec: float = 3.0,
        max_buffer: int = 50000,
    ):
        self.consumer = consumer
        self.watermark_sec = watermark_sec
        self.max_buffer = max_buffer

        # Heap stores: (event_time, insert_order_ctr, event)
        self._heap: List[Tuple[datetime, int, RealtimeEvent]] = []
        self._ctr = 0

        self.max_event_time_seen: Optional[datetime] = None

        # Dedup: Simple Set for now (Production should use OrderedDict/LRU)
        self.seen_ids: Set[str] = set()
        self.max_seen_size = 20000

        self.stats = {"in":0, "out":0, "dup":0, "drop":0, "json_err":0}

    def poll(self, current_wall_time: datetime = None) -> Optional[RealtimeEvent]:
        # 'current_wall_time' arg kept for interface compat, but using max_seen internally.
        
        raw = self.consumer.poll(timeout=0.1)
        if raw:
            self.stats["in"] += 1

            # 2nd Validation Defense
            try:
                raw.validate()
            except ValueError:
                self.consumer.commit() # Bad event, skip
                return None

            # Dedup
            if raw.event_id in self.seen_ids:
                self.stats["dup"] += 1
                # Treat as processed (drop) -> commit handled by caller eventually or implicitly?
                # Actually, if we return None, caller loop continues.
                # We should commit here because we consumed it but won't emit it.
                # BUT caller typically commits after processing returned event.
                # If we return None, caller doesn't commit.
                # So we must commit here for the skipped duplicate.
                self.consumer.commit() 
                return None

            self.seen_ids.add(raw.event_id)
            if len(self.seen_ids) > self.max_seen_size:
                self.seen_ids.clear() # Naive reset for now

            # Update Watermark Baseline
            if (self.max_event_time_seen is None) or (raw.event_time > self.max_event_time_seen):
                self.max_event_time_seen = raw.event_time

            # Backpressure / Buffer Limit
            if len(self._heap) >= self.max_buffer:
                self.stats["drop"] += 1
                # Drop incoming (Load Shedding)
                self.consumer.commit()
                return None

            self._ctr += 1
            heapq.heappush(self._heap, (raw.event_time, self._ctr, raw))

        # Emit Logic (Watermark: Max Seen Time)
        if not self._heap or self.max_event_time_seen is None:
            return None

        # Calculate safe threshold
        safe_t = self.max_event_time_seen - timedelta(seconds=self.watermark_sec)

        top_t, _, top_evt = self._heap[0]
        
        if top_t <= safe_t:
            heapq.heappop(self._heap)
            self.stats["out"] += 1
            return top_evt

        return None

    def commit(self) -> None:
        self.consumer.commit()

    def get_lag(self) -> int:
        return len(self._heap)
