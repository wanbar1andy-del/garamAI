
"""
Trading Logger with Ghost Tail Tracking
---------------------------------------
Tracks trades and updates Ghost Tail analysis in real-time or batch.
"""
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import logging

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOG_DIR = PROJECT_ROOT / "logs"
DATA_DIR = PROJECT_ROOT / "GARAM_Data"
GHOST_TAIL_LOG = LOG_DIR / "ghost_tail.csv"

# Configure Logging
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

def update_ghost_tail():
    """
    Reads trade logs and updates ghost tail analysis.
    This routine simulates the 'Real-time' update by checking recent trades.
    """
    logger.info("Updating Ghost Tail Analysis...")
    
    # 1. Load Trades
    fills_path = DATA_DIR / "orders" / "chejan_fills.csv"
    if not fills_path.exists():
        logger.warning(f"No trade fills found at {fills_path}")
        return

    try:
        trades = pd.read_csv(fills_path)
    except Exception as e:
        logger.error(f"Failed to read trade log: {e}")
        return

    if trades.empty:
        logger.info("Trade log empty.")
        return

    # 2. Existing Ghost Logs
    existing_ghost = pd.DataFrame()
    if GHOST_TAIL_LOG.exists():
        try:
             existing_ghost = pd.read_csv(GHOST_TAIL_LOG)
        except:
             pass
    
    # 3. Process New Sells
    new_entries = []
    
    for _, row in trades.iterrows():
        t_type = str(row.get('type', '')).lower()
        # Identify SELLs
        if not ("sell" in t_type or "매도" in t_type or t_type == "1"):
            continue
            
        # Unique ID for trade? Usually combine date+code+time
        # For now, simple check using timestamp
        ts_str = str(row.get('date', '')) # YYYYMMDDHHMMSS
        symbol = str(row.get('code', '')).zfill(6)
        sell_price = float(row.get('price', 0))
        
        # Check if already analyzed
        if not existing_ghost.empty:
             # Heuristic check
             duplicate = existing_ghost[
                 (existing_ghost['date'] == ts_str[:8]) & 
                 (existing_ghost['symbol'] == symbol) & 
                 (existing_ghost['sell_price'] == sell_price)
             ]
             if not duplicate.empty:
                 continue
                 
        # Analyze 120min follow-up
        # Needs Minute Data
        minute_path = DATA_DIR / "history" / "minute" / f"{symbol}.csv"
        if not minute_path.exists():
            continue
            
        try:
            df = pd.read_csv(minute_path)
            if "체결시간" in df.columns:
                df = df.rename(columns={"체결시간": "date", "현재가": "close"})
            df["date"] = pd.to_datetime(df["date"], format="%Y%m%d%H%M%S", errors='coerce')
            df = df.dropna(subset=['date']).sort_values('date')
            
            sell_dt = pd.to_datetime(ts_str, format="%Y%m%d%H%M%S")
            end_dt = sell_dt + timedelta(minutes=120)
            
            window = df[(df['date'] > sell_dt) & (df['date'] <= end_dt)]
            
            if window.empty:
                # Data might not be available yet (Real-time lag)
                continue
                
            post_price = window.iloc[-1]['close']
            diff_pct = (post_price - sell_price) / sell_price * 100
            verdict = "PERFECT_EXIT" if diff_pct < -0.5 else ("TOO_EARLY" if diff_pct > 0.5 else "NEUTRAL")
            
            # Opportunity Cost = (Post Price - Sell Price) * Qty
            # We calculate Per Share Opportunity Cost for simplicity
            opp_cost = post_price - sell_price 
            
            new_entries.append({
                "date": ts_str[:8],
                "time": ts_str[8:],
                "symbol": symbol,
                "sell_price": sell_price,
                "post_price": post_price,
                "diff_120m": diff_pct,
                "opp_cost": opp_cost,
                "verdict": verdict,
                "updated_at": datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error analyzing trade {symbol}: {e}")
            continue

    if new_entries:
        new_df = pd.DataFrame(new_entries)
        combined = pd.concat([existing_ghost, new_df], ignore_index=True)
        combined.to_csv(GHOST_TAIL_LOG, index=False)
        logger.info(f"Ghost Tail updated with {len(new_entries)} new records.")
    else:
        logger.info("No new completed ghost tails found.")

if __name__ == "__main__":
    update_ghost_tail()
