import numpy as np
import pandas as pd
import logging

logger = logging.getLogger(__name__)

class SentimentEngine:
    """
    Mock Sentiment Engine for Dual Engine Architecture.
    Simulates KR-FinBERT sentiment scores based on market data proxies.
    
    Tuned for "Optimistic Trend-Following":
    - Positive Trend = Good News (Bias +0.3)
    - Low Volatility + Up = Sustainable Rally (Score +0.5 to +0.8)
    - High Volatility + Down = Panic (Score -0.5 to -1.0)
    """
    
    def __init__(self):
        logger.info("Initializing SentimentEngine (MOCK Mode: Optimistic)...")
        self.mock_mode = True
        
    def analyze_market_sentiment(self, daily_df: pd.DataFrame) -> float:
        """
        Returns a sentiment score between -1.0 (Extreme Fear) and +1.0 (Extreme Greed).
        """
        # Bug Fix: Handle dict passing gracefully, though we expect DataFrame.
        # If dict, assume it's NOT a dataframe and return neutral.
        if daily_df is None or isinstance(daily_df, dict):
            return 0.2 # Slight positive bias if no data
            
        try:
            if daily_df.empty:
                return 0.2
        except AttributeError:
             return 0.2

            
        # 1. Calculate Volatility Proxy (Range)
        high = daily_df['high'].iloc[-1]
        low = daily_df['low'].iloc[-1]
        close = daily_df['close'].iloc[-1]
        prev_close = daily_df['close'].iloc[-2] if len(daily_df) > 1 else close
        
        daily_range_pct = (high - low) / close # Volatility
        
        # 2. Calculate Direction
        ret = (close / prev_close) - 1.0
        
        # 3. Optimistic Sentiment Logic
        base_score = 0.2 # Base Optimism (No news is good news)
        
        if ret > 0.005: # Slight Up -> Positive
            base_score = 0.5
            if ret > 0.03: # Strong Up -> Greed
                base_score = 0.8
        elif ret < -0.01: # Drop -> Fear
            base_score = -0.3
            if ret < -0.03: # Crash -> Panic
                base_score = -0.8
                
        # 4. Volatility Impact
        if daily_range_pct > 0.04: # High Volatility
            if ret < 0:
                base_score -= 0.2 # Fear amplify
            else:
                base_score += 0.1 # Excitement amplify
                
        # 5. Add Noise (Simulate random news)
        noise = np.random.normal(0, 0.05) 
        
        final_score = np.clip(base_score + noise, -1.0, 1.0)
        
        return float(final_score)
