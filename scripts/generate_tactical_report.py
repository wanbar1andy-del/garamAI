
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

# Garam Project Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "GARAM_Data"
LOG_DIR = PROJECT_ROOT / "logs"
REPORT_DIR = PROJECT_ROOT / "reports"

def load_trades():
    """Load trades from potential locations"""
    # 1. Check standard fills location
    fills_path = DATA_DIR / "orders" / "chejan_fills.csv"
    if fills_path.exists():
        return pd.read_csv(fills_path)
    
    # 2. Check logs
    fills_path = LOG_DIR / "chejan_fills.csv"
    if fills_path.exists():
        return pd.read_csv(fills_path)
        
    print("[WARN] No trade log (chejan_fills.csv) found.")
    return pd.DataFrame()

def load_minute_data(symbol):
    """Load minute data for a symbol"""
    path = DATA_DIR / "history" / "minute" / f"{symbol}.csv"
    if not path.exists():
        return pd.DataFrame()
    
    df = pd.read_csv(path)
    # Standardize headers
    if "체결시간" in df.columns:
        df = df.rename(columns={"체결시간": "date", "현재가": "close"})
    
    df["date"] = pd.to_datetime(df["date"], format="%Y%m%d%H%M%S", errors='coerce')
    df = df.dropna(subset=["date"]).sort_values("date")
    return df

def generate_ghost_tail_log(trades):
    """Analyze Post-Sell Performance"""
    if trades.empty:
        return pd.DataFrame()

    results = []
    
    # Filter Sells
    # Assume 'type' column has 'sell' or '매도' or '1'
    # And 'code', 'date' (or time), 'price'
    
    for idx, row in trades.iterrows():
        t_type = str(row.get('type', '')).lower()
        if not ("sell" in t_type or "매도" in t_type or t_type == "1"):
            continue
            
        symbol = str(row.get('code', '')).zfill(6)
        sell_price = float(row.get('price', 0))
        
        # Date parsing
        t_date_str = str(row.get('date', '')) # YYYYMMDDHHMMSS
        try:
            sell_dt = pd.to_datetime(t_date_str, format="%Y%m%d%H%M%S")
        except:
             # Try alternate
             continue
             
        # Load Data
        df = load_minute_data(symbol)
        if df.empty:
            continue
            
        # 120m window
        end_dt = sell_dt + timedelta(minutes=120)
        
        # Get price at 120m (or close to it)
        window = df[(df['date'] > sell_dt) & (df['date'] <= end_dt)]
        
        if window.empty:
            continue
            
        # Last price in window
        post_price = window.iloc[-1]['close']
        post_dt = window.iloc[-1]['date']
        
        # Calculate Ghost Return
        # (Price_After - Sell_Price) / Sell_Price
        # If Positive: I sold too early (Sad) -> BAD_SELL (in ghost terms) 
        # If Negative: I sold before crash (Happy) -> GOOD_SELL
        
        diff_pct = (post_price - sell_price) / sell_price * 100
        
        verdict = "PERFECT_EXIT" if diff_pct < -0.5 else ("TOO_EARLY" if diff_pct > 0.5 else "NEUTRAL")
        
        results.append({
            "date": sell_dt.strftime("%Y-%m-%d"),
            "time": sell_dt.strftime("%H:%M:%S"),
            "symbol": symbol,
            "sell_price": sell_price,
            "post_price": post_price,
            "diff_120m": diff_pct,
            "verdict": verdict
        })
        
    return pd.DataFrame(results)

def main():
    print("=== Garam Tactical Analyst Report Generator ===")
    
    # 1. Load Trades
    trades = load_trades()
    print(f"Loaded {len(trades)} trades.")
    
    # 2. Ghost Tail Analysis
    ghost_df = generate_ghost_tail_log(trades)
    
    # Save Log
    ghost_log_path = LOG_DIR / "ghost_tail.csv"
    ghost_df.to_csv(ghost_log_path, index=False)
    print(f"[Log] Ghost Tail Log saved: {ghost_log_path}")
    
    # 3. Create Markdown Report
    today_str = datetime.now().strftime("%Y-%m-%d")
    report_path = REPORT_DIR / f"tactical_review_{today_str}.md"
    
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(f"# 🛡️ Garam Tactical Review ({today_str})\n\n")
        
        # Summary
        f.write("## 1. Trading Summary\n")
        f.write(f"- Total Trades: {len(trades)}\n")
        if not trades.empty:
             buys = len([x for x in trades['type'].astype(str) if '2' in x or '매수' in x])
             sells = len(trades) - buys
             f.write(f"- Buys: {buys}, Sells: {sells}\n")
        else:
             f.write("- No trades today.\n")
             
        # Ghost Tail Section
        f.write("\n## 2. Ghost Tail Analysis (Post-Sell 120m)\n")
        if not ghost_df.empty:
            good_exits = len(ghost_df[ghost_df['diff_120m'] < 0])
            bad_exits = len(ghost_df[ghost_df['diff_120m'] > 0])
            f.write(f"- **Exit Quality**: Good {good_exits} vs Bad {bad_exits}\n")
            f.write("\n### Details\n")
            f.write(ghost_df.to_markdown(index=False))
        else:
            f.write("No sales or data insufficient for analysis.\n")
            
        f.write("\n---\n*Generated by Garam Tactical Monitor*\n")
        
    print(f"[Report] Saved to {report_path}")

if __name__ == "__main__":
    main()
