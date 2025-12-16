import pandas as pd
import numpy as np
import json

# Import technical indicators
# Assuming we have them in garam.features.library or we can implement simple versions here
# to ensure self-containment and avoid dependency hell during this phase.
# The user mentioned `features.library.momentum`. Let's try to import, if fail, implement.

try:
    from garam.features.library.momentum import rsi, macd, bollinger_bands
except ImportError:
    # Simple implementations for fallback
    def rsi(series, window=14):
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    def macd(series, fast=12, slow=26, signal=9):
        ema_fast = series.ewm(span=fast, adjust=False).mean()
        ema_slow = series.ewm(span=slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        hist = macd_line - signal_line
        return macd_line, signal_line, hist

    def bollinger_bands(series, window=20, num_std=2):
        ma = series.rolling(window=window).mean()
        std = series.rolling(window=window).std()
        upper = ma + (std * num_std)
        lower = ma - (std * num_std)
        return upper, ma, lower

CATEGORICAL_COLS = ["symbol", "strategy_id", "regime_ml"]

def build_features(df_raw: pd.DataFrame) -> pd.DataFrame:
    """
    Transforms raw dataset (Signals + Price) into Feature Matrix (X).
    """
    df = df_raw.copy()
    
    # 1. Parse 'features_json' if it exists and is a string
    # The signal logger saves a snapshot of features at that time.
    # We should prioritize using those "point-in-time" features if available,
    # as they represent exactly what the strategy saw.
    # However, for training, we might want to re-calculate or add MORE features.
    # Let's extract what's in JSON first.
    
    if 'features_json' in df.columns:
        # This is slow for large datasets, but fine for now.
        # Vectorized approach:
        # df_json = pd.json_normalize(df['features_json'].apply(json.loads))
        # But we need to handle potential errors or NaNs.
        pass

    # 2. Calculate Technical Indicators on the attached price columns
    # Note: df_raw usually has 'close', 'volume' etc from the merge.
    # But wait, the merge in dataset_builder only attached the *current* bar's price.
    # To calculate RSI/MACD, we need history.
    # Ideally, 'features_json' ALREADY contains the values (rsi, ma_20, etc.) computed by StreamProcessor.
    # So we should rely on 'features_json' for the core indicators.
    
    # Let's expand 'features_json' into columns
    if 'features_json' in df.columns:
        def parse_safe(x):
            try:
                return json.loads(x) if isinstance(x, str) else {}
            except:
                return {}
        
        expanded = df['features_json'].apply(parse_safe).apply(pd.Series)
        # Avoid column collision
        expanded = expanded.add_prefix('feat_')
        df = pd.concat([df, expanded], axis=1)

    # 3. Regime Encoding
    # Simple One-Hot or Label Encoding
    # For XGBoost, Category type is often supported natively or we use int.
    if 'regime_ml' in df.columns:
        df['regime_ml'] = df['regime_ml'].astype('category')
        
    if 'strategy_id' in df.columns:
        df['strategy_id'] = df['strategy_id'].astype('category')

    # 4. Clean up
    # Drop non-feature columns that are not needed for training
    # Keep labels!
    # Also drop raw price columns as they are non-stationary and bad for ML
    cols_to_drop = ['features_json', 'reason', 'timestamp', 'open', 'high', 'low', 'close', 'volume', 'price'] 
    df = df.drop(columns=[c for c in cols_to_drop if c in df.columns], errors='ignore')
    
    # Handle NaNs
    # df = df.fillna(0) # Risky for some features
    
    return df
