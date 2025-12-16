from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Dict, Any
import json
import pandas as pd
import logging

# Assuming these exist or we mock them for now if dependencies are missing
# from garam.data.loaders.kr_minute_loader import KRMinuteLoader
# from garam.research.regime.labeler import RegimeLabeler

# For now, let's implement a basic loader inside or assume standard pandas read
# To keep it self-contained as per user request structure

logger = logging.getLogger(__name__)

@dataclass
class DatasetConfig:
    signal_log_dir: Path
    price_data_root: Path
    universe: List[str]
    bar_interval: str = "1min"
    label_horizon_bars: int = 30      # e.g., 30 mins later
    min_history_bars: int = 60        # Min history for labeling
    regime_window_days: int = 60      # For RegimeLabeler

class AIDatasetBuilder:
    """
    Combines Shadow signal logs + Intraday Price Data -> Training DataFrame.
    Row = (Timestamp, Symbol, Strategy, Regime, Features, Label)
    """
    def __init__(self, config: DatasetConfig):
        self.config = config
        # self.price_loader = KRMinuteLoader(root_dir=config.price_data_root)
        # self.regime_labeler = RegimeLabeler(window_days=config.regime_window_days)

    def load_signal_logs(self, start_date: str, end_date: str) -> pd.DataFrame:
        """
        Reads signal_logger.py JSONL logs.
        Expected columns: ['timestamp', 'symbol', 'strategy_id', 'regime', 'features_json', 'signal', 'reason', ...]
        """
        rows: List[Dict[str, Any]] = []
        log_dir = self.config.signal_log_dir
        
        if not log_dir.exists():
            logger.warning(f"Log dir not found: {log_dir}")
            return pd.DataFrame()

        # Iterate over log files (assuming pattern signals_YYYYMMDD.csv or .jsonl)
        # The user mentioned .jsonl but current system uses .csv with a JSON column.
        # Let's support CSV reading as implemented in signal_logger.py
        
        for path in log_dir.glob("signals_*.csv"):
            try:
                # Extract date from filename to filter early?
                # signals_20251125.csv
                file_date_str = path.stem.split('_')[1]
                if not (start_date.replace('-','') <= file_date_str <= end_date.replace('-','')):
                    continue
                    
                df_file = pd.read_csv(path, dtype={'symbol': str})
                if not df_file.empty:
                    # Parse features_json if needed, or keep as string for now
                    # We might need to expand it later
                    rows.append(df_file)
            except Exception as e:
                logger.error(f"Error reading {path}: {e}")
                continue

        if not rows:
            return pd.DataFrame()

        df = pd.concat(rows, ignore_index=True)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df = df.set_index("timestamp").sort_index()
        
        # Filter by date range
        mask = (df.index >= pd.to_datetime(start_date)) & (df.index <= pd.to_datetime(end_date) + pd.Timedelta(days=1))
        return df.loc[mask]

    def attach_price_data(self, signals: pd.DataFrame) -> pd.DataFrame:
        """
        Joins future price data for labeling.
        """
        merged_list: List[pd.DataFrame] = []
        
        for symbol in signals["symbol"].unique():
            sig_sym = signals[signals["symbol"] == symbol].copy()
            if sig_sym.empty:
                continue

            # Load Price Data
            # In a real scenario, use KRMinuteLoader. 
            # Here we simulate loading from CSV directly for simplicity/speed in this step.
            price_dir = self.config.price_data_root
            # Assuming pattern: symbol_YYYYMMDD.csv or similar. 
            # But we need a continuous series for labeling.
            # Let's assume we can load a big file or multiple files.
            
            # For this implementation, let's try to find relevant files
            # This part is tricky without a proper Loader class.
            # I'll implement a simple glob loader here.
            
            price_dfs = []
            # We need to look for files that cover the signal dates
            # This is a simplification.
            for path in price_dir.glob(f"{symbol}_*.csv"):
                try:
                    p_df = pd.read_csv(path)
                    p_df['datetime'] = pd.to_datetime(p_df['datetime']) # Assuming 'datetime' col
                    p_df = p_df.set_index('datetime').sort_index()
                    price_dfs.append(p_df)
                except:
                    continue
            
            if not price_dfs:
                logger.warning(f"No price data for {symbol}")
                continue
                
            df_price = pd.concat(price_dfs).sort_index()
            df_price = df_price[~df_price.index.duplicated(keep='first')]

            # Merge
            # We want to attach current price info (already in signal usually)
            # But mostly we need this df_price for the Labeling step later.
            # The user design says "attach_price_data". 
            # Ideally we might just pass the price loader to the labeling step.
            # But let's follow the design: merge "open", "high", "low", "close", "volume"
            
            merged = pd.merge_asof(
                sig_sym.sort_index(),
                df_price[["open", "high", "low", "close", "volume"]],
                left_index=True,
                right_index=True,
                direction="backward",
                suffixes=('', '_market')
            )
            merged_list.append(merged)

        if not merged_list:
            return pd.DataFrame()

        return pd.concat(merged_list, axis=0).sort_index()

    def add_regime_labels(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Adds/Refines regime labels.
        """
        # If 'regime' is already in signals (from ShadowTrader), use it.
        # Or re-calculate if 'regime' is 'unknown'.
        if 'regime' not in df.columns:
            df['regime'] = 'UNCERTAIN'
            
        df["regime_ml"] = df["regime"] # Use existing for now
        return df

    def build(self, start_date: str, end_date: str) -> pd.DataFrame:
        """
        Full Pipeline: Load Logs -> Attach Price -> Add Regime
        """
        signals = self.load_signal_logs(start_date, end_date)
        if signals.empty:
            logger.info("No signals found.")
            return signals

        df = self.attach_price_data(signals)
        df = self.add_regime_labels(df)
        return df
