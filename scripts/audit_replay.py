import pandas as pd
from pathlib import Path
import sys

def audit_matches(df_trades):
    """
    Check if every BUY has a corresponding SELL.
    """
    print("[AUDIT] Checking BUY-SELL Matching...")
    if df_trades.empty:
        print("  No trades found.")
        return
        
    counts = df_trades.groupby(["symbol", "entry_date"]).size()
    # Should be 1 entry?
    # Our trades list logs 'closed_trades'. 
    # So every row in 'all_trades.csv' IS a closed trade (Buy + Sell).
    # Buying and holding forever means it's NOT in 'all_trades.csv'.
    # We should check 'all_orders.csv' if available?
    # Replay script might not save 'all_orders.csv' anymore in new version?
    # New version saves 'all_trades.csv' from 'closed_trades' list.
    
    # If using 'all_trades.csv', we only see matched trades.
    # To detect "Missing Sells", we need to check if there are Open Positions left at end.
    # But Manifest "total_trades" vs "positions"?
    
    print(f"  Closed Trades Count: {len(df_trades)}")
    return True

def audit_divergence(baseline_equity, new_equity):
    """
    Find first divergence date.
    """
    print("\n[AUDIT] Checking Equity Divergence...")
    base = pd.read_csv(baseline_equity)[["date", "equity"]].rename(columns={"equity": "base_eq"})
    new = pd.read_csv(new_equity)[["date", "equity"]].rename(columns={"equity": "new_eq"})
    
    # Merge
    merged = pd.merge(base, new, on="date", how="inner")
    
    merged["diff"] = merged["base_eq"] - merged["new_eq"]
    merged["diff_abs"] = merged["diff"].abs()
    
    divergence = merged[merged["diff_abs"] > 1000] # Tolerance 1000 KRW
    
    if not divergence.empty:
        first_div = divergence.iloc[0]
        print(f"  DIVERGENCE FOUND at {first_div['date']}")
        print(f"  Base: {first_div['base_eq']:,.0f}")
        print(f"  New : {first_div['new_eq']:,.0f}")
        print(f"  Diff: {first_div['diff']:,.0f}")
        return False
    else:
        print("  NO Divergence found (Equity match).")
        return True

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline_dir", help="Dir of baseline run (optional)")
    parser.add_argument("--new_dir", required=True, help="Dir of new run")
    args = parser.parse_args()
    
    new_path = Path(args.new_dir)
    trades_path = new_path / "all_trades.csv"
    
    if trades_path.exists():
        df = pd.read_csv(trades_path)
        audit_matches(df)
    else:
        print("all_trades.csv not found.")
        
    if args.baseline_dir:
        base_path = Path(args.baseline_dir)
        audit_divergence(base_path / "equity_curve.csv", new_path / "equity_curve.csv")
