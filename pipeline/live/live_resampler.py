import pandas as pd
import numpy as np

class LiveResampler:
    def __init__(self, interval_min=5):
        self.interval = interval_min
        self.buffer = {} # symbol -> list of 1m bars
        
    def push(self, symbol, bar):
        """
        bar: dict {dt, open, high, low, close, volume}
        """
        if symbol not in self.buffer:
            self.buffer[symbol] = []
            
        self.buffer[symbol].append(bar)
        
    def check_closure(self, current_dt):
        """
        Checks if the 5m bar is closed based on current_dt.
        Returns dict of closed bars: {symbol: {dt, open, high, low, close, volume}}
        """
        # Logic: If current_dt minute % 5 == 0, previous block is done?
        # NO. We need robust logic.
        # If we receive 09:05:00, the 09:00~09:04 bar is effectively done?
        # Wait, typical 1m data "09:05:00" means 09:04:00~09:05:00?
        # Let's assume input bar 'dt' is the END time of the 1m bar.
        # If dt is 09:05:00, then 09:00:00~09:05:00 is complete.
        
        closed_bars = {}
        
        if current_dt.minute % self.interval == 0:
            for sym, bars in self.buffer.items():
                if not bars: continue
                
                # Aggregate
                df = pd.DataFrame(bars)
                agg = {
                    'dt': current_dt, # Timestamp of closure
                    'open': df['open'].iloc[0],
                    'high': df['high'].max(),
                    'low': df['low'].min(),
                    'close': df['close'].iloc[-1],
                    'volume': df['volume'].sum()
                }
                closed_bars[sym] = agg
            
            # Clear buffer after closure
            self.buffer = {}
            
        return closed_bars
