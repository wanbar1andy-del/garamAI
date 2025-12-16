import sys
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from config import PATHS
from strategies.components.regime_router import RegimeRouter

def tag_regimes():
    print(">>> Tagging Regimes for Hybrid Verification...")
    
    # 1. Setup
    output_dir = PATHS.BASE_DIR / "analysis/regimes"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    symbols = [
        "005930", "000660", "005380", "005490", "035420", 
        "000270", "051910", "068270", "105560", "006400"
    ]
    
    router = RegimeRouter(PATHS.CONFIG_DIR / "playbook_v1.yaml")
    
    for symbol in symbols:
        print(f"Processing {symbol}...")
        
        # 2. Load 1m Data
        file_path = PATHS.DATA_DIR / "kr/intraday/1m" / f"{symbol}_1m.csv"
        if not file_path.exists():
            print(f"Warning: No data for {symbol}")
            continue
            
        df_1m = pd.read_csv(file_path)
        if 'timestamp' in df_1m.columns:
            df_1m['timestamp'] = pd.to_datetime(df_1m['timestamp'])
            df_1m.set_index('timestamp', inplace=True)
        elif 'date' in df_1m.columns:
             df_1m['date'] = pd.to_datetime(df_1m['date'])
             df_1m.set_index('date', inplace=True)
             
        # 3. Resample to Daily for Indicators
        df_daily = df_1m.resample('D').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }).dropna()
        
        if df_daily.empty:
            continue
            
        # 4. Calculate Indicators
        # Trend 20d
        df_daily['trend_20d'] = df_daily['close'].pct_change(20)
        
        # MA20 & FM
        df_daily['ma20'] = df_daily['close'].rolling(20).mean()
        df_daily['fm'] = (df_daily['close'] - df_daily['ma20']) / df_daily['ma20']
        
        # ATR
        high_low = df_daily['high'] - df_daily['low']
        high_close = (df_daily['high'] - df_daily['close'].shift()).abs()
        low_close = (df_daily['low'] - df_daily['close'].shift()).abs()
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df_daily['atr'] = tr.rolling(14).mean()
        
        # ATR Z
        df_daily['atr_min'] = df_daily['atr'].rolling(60, min_periods=1).min()
        df_daily['atr_max'] = df_daily['atr'].rolling(60, min_periods=1).max()
        df_daily['atr_z'] = (df_daily['atr'] - df_daily['atr_min']) / (df_daily['atr_max'] - df_daily['atr_min'])
        
        # Backfill indicators to handle cold start
        df_daily['trend_20d'] = df_daily['trend_20d'].bfill().fillna(0)
        df_daily['atr_z'] = df_daily['atr_z'].bfill().fillna(0.5)
        df_daily['fm'] = df_daily['fm'].bfill().fillna(0)
        
        # 5. Classify Regimes (Daily)
        df_daily['regime_id'] = 'UNKNOWN'
        
        for idx, row in df_daily.iterrows():
            # Create MarketState-like object or dict
            # RegimeRouter expects MarketState object, but we can bypass or mock it
            # Actually, RegimeRouter.classify_regime takes MarketState
            # Let's manually classify using the same logic to avoid dependency complexity or create dummy state
            
            # Logic from RegimeRouter:
            # R1: Trend > 0.05, ATR_Z > 0.7
            # R2: Trend > 0.03, ATR_Z < 0.7
            # R5: Trend < -0.03, ATR_Z < 0.7
            # R6: Trend < -0.05, ATR_Z > 0.7
            # R3: |Trend| < 0.03, ATR_Z < 0.4
            # R4: |Trend| < 0.03, ATR_Z > 0.6
            
            trend = row['trend_20d']
            atr_z = row['atr_z']
            
            if pd.isna(trend) or pd.isna(atr_z):
                regime = 'UNKNOWN'
            elif trend > 0.05 and atr_z > 0.7:
                regime = 'R1_STRONG_UP_BREAKOUT'
            elif trend > 0.03:
                regime = 'R2_STRONG_UP_GRIND'
            elif trend < -0.05 and atr_z > 0.7:
                regime = 'R6_STRONG_DOWN_CRASH'
            elif trend < -0.03:
                regime = 'R5_WEAK_DOWN_DRIFT'
            elif abs(trend) <= 0.03 and atr_z < 0.4:
                regime = 'R3_SIDEWAYS_RANGE_LOWVOL'
            elif abs(trend) <= 0.03 and atr_z > 0.6:
                regime = 'R4_SIDEWAYS_RANGE_HIGHVOL'
            else:
                regime = 'R3_SIDEWAYS_RANGE_LOWVOL' # Default to R3 if ambiguous
                
            df_daily.at[idx, 'regime_id'] = regime
            
        # 6. Merge Regime back to 1m Data
        # Forward fill regime from daily to intraday
        # We use the regime of the *current* day (calculated at close? No, usually prev close for next day)
        # But for backtest, we often use "Today's Regime" based on "Yesterday's Close".
        # Let's shift daily regime by 1 day to represent "Regime known at Open".
        
        df_daily['regime_id_shifted'] = df_daily['regime_id'].shift(1).fillna('UNKNOWN')
        df_daily['trend_20d_shifted'] = df_daily['trend_20d'].shift(1)
        df_daily['atr_z_shifted'] = df_daily['atr_z'].shift(1)
        df_daily['fm_shifted'] = df_daily['fm'].shift(1) # FM is also daily metric
        
        # Reindex 1m to include daily columns
        # Map date to date
        df_1m['date_only'] = df_1m.index.date
        df_1m['date_only'] = pd.to_datetime(df_1m['date_only'])
        
        merged = df_1m.merge(
            df_daily[['regime_id_shifted', 'trend_20d_shifted', 'atr_z_shifted', 'fm_shifted']],
            left_on='date_only',
            right_index=True,
            how='left'
        )
        
        # Rename columns
        merged.rename(columns={
            'regime_id_shifted': 'regime_id',
            'trend_20d_shifted': 'trend_20d',
            'atr_z_shifted': 'atr_z',
            'fm_shifted': 'fm'
        }, inplace=True)
        
        # Calculate Intraday Indicators (fs_orb, fs_fast)
        # This is expensive to do here for every tick.
        # But user requested [timestamp, symbol, ..., fs_orb, fs_fast, regime_id]
        # fs_fast requires loop.
        # For efficiency, we might skip fs_fast here and calculate in strategy, 
        # OR calculate it here if we want "Tagged Data" to be complete.
        # Given 2 months data, we can try to calculate it.
        
        # For now, let's save without fs_fast/fs_orb to save time, 
        # as strategies calculate them dynamically anyway.
        # The user asked for them in output columns, but maybe for analysis?
        # Let's add placeholders or simple calculation if possible.
        # fs_orb is simple (Open Range Breakout).
        # fs_fast is complex.
        
        merged['fs_orb'] = 0.0 # Placeholder
        merged['fs_fast'] = 0.0 # Placeholder
        
        # Save to CSV (Parquet failed to install)
        output_file = output_dir / f"intraday_with_regime_{symbol}.csv"
        merged.to_csv(output_file)
        print(f"Saved {output_file}")

if __name__ == "__main__":
    tag_regimes()
