import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

# otherwise fallback to local config (when running from root)
try:
    from garam.config import PATHS
except ImportError:
    from config import PATHS

logger = logging.getLogger(__name__)

class SignalReconciliation:
    """
    Reconciles generated signals against executed trades to detect drops or failures.
    """
    def __init__(self, date_str: str = None):
        self.date_str = date_str or datetime.now().strftime("%Y%m%d")
        self.signals_dir = PATHS.LOGS_DIR / "signals"
        self.trades_dir = PATHS.LOGS_DIR / "trades" # Assuming trades are logged here or we scan broker logs
        # Note: RealBrokerSim logs trades to a specific file, we might need to adapt this path
        # based on where RealBrokerSim saves trade history. 
        # For now, let's assume we can find trade logs in logs/shadow/trades_{date}.jsonl or similar.
        # If not, we'll need to update RealBrokerSim to produce a standard trade log.
        self.shadow_logs_dir = PATHS.SHADOW_LOGS
        
    def run(self) -> Dict[str, Any]:
        """
        Compare signals vs trades.
        Returns a summary dict.
        """
        signals = self._load_signals()
        trades = self._load_trades()
        
        report = {
            "date": self.date_str,
            "total_signals": len(signals),
            "total_trades": len(trades),
            "matches": 0,
            "missing_trades": [],
            "orphan_trades": []
        }
        
        # Simple matching logic: 
        # A signal is "matched" if there is a trade for the same symbol and side 
        # within a reasonable time window (e.g., 5 mins) or just same day for now.
        
        # Index trades by symbol for faster lookup
        trades_by_symbol = {}
        for t in trades:
            sym = t.get('symbol') or t.get('code')
            if sym not in trades_by_symbol:
                trades_by_symbol[sym] = []
            trades_by_symbol[sym].append(t)
            
        # Check Signals -> Trades
        for sig in signals:
            sym = sig.get('symbol')
            side = sig.get('signal_type') # BUY/SELL
            
            matched = False
            if sym in trades_by_symbol:
                # Look for a matching trade
                for t in trades_by_symbol[sym]:
                    # Map signal side to trade side if needed
                    trade_side = t.get('side') # buy/sell
                    if trade_side and side and trade_side.upper() == side.upper():
                        matched = True
                        break
            
            if matched:
                report["matches"] += 1
            else:
                report["missing_trades"].append(sig)
                
        # Check Trades -> Signals (Orphans)
        # (Optional: Find trades that had no corresponding signal - unauthorized trading?)
        
        return report

    def _load_signals(self) -> List[Dict[str, Any]]:
        path = self.signals_dir / f"signals_{self.date_str}.jsonl"
        signals = []
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        signals.append(json.loads(line))
                    except:
                        pass
        return signals

    def _load_trades(self) -> List[Dict[str, Any]]:
        # Attempt to load from shadow trade logs
        # RealBrokerSim saves to: self.trade_log_path (passed in init)
        # We need to standardize where RealBrokerSim saves trades.
        # Let's assume it saves to GARAM_Data/logs/shadow/trades_{date}.jsonl
        
        path = self.shadow_logs_dir / f"trades_{self.date_str}.jsonl"
        trades = []
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        trades.append(json.loads(line))
                    except:
                        pass
        return trades

if __name__ == "__main__":
    # CLI usage
    rec = SignalReconciliation()
    report = rec.run()
    print(json.dumps(report, indent=2))
