import pandas as pd
from pathlib import Path
from run_backtest_final import load_data

def check_market_health():
    import glob
    def load_data_all(data_dir, s_date, e_date):
        print(f"[Loader] Loading ALL data from {data_dir}...")
        files = glob.glob(str(data_dir / "*.csv"))
        symbols = [Path(f).stem for f in files]
        
        closes = {}
        s_dt, e_dt = pd.to_datetime(s_date), pd.to_datetime(e_date)
        
        for f in files:
            try:
                df = pd.read_csv(f)
                cols = [c.lower() for c in df.columns]
                df.columns = cols
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
            except: pass
        return pd.DataFrame(closes), None

    print("::: MARKET HEALTH CHECK (2025.06-2026.02) :::")
    
    data_dir = Path("c:/garam/garam/GARAM_Data/history/minute")
    
    closes, _ = load_data_all(data_dir, "20250601", "20260205")
    
    if closes.empty:
        print("CRITICAL ERROR: No Data Loaded.")
        return

    # Check Specifics
    targets = ["005930", "000660", "005380"] # Sam, Hynix, Hyundai
    print("\n[Benchmarks]")
    for t in targets:
        if t in closes.columns:
            s = closes[t].iloc[0]
            e = closes[t].iloc[-1]
            r = (e/s) - 1.0
            print(f"{t}: {s} -> {e} ({r*100:+.2f}%)")
        else:
            print(f"{t}: Not Found")
    market_index = closes.mean(axis=1)
    start_px = market_index.iloc[0]
    end_px = market_index.iloc[-1]
    ret = (end_px / start_px) - 1.0
    
    # Calculate Top 5 Winners
    symbol_rets = (closes.iloc[-1] / closes.iloc[0]) - 1.0
    top_5 = symbol_rets.sort_values(ascending=False).head(5)
    
    print(f"\n[Market Overview]")
    print(f"Start Index: {start_px:.2f}")
    print(f"End Index:   {end_px:.2f}")
    print(f"Market Return: {ret*100:+.2f}%")
    
    print("\n[Top 5 Winners]")
    for sym, r in top_5.items():
        print(f"{sym}: {r*100:+.2f}%")
        
    if ret > 0.20:
        print("\n[Diagnosis] BULL MARKET CONFIRMED.")
        print(" -> System Logic was WRONG (Too Defensive).")
        print(" -> Action: Switch to 'Trend Following' (Loose Stop, Breakout Entry).")
    elif ret < -0.10:
        print("\n[Diagnosis] BEAR MARKET CONFIRMED.")
        print(" -> User Perception Mismatch? Or Sector-specific Bull?")
    else:
        print("\n[Diagnosis] SIDEWAYS / MIXED.")

if __name__ == "__main__":
    check_market_health()
