import pandas as pd
import logging
from typing import Dict, List, Any, Callable
from .factory import FeatureFactory

logger = logging.getLogger(__name__)

class StreamProcessor:
    """
    Real-time feature processing engine.
    Buffers ticks -> Updates DataFrame -> Computes Features -> Emits Signal.
    """
    
    def __init__(self, factory: FeatureFactory, window_size: int = 100):
        self.factory = factory
        self.window_size = window_size
        self.buffers: Dict[str, pd.DataFrame] = {}
        self.configs: Dict[str, List[Dict]] = {}
        logger.info("StreamProcessor initialized.")

    def register_symbol(self, symbol: str, feature_config: List[Dict]):
        """Register a symbol and its feature configuration."""
        self.configs[symbol] = feature_config
        # Initialize empty buffer with required columns
        self.buffers[symbol] = pd.DataFrame(columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        logger.info(f"Registered {symbol} for stream processing.")

    def on_tick(self, tick: Dict) -> Dict[str, Any]:
        """
        Process a new tick.
        Returns the latest feature row if computation was successful.
        """
        symbol = tick['symbol']
        if symbol not in self.buffers:
            return None
            
        # Update Buffer
        # For simplicity in v0, we treat each tick as a "bar" or append to minute bars.
        # Here we assume the feed sends "bars" (or we treat ticks as bars for testing).
        
        new_row = pd.DataFrame([tick])
        # Ensure timestamp is datetime
        if 'timestamp' in new_row.columns:
            new_row['timestamp'] = pd.to_datetime(new_row['timestamp'])
            
        df = self.buffers[symbol]
        df = pd.concat([df, new_row], ignore_index=True)
        
        # Maintain window size
        if len(df) > self.window_size:
            df = df.iloc[-self.window_size:]
            
        self.buffers[symbol] = df
        
        # Compute Features
        if len(df) >= 20: # Minimum size for MA/Vol
            try:
                df_features = self.factory.compute_features(df, self.configs[symbol])
                latest = df_features.iloc[-1].to_dict()
                return latest
            except Exception as e:
                logger.error(f"Stream processing error for {symbol}: {e}")
                return None
                
        return None
