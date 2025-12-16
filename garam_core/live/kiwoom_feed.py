# garam_core/live/kiwoom_feed.py
from __future__ import annotations
from typing import List, Dict
import queue
import threading
import pandas as pd
from datetime import datetime

from garam_core.live.interfaces import DataFeed
from garam_core.live.aggregator import MinuteBarAggregator

class KiwoomDataFeed(DataFeed):
    def __init__(self, aggregator: MinuteBarAggregator):
        self.aggregator = aggregator
        self._symbols: List[str] = []
        self._bar_queue: "queue.Queue[Dict[str, pd.Series]]" = queue.Queue()
        self._stop = False
        self._thread = None

    def subscribe(self, symbols: List[str]) -> None:
        self._symbols = symbols
        # NOTE: Registration to Kiwoom happens via Wrapper, 
        # usually orchestrated by main script
        pass

    def _on_tick_from_kiwoom(self, symbol: str, price: float, volume: int, ts: datetime):
        tick = {"ts": pd.Timestamp(ts), "price": float(price), "volume": int(volume)}
        self.aggregator.on_tick(symbol, tick)

        bars = self.aggregator.pop_completed_bars(now_ts=pd.Timestamp(ts))
        if bars:
            self._bar_queue.put(bars)

    def get_next_bar(self) -> Dict[str, pd.Series]:
        if self._stop:
            return {}
        try:
            # 60s timeout to allow periodic checks
            bars = self._bar_queue.get(timeout=60.0)
            return bars
        except queue.Empty:
            return {}

    def stop(self):
        self._stop = True
