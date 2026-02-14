from typing import Dict, Any, Optional
from .envelope import RealtimeEvent, EventType

class RealtimeAdapter:
    """
    Adapts RealtimeEvents to Engine-compatible (Replay-Schema) structures.
    """
    
    def to_replay_evt(self, event: RealtimeEvent) -> Optional[Dict[str, Any]]:
        """
        Converts a RealtimeEvent (BAR) into the dictionary format expected by the Replay Loop.
        Returns None if event is not a BAR or invalid.
        """
        if event.event_type != EventType.BAR:
            return None

        # Ensure valid before conversion
        event.validate()
        
        p = event.payload
        sym = event.symbol

        # Replay Schema: {ts, symbol, open, high, low, close, volume}
        # Note: Replay uses localized datetime usually, RealtimeEvent has timezone aware?
        # run_live_paper.py expects standard datetime objects.
        
        return {
            "ts": event.event_time,      # Use Source Time
            "symbol": sym,
            "open": float(p["open"]),
            "high": float(p["high"]),
            "low": float(p["low"]),
            "close": float(p["close"]),
            "volume": float(p["volume"]),
        }

    def to_minute_bars(self, event: RealtimeEvent) -> Optional[Dict[str, Dict[str, Any]]]:
        """
        Helper to create the 'minute_bars' dictionary: {symbol: {OHLCV...}}
        Used when inject directly into logic that expects bulk bars (though usually list of 1).
        """
        evt = self.to_replay_evt(event)
        if not evt:
            return None
        sym = evt["symbol"]
        return {sym: evt}
