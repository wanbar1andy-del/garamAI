import pandas as pd
from pathlib import Path
import json

def load_trades(run_dir):
    # Try loading all_trades.csv first
    p = run_dir / "all_trades.csv"
    if p.exists():
        return pd.read_csv(p)
    # Check for all_orders.csv
    p = run_dir / "all_orders.csv"
    if p.exists():
        # Convert orders to pseudo-trades for symbol check
        # Assuming BUY orders represent entries
        df = pd.read_csv(p)
        return df[df["side"] == "BUY"]
    return pd.DataFrame()

def analyze_mismatch(base_path, new_path):
    print(f"Comparing:")
    print(f"  Base: {base_path}")
    print(f"  New : {new_path}")
    
    df_base = load_trades(base_path)
    df_new = load_trades(new_path)
    
    if "entry_date" in df_base.columns:
        # Standard trades format (YYYYMMDD)
        # Check type
        if df_base["entry_date"].dtype != 'int64':
             # Try parse
             pass 
    elif "date" in df_base.columns:
        # Orders format
        df_base["entry_date"] = df_base["date"]
    
    # Ensure entry_date is int YYYYMMDD
    df_base["entry_date"] = df_base["entry_date"].astype(str).str.replace("-", "").astype(int)
    df_new["entry_date"] = df_new["entry_date"].astype(str).str.replace("-", "").astype(int)
    
    # Group by date
    dates_base = sorted(df_base["entry_date"].unique())
    dates_new = sorted(df_new["entry_date"].unique())
    all_dates = sorted(list(set(dates_base) | set(dates_new)))
    
    print("\n[Date-by-Date Symbol Jaccard]")
    for d in all_dates:
        syms_base = set(df_base[df_base["entry_date"] == d]["symbol"].astype(str))
        syms_new = set(df_new[df_new["entry_date"] == d]["symbol"].astype(str))
        
        intersect = len(syms_base & syms_new)
        union = len(syms_base | syms_new)
        jaccard = intersect / union if union > 0 else 1.0
        
        print(f"{d}: Base({len(syms_base)}) vs New({len(syms_new)}) -> Jaccard {jaccard:.2f}")
        
        if jaccard < 1.0:
            print(f"   Diff: Base-New={syms_base-syms_new}, New-Base={syms_new-syms_base}")

    # Cost Analysis if columns exist
    # If trades df has net_return/cost?
    # New trades has net_return. Base might not.
    # We can check simple cost per trade if possible.
    
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True)
    parser.add_argument("--new", required=True)
    args = parser.parse_args()
    
    analyze_mismatch(Path(args.base), Path(args.new))
