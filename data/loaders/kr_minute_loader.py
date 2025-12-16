import pandas as pd
import logging
from pathlib import Path
from typing import Optional
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config import PATHS

logger = logging.getLogger(__name__)

class KRMinuteLoader:
    """
    Handles loading of KR intraday data collected from Kiwoom.
    Reads CSV files from GARAM_Data/kr/intraday/{interval}m/
    """
    
    def __init__(self):
        self.base_path = PATHS.KR_ROOT / "intraday"
        
    def load(self, symbol: str, interval: str = "1") -> Optional[pd.DataFrame]:
        """
        Load intraday data for a symbol.
        
        Args:
            symbol: Stock code (6 digits)
            interval: Minute interval ("1", "3", "5", "15", "30", "60")
            
        Returns:
            DataFrame with DatetimeIndex and columns [open, high, low, close, volume]
            or None if file not found.
        """
        try:
            file_path = self.base_path / f"{interval}m" / f"{symbol}_{interval}m.csv"
            
            if not file_path.exists():
                # Fallback patterns
                patterns = [
                    PATHS.HISTORY_DIR / f"{symbol}_{interval}m.csv",
                    PATHS.HISTORY_DIR / f"{interval}m" / f"{symbol}_{interval}m.csv",
                    Path("g:/내 드라이브/garamdata/history/minute") / f"{symbol}_{interval}m.csv"
                ]
                
                found = False
                for p in patterns:
                    if p.exists():
                        file_path = p
                        found = True
                        break
                
                if not found:
                    logger.warning(f"Data file not found for {symbol} ({interval}m)")
                    return None
                
            # Read CSV
            df = pd.read_csv(file_path)
            
            # Parse timestamp/date
            date_col = None
            for col in ['timestamp', 'date', '일자']:
                if col in df.columns:
                    date_col = col
                    break
            
            if date_col:
                df['timestamp'] = pd.to_datetime(df[date_col])
                df.set_index('timestamp', inplace=True)
                df.sort_index(inplace=True)
                
            # Ensure numeric columns
            numeric_cols = ['open', 'high', 'low', 'close', 'volume']
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                    
            logger.debug(f"Loaded {len(df)} rows for {symbol} ({interval}m)")
            return df
            
        except Exception as e:
            logger.error(f"Error loading data for {symbol}: {e}")
            return None
