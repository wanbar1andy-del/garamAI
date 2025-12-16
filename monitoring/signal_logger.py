import csv
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# otherwise fallback to local config (when running from root)
try:
    from garam.config import PATHS
except ImportError:
    from config import PATHS

logger = logging.getLogger(__name__)

class SignalLogger:
    """
    Logs trading signals to persistent storage for audit and reconciliation.
    """
    def __init__(self):
        self.log_dir = PATHS.LOGS_DIR / "signals"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Daily signal files
        today_str = datetime.now().strftime("%Y%m%d")
        self.log_file = self.log_dir / f"signals_{today_str}.csv"
        self.jsonl_file = self.log_dir / f"signals_{today_str}.jsonl"

    def log_signal(self, 
                   timestamp: datetime, 
                   symbol: str, 
                   signal: int, 
                   price: float, 
                   strategy_id: str = "default",
                   regime: str = "unknown",
                   features: Dict[str, Any] = None,
                   reason: str = ""):
        """
        Log a trading signal with full context for ML training.
        
        Schema:
        - timestamp: Signal time
        - symbol: Target asset
        - signal: 1 (Buy), -1 (Sell), 0 (Hold/Exit)
        - price: Signal price (usually Close of signal bar)
        - strategy_id: Identifier of the logic used (e.g., "SB-2.5")
        - regime: Market regime label at time of signal
        - features: JSON string of key feature values (snapshot)
        - reason: Human readable reason
        """
        if features is None:
            features = {}
            
        record = {
            'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'symbol': symbol,
            'signal': signal,
            'price': price,
            'strategy_id': strategy_id,
            'regime': regime,
            'features_json': json.dumps(features), # Snapshot for ML replay
            'reason': reason
        }
        
        # CSV Log
        try:
            file_exists = self.log_file.exists()
            with open(self.log_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=record.keys())
                if not file_exists:
                    writer.writeheader()
                writer.writerow(record)
        except Exception as e:
            logger.error(f"Failed to write signal to CSV: {e}")
            
        # JSONL Log (for easier parsing)
        try:
            with open(self.jsonl_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(record) + '\n')
        except Exception as e:
            logger.error(f"Failed to write signal to JSONL: {e}")
            
        logger.info(f"Signal Logged: {strategy_id} {signal} {symbol} @ {price}")
