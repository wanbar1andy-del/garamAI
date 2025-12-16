# garam_core/live/aggregator.py
from __future__ import annotations
import pandas as pd
from typing import Dict, Any

class MinuteBarAggregator:
    """
    Aggregates realtime ticks into Minute Bars.
    """
    def __init__(self, timeframe: str = "minute", bar_interval: int = 1):
        self.timeframe = timeframe
        self.bar_interval = bar_interval
        self.buffers: Dict[str, pd.DataFrame] = {}

    def on_tick(self, symbol: str, tick: Dict[str, Any]):
        """
        tick: {"ts": Timestamp, "price": float, "volume": int, ...}
        """
        df = self.buffers.get(symbol)
        row = pd.DataFrame([tick]).set_index("ts")
        if df is None:
            df = row
        else:
            df = pd.concat([df, row])
        self.buffers[symbol] = df

    def pop_completed_bars(self, now_ts) -> Dict[str, pd.Series]:
        """
        Returns 1-min bars completed before now_ts (floor to minute).
        """
        out: Dict[str, pd.Series] = {}
        cutoff = now_ts.floor("T")  # truncate to minute

        for sym, df in list(self.buffers.items()):
            if df.empty:
                continue

            # Resample to bar_interval minutes
            # Using 'closed=left', 'label=left' semantics usually
            rule = f"{self.bar_interval}T"
            
            # To handle partials correctly in pandas resample for realtime is tricky.
            # Simplified approach: Filter df for data < cutoff, then resample THAT.
            
            ready_data = df[df.index < cutoff]
            if ready_data.empty:
                continue
                
            # Aggregate ready_data
            bar_df = ready_data.resample(rule).agg({
                "price": ["first", "max", "min", "last"],
                "volume": "sum",
            })
            bar_df.columns = ["open", "high", "low", "close", "volume"]
            
            # We assume ready_data contains potentially multiple bars if lag occurred,
            # but usually just the last one is relevant for live logic?
            # Or we return ALL completed bars? 
            # LiveRunner expects "latest completed". We'll return the last one.
            
            if not bar_df.empty:
                out[sym] = bar_df.iloc[-1]
                
                # Clear buffer up to used data
                last_ts = ready_data.index.max()
                # Keep data strictly AFTER the ready_data range
                # Actually safer to keep data >= cutoff
                self.buffers[sym] = df[df.index >= cutoff]
        
        return out
