import pandas as pd
import numpy as np
from typing import Optional

# We need a way to load price data. 
# In the user's design, this function takes a loader.
# For simplicity in this phase (and given we might not have the full loader infrastructure perfectly set up for all contexts),
# I'll assume we can pass a price DataFrame or a loader object.
# Let's stick to the user's signature but make it flexible.

def add_forward_R_label(
    df_signals: pd.DataFrame,
    price_loader=None, # Type: KRMinuteLoader or similar
    horizon_bars: int = 30,
    target_R: float = 1.5,
    price_col: str = "close"
) -> pd.DataFrame:
    """
    Calculates 'Realized R' for each signal by looking ahead 'horizon_bars'.
    
    Logic:
    1. For each signal at time T, get price data from T+1 to T+horizon.
    2. Calculate Max PnL (High - Entry) and Max Drawdown (Entry - Low) for Longs.
       (Reverse for Shorts if we had them, but currently mostly Long).
    3. Define 'Best Return' within horizon.
    4. Label 'good_trade' if Best Return > Threshold.
    
    Args:
        df_signals: DataFrame with 'timestamp', 'symbol', 'price' (entry price).
        price_loader: Object with .load(symbol, interval) method returning DataFrame with datetime index.
        horizon_bars: Number of bars to look ahead.
        target_R: Not strictly used if we just return raw return, but useful for binary label.
                  Here we use a simple % threshold for 'good_trade'.
    """
    df = df_signals.copy()
    labels_r = []
    labels_good = []
    
    # Pre-load prices if possible to avoid repeated IO?
    # For now, follow the loop pattern.
    
    for idx, row in df.iterrows():
        ts = row.name if isinstance(row.name, pd.Timestamp) else pd.to_datetime(row['timestamp'])
        symbol = row['symbol']
        entry_price = row.get('price')
        
        # If entry price missing, skip
        if pd.isna(entry_price):
            labels_r.append(None)
            labels_good.append(0)
            continue
            
        # Load price data for this symbol
        # Optimization: In a real large-scale system, we'd cache this or pass it in.
        if price_loader:
            df_price = price_loader.load(symbol=symbol, interval="1")
        else:
            # Fallback or Error
            labels_r.append(None)
            labels_good.append(0)
            continue
            
        if df_price is None or df_price.empty:
            labels_r.append(None)
            labels_good.append(0)
            continue
            
        # Ensure sorted
        df_price = df_price.sort_index()
        
        # Slice future
        # Use searchsorted or direct slicing if index is datetime
        try:
            # Get integer location of timestamp
            # This is approximate if exact TS doesn't exist
            # future = df_price.loc[ts:].iloc[1:horizon_bars+1]
            
            # More robust: find insertion point
            start_idx = df_price.index.searchsorted(ts)
            if start_idx >= len(df_price):
                labels_r.append(None)
                labels_good.append(0)
                continue
                
            # future window: start_idx + 1 to start_idx + 1 + horizon
            future = df_price.iloc[start_idx+1 : start_idx+1+horizon_bars]
            
            if future.empty:
                labels_r.append(None)
                labels_good.append(0)
                continue
                
            # Calculate Returns (Long Only assumption for now)
            # TODO: Handle Short signals if signal column is -1
            signal = row.get('signal', 1)
            if signal == 0: 
                # No trade
                labels_r.append(0.0)
                labels_good.append(0)
                continue
                
            if signal == 1:
                max_price = future['high'].max()
                best_ret = (max_price - entry_price) / entry_price
            elif signal == -1:
                min_price = future['low'].min()
                best_ret = (entry_price - min_price) / entry_price
            else:
                best_ret = 0.0
                
            labels_r.append(best_ret)
            
            # Binary Label: Did it hit at least 0.5% profit?
            # Or use target_R logic if we had ATR. 
            # Let's use a fixed threshold for now: 0.2% (scalping) or 0.5%
            threshold = 0.002 # 0.2%
            labels_good.append(1 if best_ret >= threshold else 0)
            
        except Exception as e:
            # print(f"Error labeling {ts} {symbol}: {e}")
            labels_r.append(None)
            labels_good.append(0)

    df['label_max_return'] = labels_r
    df['label_good_trade'] = labels_good
    
    return df
