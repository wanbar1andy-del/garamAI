import pandas as pd
import numpy as np
import argparse
from pathlib import Path
from run_alpha_robust import load_data

def run_real_boom():
    print("::: GARAM REALITY CHECK: WHALE SURFING MODE :::")
    print("Period: 2025-06-01 ~ 2026-02-05")
    print("Condition: RAW MARKET DATA (No artificial crashes)")
    print("Strategy: WHALE SURFING (Ride the Volume)")
    
    # Local load_data to bypass limits
    import glob
    def load_data_all(data_dir, s_date, e_date):
        print(f"[Loader] Loading ALL data from {data_dir}...")
        files = glob.glob(str(data_dir / "*.csv"))
        symbols = [Path(f).stem for f in files] # NO LIMIT
        
        closes, volumes = {}, {}
        s_dt, e_dt = pd.to_datetime(s_date), pd.to_datetime(e_date)
        
        for f in files:
            try:
                df = pd.read_csv(f)
                # Parse
                cols = [c.lower() for c in df.columns]
                df.columns = cols
                if "datetime" in df.columns: df = df.rename(columns={"datetime": "date"})
                if "volume" not in df.columns: df["volume"] = 0.0
                
                if "date" in df.columns:
                     df["dt"] = pd.to_datetime(df["date"].astype(str), format="%Y%m%d%H%M%S", errors='coerce')
                     if df["dt"].isnull().all():
                         df["dt"] = pd.to_datetime(df["date"].astype(str), format="%Y%m%d%H%M", errors='coerce')
                
                df = df.dropna(subset=["dt"]).set_index("dt").sort_index()
                mask = (df.index >= s_dt) & (df.index <= e_dt)
                df = df.loc[mask]
                
                if not df.empty:
                    sym = Path(f).stem
                    closes[sym] = df["close"]
                    volumes[sym] = df["volume"]
            except: pass
            
        print(f"[Loader] Loaded {len(closes)} symbols (Total Market).")
        return pd.DataFrame(closes), pd.DataFrame(volumes)

    # 1. Load Data
    data_dir = Path("c:/garam/garam/GARAM_Data/history/minute")
    start_date = "20250601"
    end_date = "20260205"
    
    print(f"[{data_dir.name}] Loading Real History Data...")
    closes, volumes = load_data_all(data_dir, start_date, end_date)
    if closes.empty: return

    # 2. Whale Logic (Simple & Aggressive)
    # Use the Whale: Ride the wave when volume explodes
    
    print("[Brain] Calculating Whale Signals...")
    
    # Vol Ratio (Relative to 20-bar avg)
    v_ma20 = volumes.rolling(20).mean()
    vol_ratio = volumes / (v_ma20 + 1e-9)
    
    # Price Trend (Above MA60)
    ma60 = closes.rolling(60).mean()
    trend_ok = closes > ma60
    
    # Momentum (RSI or just PctChange)
    ret = closes.pct_change()
    
    # Signal: Huge Volume (>5x) + Up Move (>1%) + Trend OK
    # This is the "Whale Strike"
    whale_signal = (vol_ratio > 5.0) & (ret > 0.01) & trend_ok
    
    # Execution
    cash = 1_000_000 # 100 Man Won
    equity_curve = []
    trades = []
    
    pos_sym = None
    pos_qty = 0
    entry_px = 0.0
    
    # Aggressive Settings for Bull Market
    # Trailing Stop: 3% (Standard)
    # Take Profit: None (Ride the wave until Stop hit or Reversal)
    # Or Partial Profit? Let's use Trailing Stop of 5% from High.
    
    high_water_mark = 0.0
    
    for ts in closes.index:
        current_prices = closes.loc[ts]
        current_sigs = whale_signal.loc[ts]
        
        equity = cash
        if pos_sym:
            curr_px = current_prices.get(pos_sym, entry_px)
            if pd.isna(curr_px): curr_px = entry_px
            equity += pos_qty * curr_px
            
            # Update High Water Mark for Trailing Stop
            if curr_px > high_water_mark:
                high_water_mark = curr_px
                
            # Trailing Stop Logic (Loose 5% from Peak)
            drawdown = (curr_px / high_water_mark) - 1.0
            
            if drawdown < -0.05: # Trailing Stop Hit
                exit_px = curr_px * 0.998 # 0.2% slip/fee
                cash += pos_qty * exit_px
                pnl = (exit_px / entry_px) - 1.0
                trades.append({"ts": ts, "type": "EXIT_TRAIL", "pnl": pnl})
                pos_sym = None; pos_qty = 0
                continue
                
            # Stop Loss (Hard -3% from Entry)
            ret_entry = (curr_px / entry_px) - 1.0
            if ret_entry < -0.03:
                exit_px = curr_px * 0.998
                cash += pos_qty * exit_px
                pnl = (exit_px / entry_px) - 1.0
                trades.append({"ts": ts, "type": "EXIT_STOP", "pnl": pnl})
                pos_sym = None; pos_qty = 0
                continue
                
        # Entry Logic
        if pos_sym is None:
            cands = current_sigs[current_sigs].index
            if not cands.empty:
                # Pick strongest momentum
                best_sym = None
                best_ret = -1.0
                for sym in cands:
                     r = ret.at[ts, sym]
                     if r > best_ret:
                         best_ret = r
                         best_sym = sym
                
                if best_sym:
                    price = current_prices.get(best_sym, 0)
                    if price > 0:
                        # Full Bet (Whale Surfing)
                        invest = cash * 0.98
                        qty = int(invest / (price * 1.002))
                        if qty > 0:
                            cash -= qty * price * 1.002
                            pos_sym = best_sym
                            pos_qty = qty
                            entry_px = price
                            high_water_mark = price
                            trades.append({"ts": ts, "type": "ENTRY"})
                            
        equity_curve.append({"ts": ts, "equity": equity})

    # Report
    final_eq = equity_curve[-1]["equity"]
    roi = (final_eq / 1_000_000) - 1.0
    
    print("\n" + "="*50)
    print("📈 REAL MARKET REPORT (NO SIMULATED CRASHES)")
    print("Strategy: WHALE SURFING (Aggressive)")
    print("="*50)
    print(f"Initial Capital : 1,000,000 KRW")
    print(f"Final Equity    : {final_eq:,.0f} KRW")
    print(f"Net Return      : {roi*100:+.2f}%")
    print(f"Total Trades    : {len([t for t in trades if t['type'] != 'ENTRY'])}")
    
    win_trades = [t for t in trades if t.get('pnl', 0) > 0]
    win_rate = len(win_trades) / len(trades) * 200 if trades else 0 # Approx
    # Wait, trade list has entries too.
    exits = [t for t in trades if t['type'] != 'ENTRY']
    wins = [t for t in exits if t['pnl'] > 0]
    wr = len(wins) / len(exits) * 100 if exits else 0
    
    print(f"Win Rate        : {wr:.1f}%")
    print("="*50)

if __name__ == "__main__":
    run_real_boom()
