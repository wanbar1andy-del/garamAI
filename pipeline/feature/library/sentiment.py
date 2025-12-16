import pandas as pd
import numpy as np

def calc_news_fear_score(df: pd.DataFrame, news_data: pd.DataFrame = None) -> pd.DataFrame:
    """
    Calculate News Fear Score based on news sentiment and volume.
    If news_data is None, we simulate it based on price drops (VIX proxy) or return a default.
    
    Score range: 0 (Greed) to 100 (Extreme Fear)
    """
    df = df.copy()
    
    if news_data is None:
        # Simulation / Proxy Mode
        # Use "Price Drop" as a proxy for fear
        # If price drops > 2% in short term, fear goes up
        
        # Calculate 5-day return
        df['ret_5d'] = df['close'].pct_change(5)
        
        # Base fear on return: -5% return => 80 fear, +5% => 20 fear
        # Sigmoid-like mapping
        # fear = 50 - (ret_5d * 1000)  (e.g. -0.05 * 1000 = -50 => 50 - (-50) = 100)
        
        df['news_fear_score'] = 50 - (df['ret_5d'] * 500)
        df['news_fear_score'] = df['news_fear_score'].clip(0, 100).fillna(50)
        
        # Add some noise for simulation realism
        noise = np.random.normal(0, 5, size=len(df))
        df['news_fear_score'] = (df['news_fear_score'] + noise).clip(0, 100)
        
        df.drop(columns=['ret_5d'], inplace=True, errors='ignore')
    else:
        # TODO: Implement real news sentiment aggregation
        # 1. Filter news by date
        # 2. Weighted average of sentiment scores
        # 3. Normalize to 0-100
        df['news_fear_score'] = 50.0
        
    return df
