"""
Shadow Performance Aggregator
Calculates daily performance metrics from shadow trade logs.
Generates JSON and Markdown reports.
"""

import json
import logging
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import sys

# Add project root to path
# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root.parent))

from garam.config import PATHS

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ShadowPerf")

class ShadowPerformanceAggregator:
    def __init__(self, date_str: Optional[str] = None, mode: str = "SHADOW"):
        """
        Args:
            date_str: YYYYMMDD format. Defaults to today.
            mode: SHADOW or LIVE_PAPER. Defaults to SHADOW.
        """
        self.date_str = date_str or datetime.now().strftime('%Y%m%d')
        self.mode = mode
        
        # Determine log root based on mode
        log_subdir = "live_paper" if self.mode == "LIVE_PAPER" else "shadow"
        self.log_root = PATHS.LOGS_DIR / log_subdir
        
        self.trades_file = self.log_root / f"trades_{self.date_str}.json"
        # Signals are currently shared in LOGS_DIR/signals, or should they be separated?
        # ShadowTrader logs to LOGS_DIR/signals regardless of mode currently?
        # Let's check ShadowTrader.log_signal. It uses SignalLogger.
        # SignalLogger uses PATHS.LOGS_DIR / "signals".
        # So signals are shared or mixed. We can filter by strategy_id or just use the file.
        # For now, assume shared signal logs.
        self.signals_file = PATHS.LOGS_DIR / "signals" / f"signals_{self.date_str}.csv"
        
        self.output_json = self.log_root / f"perf_daily.json" # Latest
        self.output_md = self.log_root / f"perf_daily_{self.date_str}.md"
        
    def load_trades(self) -> List[Dict]:
        if not self.trades_file.exists():
            logger.warning(f"No trades file found for {self.date_str}: {self.trades_file}")
            return []
            
        try:
            with open(self.trades_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load trades: {e}")
            return []

    def load_signals(self) -> pd.DataFrame:
        if not self.signals_file.exists():
            # Try jsonl if csv not found? Current implementation uses csv.
            logger.warning(f"No signals file found for {self.date_str}: {self.signals_file}")
            return pd.DataFrame()
            
        try:
            return pd.read_csv(self.signals_file)
        except Exception as e:
            logger.error(f"Failed to load signals: {e}")
            return pd.DataFrame()
            
    def calculate_metrics(self, trades: List[Dict]) -> Dict:
        # Load signals for AI stats
        df_signals = self.load_signals()
        
        ai_stats = {
            "intervention_count": 0,
            "total_signals": 0,
            "avg_confidence": 0.0,
            "current_regime": "unknown",
            "last_confidence": 0.0
        }
        
        if not df_signals.empty:
            ai_stats["total_signals"] = len(df_signals)
            if "regime" in df_signals.columns:
                ai_stats["current_regime"] = df_signals.iloc[-1]["regime"]
            
            # Check for AI columns
            # Note: Columns might be 'ai_confidence', 'ai_adjustment' if logged by SignalLogger
            # SignalLogger logs whatever is in the 'extra' dict or passed args.
            # We need to ensure SignalLogger actually saved these columns.
            # In ShadowTrader, we passed `ai_confidence` inside `features` or `reason`?
            # Wait, in `ShadowTrader.on_bar`, we did:
            # log_signal(..., features=features, ...)
            # And `SurfingBrainAdapter` added `ai_confidence` to `result`.
            # `ShadowTrader` extracts `signal`, `strategy_id`, `reason`.
            # It does NOT automatically extract `ai_confidence` from `result` and pass it to `log_signal` as a separate column.
            # It passes `features`.
            # But `SurfingBrainAdapter` put `ai_confidence` in `result`, NOT in `features`.
            # So `ai_confidence` is currently ONLY in `reason` string (e.g. "Reason | AI:boost(0.7)").
            # We should parse it from `reason` or update `ShadowTrader` to log it explicitly.
            # Parsing from `reason` is easier for now without changing ShadowTrader again.
            
            # Parse AI stats from 'reason' column if available
            if "reason" in df_signals.columns:
                # Look for "AI:..."
                # Example: "MA Cross | AI:suppress(0.2)"
                ai_rows = df_signals[df_signals["reason"].str.contains("AI:", na=False)]
                ai_stats["intervention_count"] = len(ai_rows)
                
                # Extract confidence
                # Regex or simple split
                # AI:xxx(0.xx)
                try:
                    # Extract float between ( and ) after AI:
                    extracted = df_signals["reason"].str.extract(r"AI:[a-zA-Z]+\((\d+\.\d+)\)")
                    if not extracted.empty:
                        confs = extracted[0].astype(float)
                        ai_stats["avg_confidence"] = round(confs.mean(), 2)
                        ai_stats["last_confidence"] = round(confs.iloc[-1], 2) if not confs.empty else 0.0
                except Exception as e:
                    logger.warning(f"Failed to parse AI confidence: {e}")

        if not trades:
            metrics = self._empty_metrics()
            metrics.update(ai_stats) # Add AI stats even if no trades
            return metrics
            
        df = pd.DataFrame(trades)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Basic Stats
        total_trades = len(df)
        
        # ... (P&L Calculation Logic - Keeping existing) ...
        # Group by symbol
        pnl_total = 0
        winning_trades = 0
        losing_trades = 0
        
        # Simple FIFO matcher for P&L
        symbol_queues = {} # symbol -> list of (qty, price)
        completed_trades = []
        
        for _, row in df.iterrows():
            sym = row['symbol']
            action = row['action']
            qty = row['qty']
            price = row['price']
            
            if sym not in symbol_queues:
                symbol_queues[sym] = []
                
            if action == 'BUY':
                symbol_queues[sym].append({'qty': qty, 'price': price})
            elif action == 'SELL':
                remaining_qty = qty
                while remaining_qty > 0 and symbol_queues[sym]:
                    match = symbol_queues[sym][0]
                    match_qty = match['qty']
                    match_price = match['price']
                    
                    executed_qty = min(remaining_qty, match_qty)
                    
                    # Calculate P&L for this chunk
                    trade_pnl = (price - match_price) * executed_qty
                    # Transaction cost (0.23% tax + 0.015% fee approx)
                    cost = (price * executed_qty * 0.0023) + ((price + match_price) * executed_qty * 0.00015) 
                    net_pnl = trade_pnl - cost
                    
                    pnl_total += net_pnl
                    
                    completed_trades.append({
                        'symbol': sym,
                        'pnl': net_pnl,
                        'return_pct': (net_pnl / (match_price * executed_qty)) * 100
                    })
                    
                    if net_pnl > 0:
                        winning_trades += 1
                    elif net_pnl < 0:
                        losing_trades += 1
                        
                    # Update queue
                    if match_qty > remaining_qty:
                        match['qty'] -= remaining_qty
                        remaining_qty = 0
                    else:
                        symbol_queues[sym].pop(0)
                        remaining_qty -= match_qty
                        
        win_rate = (winning_trades / (winning_trades + losing_trades)) * 100 if (winning_trades + losing_trades) > 0 else 0
        
        return {
            "date": self.date_str,
            "total_pnl": round(pnl_total, 0),
            "win_rate": round(win_rate, 1),
            "total_trades": total_trades,
            "completed_trades": len(completed_trades),
            "winning_trades": winning_trades,
            "losing_trades": losing_trades,
            "timestamp": datetime.now().isoformat(),
            **ai_stats # Merge AI stats
        }

    def _empty_metrics(self) -> Dict:
        return {
            "date": self.date_str,
            "total_pnl": 0,
            "win_rate": 0,
            "total_trades": 0,
            "completed_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "timestamp": datetime.now().isoformat()
        }

    def generate_report(self):
        trades = self.load_trades()
        metrics = self.calculate_metrics(trades)
        
        # Save JSON
        with open(self.output_json, 'w', encoding='utf-8') as f:
            json.dump(metrics, f, indent=2)
            
        # Save Markdown
        with open(self.output_md, 'w', encoding='utf-8') as f:
            f.write(f"# Shadow Performance Report ({self.date_str})\n\n")
            f.write(f"## Summary\n")
            f.write(f"- **P&L**: {metrics['total_pnl']:,.0f} KRW\n")
            f.write(f"- **Win Rate**: {metrics['win_rate']}%\n")
            f.write(f"- **Trades**: {metrics['total_trades']} (Completed: {metrics['completed_trades']})\n")
            
        logger.info(f"Generated reports: {self.output_json}, {self.output_md}")
        return metrics

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", type=str, help="YYYYMMDD")
    parser.add_argument("--mode", type=str, default="SHADOW", choices=["SHADOW", "LIVE_PAPER"])
    args = parser.parse_args()
    
    aggregator = ShadowPerformanceAggregator(date_str=args.date, mode=args.mode)
    aggregator.generate_report()
