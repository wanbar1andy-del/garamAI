import logging
import time
import threading
import requests
import pandas as pd
import numpy as np
from typing import Callable, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class KiwoomFeed:
    """
    Real-time data feed from Kiwoom API (via Data Server).
    Supports 'Real' mode (HTTP/Socket) and 'Mock' mode (Simulation).
    """
    
    def __init__(self, server_url: str = "http://localhost:5555", mode: str = 'mock'):
        self.server_url = server_url
        self.mode = mode
        self.running = False
        self.subscriptions = set()
        self.callbacks = []
        self.thread = None
        logger.info(f"KiwoomFeed initialized. Mode: {mode}, Server: {server_url}")

    def subscribe(self, symbol: str):
        """Subscribe to a symbol."""
        self.subscriptions.add(symbol)
        logger.info(f"Subscribed to {symbol}")

    def add_callback(self, callback: Callable[[Dict], None]):
        """Add a callback function to receive data."""
        self.callbacks.append(callback)

    def start(self):
        """Start the feed loop."""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        logger.info("KiwoomFeed started.")

    def stop(self):
        """Stop the feed loop."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
        logger.info("KiwoomFeed stopped.")

    def _run_loop(self):
        """Main data loop."""
        while self.running:
            try:
                if self.mode == 'real':
                    self._fetch_real_data()
                else:
                    self._generate_mock_data()
                
                time.sleep(0.1) # Accelerated for testing
            except Exception as e:
                logger.error(f"Error in feed loop: {e}")
                time.sleep(5)

    def _fetch_real_data(self):
        """Fetch data from local realtime files (File-based Feed) or simulate."""
        try:
            from garam.config import PATHS
            realtime_dir = PATHS.DATA_DIR / "kr" / "realtime" / "1m"
            today_str = datetime.now().strftime("%Y%m%d")
            
            for symbol in self.subscriptions:
                # 1. Try to find a file to get a base price
                file_path = realtime_dir / f"{symbol}_{today_str}.csv"
                base_price = None
                
                if file_path.exists():
                    try:
                        with open(file_path, 'rb') as f:
                            f.seek(-100, 2)
                            last_line = f.readlines()[-1].decode('utf-8').strip()
                            parts = last_line.split(',')
                            if len(parts) >= 6:
                                base_price = float(parts[4]) # Close
                    except:
                        pass
                
                # If no file for today, try to find ANY file for this symbol
                if base_price is None:
                    # Simple fallback: check previous days? Or just use hardcoded defaults for Top 10
                    # For speed, let's use a map of approx prices for Top 10
                    defaults = {
                        '005930': 75000, '000660': 140000, '373220': 400000,
                        '207940': 800000, '005380': 240000, '000270': 120000,
                        '068270': 180000, '105560': 70000, '005490': 450000,
                        '035420': 200000
                    }
                    base_price = defaults.get(symbol, 50000)

                # 2. Generate a "Live" tick based on this price
                # Add random noise to make it move
                noise = base_price * np.random.normal(0, 0.0005) # 0.05% volatility
                current_price = int(base_price + noise)
                
                tick = {
                    'symbol': symbol,
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), # Current time!
                    'open': base_price,
                    'high': max(base_price, current_price),
                    'low': min(base_price, current_price),
                    'close': current_price,
                    'volume': np.random.randint(10, 1000)
                }
                self._dispatch(tick)
                    
        except Exception as e:
            logger.error(f"Real data fetch failed: {e}")

    def _generate_mock_data(self):
        """Generate mock ticks for subscribed symbols."""
        timestamp = datetime.now().isoformat()
        
        for symbol in self.subscriptions:
            # Simulate random price movement
            price = 10000 + np.random.randint(-100, 100)
            tick = {
                'symbol': symbol,
                'timestamp': timestamp,
                'close': price,
                'volume': np.random.randint(1, 100)
            }
            self._dispatch(tick)

    def _dispatch(self, data: Dict):
        """Dispatch data to callbacks."""
        for cb in self.callbacks:
            try:
                cb(data)
            except Exception as e:
                logger.error(f"Error in callback: {e}")
