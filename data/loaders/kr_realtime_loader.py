import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import List, Tuple, Dict, Any
import logging

logger = logging.getLogger(__name__)

class KRRealtimeBarLoader:
    def __init__(self, data_root: Path, universe: List[str]):
        self.data_root = data_root
        self.universe = universe
        self.csv_dir = self.data_root / "1m"
        self.last_bar_time = {code: None for code in universe}
        
    def get_new_bars(self) -> List[Tuple[str, Dict[str, Any]]]:
        """
        Check for new bars for all symbols in universe.
        Returns a list of (code, bar_dict).
        """
        new_bars = []
        today_str = datetime.now().strftime("%Y%m%d")
        
        for code in self.universe:
            try:
                # Assuming daily files: code_YYYYMMDD.csv
                file_path = self.csv_dir / f"{code}_{today_str}.csv"
                if not file_path.exists():
                    continue
                    
                # Read CSV safely
                try:
                    df = pd.read_csv(file_path)
                    if df.empty:
                        continue
                    
                    last_row = df.iloc[-1]
                    bar_time = last_row['datetime'] # Assuming datetime column exists
                    
                    if self.last_bar_time[code] != bar_time:
                        self.last_bar_time[code] = bar_time
                        bar = last_row.to_dict()
                        new_bars.append((code, bar))
                except Exception:
                    continue
                    
            except Exception:
                continue
                
        return new_bars

    def get_data_latency(self) -> float:
        """Get latency of the most recent bar across all symbols."""
        latest_ts = None
        today_str = datetime.now().strftime("%Y%m%d")
        
        for code in self.universe:
            file_path = self.csv_dir / f"{code}_{today_str}.csv"
            if not file_path.exists():
                continue
                
            try:
                df = pd.read_csv(file_path)
                if not df.empty:
                    last_ts_str = df.iloc[-1]['datetime']
                    # Format: YYYY-MM-DD HH:MM
                    dt = datetime.strptime(last_ts_str, "%Y-%m-%d %H:%M")
                    if latest_ts is None or dt > latest_ts:
                        latest_ts = dt
            except Exception:
                continue
                
        if latest_ts:
            return (datetime.now() - latest_ts).total_seconds()
            
        return 9999.0
