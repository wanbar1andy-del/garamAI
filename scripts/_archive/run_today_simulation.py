import json
from datetime import datetime
from pathlib import Path
import sys
import pandas as pd
import numpy as np

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import PATHS
from data.loaders.kr_minute_loader import KRMinuteLoader
from sim.test_account import TestAccount
from strategies.kr_intraday.backtest_runner import IntradayBacktestRunner
from strategies.kr_intraday.momentum_breakout import MomentumBreakoutStrategy
import logging

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TodaySimulation")

import json
from datetime import datetime
from pathlib import Path
import sys
import pandas as pd
import numpy as np

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import PATHS
from data.loaders.kr_minute_loader import KRMinuteLoader
from sim.test_account import TestAccount
import logging

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TodaySimulation")

class RealtimeLoader:
    def __init__(self, target_date_str):
        self.date_nodash = target_date_str.replace("-", "")
        self.base_path = PATHS.DATA_DIR / "kr" / "realtime" / "1m"

    def load(self, symbol):
        """Load {symbol}_{date}.csv and return last close price and OHLC/Vol."""
        filename = f"{symbol}_{self.date_nodash}.csv"
        file_path = self.base_path / filename
        
        if not file_path.exists():
            return None
            
        try:
            df = pd.read_csv(file_path)
            if 'close' not in df.columns or 'datetime' not in df.columns:
                return None
                
            # Convert
            df['close'] = pd.to_numeric(df['close'], errors='coerce')
            df['volume'] = pd.to_numeric(df['volume'], errors='coerce')
            df['timestamp'] = pd.to_datetime(df['datetime'])
            df.set_index('timestamp', inplace=True)
            df.sort_index(inplace=True)
            
            if df.empty:
                return None
                
            last_price = df['close'].iloc[-1]
            last_time = df.index[-1]
            
            # Simple stats for report
            high = df['close'].max()
            low = df['close'].min()
            vol = df['volume'].sum()
            
            return {
                'last_price': float(last_price),
                'last_time': last_time,
                'high': float(high),
                'low': float(low),
                'volume': float(vol)
            }
            
        except Exception as e:
            logger.error(f"Failed to load {filename}: {e}")
            return None

def run_simulation_and_sync():
    today_str = datetime.now().strftime("%Y-%m-%d")
    logger.info(f"Starting RECOVERY & SYNC for {today_str}")
    
    rt_loader = RealtimeLoader(today_str)
    
    # 1. Restore Legacy Positions (From Morning/Yesterday State)
    legacy_holdings = {
        "458870": {"qty": 143, "entry_price": 122200.0, "name": "CusTech"},
        "353200": {"qty": 373, "entry_price": 46550.0, "name": "Daeduck"},
        "440110": {"qty": 673, "entry_price": 25600.0, "name": "PoscoDX"},
        "298040": {"qty": 9, "entry_price": 1848000.0, "name": "Hyosung"},
        "007660": {"qty": 119, "entry_price": 136500.0, "name": "LeeSu"}
    }
    
    active_holdings = {}
    closed_trades = []
    
    total_initial_capital = 100_000_000
    # Estimate Cash based on invested
    # Invested ~ 17M * 5 approx 85M? 
    # Current Equity ~100M
    
    calculated_equity = 0.0
    invested_value = 0.0
    
    STOP_LOSS_PCT = -0.02 # -2% Stop Loss Trigger
    
    logger.info("Processing Legacy Positions...")
    
    for symbol, info in legacy_holdings.items():
        data = rt_loader.load(symbol)
        
        qty = info['qty']
        entry_price = info['entry_price']
        
        if data:
            current_price = data['last_price']
            pnl = (current_price - entry_price) * qty
            pnl_pct = (current_price / entry_price) - 1.0
            value = current_price * qty
            
            logging.info(f"[{symbol}] Entry: {entry_price}, Curr: {current_price}, PnL: {pnl_pct:.2%}")
            
            # Exit Logic
            if pnl_pct < STOP_LOSS_PCT:
                logging.info(f"  -> STOP LOSS Triggered ({pnl_pct:.2%}). Closing.")
                closed_trades.append({
                    "symbol": symbol,
                    "pnl": pnl,
                    "reason": "STOP_LOSS"
                })
                # Add cash proceeds (simplified)
                # We track equity mainly
                calculated_equity += (entry_price * qty) + pnl
            else:
                # Hold
                active_holdings[symbol] = {
                    "name": info.get("name", symbol),
                    "qty": qty,
                    "entry_price": entry_price,
                    "current_price": current_price,
                    "entry_date": today_str, # Assuming today/carryover
                    "value": value,
                    "pnl": pnl,
                    "pnl_pct": pnl_pct * 100
                }
                calculated_equity += value
                invested_value += value
                
        else:
            # No Data found? Keep as is, assume price unchanged (or use entry price)
            logging.warning(f"No Data for {symbol}. Keeping unchanged.")
            active_holdings[symbol] = {
                "name": info.get("name", symbol),
                "qty": qty,
                "entry_price": entry_price,
                "current_price": entry_price,
                "entry_date": today_str,
                "value": entry_price * qty,
                "pnl": 0.0,
                "pnl_pct": 0.0
            }
            calculated_equity += (entry_price * qty)
            invested_value += (entry_price * qty)

    # Calculate Cash
    # If base was 100M, and we had closed trades or holdings.
    # Simplified: Equity = Cash + Holdings Value.
    # We assume Starting Equity was 100M.
    # Current Equity = Starting + Realized PnL + Unrealized PnL.
    
    realized_pnl = sum(t['pnl'] for t in closed_trades)
    unrealized_pnl = sum(h['pnl'] for h in active_holdings.values())
    
    final_equity = total_initial_capital + realized_pnl + unrealized_pnl
    final_cash = final_equity - invested_value
    
    # Construct Report
    trade_count = len(closed_trades) # New exits
    win_count = 0 # Stops are losses
    
    report_data = {
        "date": today_str,
        "status": "OK",
        "win_rate": 0.0,
        "pnl": realized_pnl + unrealized_pnl, # Total Day Change
        "trade_count": trade_count,
        "total_return_pct": ((realized_pnl + unrealized_pnl) / total_initial_capital) * 100,
        "summary": f"Data Sync Completed. {len(active_holdings)} Positions Held. {trade_count} Positions Closed on Stop Loss. Total PnL: {realized_pnl + unrealized_pnl:,.0f} KRW."
    }
    
    # Save Report
    report_path = PATHS.TODAY_SIM_FILE
    with report_path.open("w", encoding="utf-8") as f:
        json.dump(report_data, f, ensure_ascii=False, indent=2)
    logger.info(f"Saved report to {report_path}")
    
    # Sync signals_live.json
    live_state = {
        "date": today_str,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "regime": "SYNCED_RECOVERY",
        "orders": [],
        "holdings": active_holdings,
        "equity": final_equity,
        "cash": final_cash
    }
    
    live_path = PATHS.STRATEGY_SIGNALS_LIVE
    with live_path.open("w", encoding="utf-8") as f:
        json.dump(live_state, f, ensure_ascii=False, indent=2)
    logger.info(f"Synced portfolio state to {live_path}")

if __name__ == "__main__":
    run_simulation_and_sync()
