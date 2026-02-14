# scripts/phase25/prep_paper_ops_flow.py
# -*- coding: utf-8 -*-
import pandas as pd
import argparse
from pathlib import Path
import sys

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw_csv", required=True)
    ap.add_argument("--target_col", default="외국인투자자_ratio_z20")
    ap.add_argument("--out_csv", required=True)
    args = ap.parse_args()

    raw_path = Path(args.raw_csv)
    if not raw_path.exists():
        print(f"[FAIL] raw_csv not found: {raw_path}")
        sys.exit(1)

    df = pd.read_csv(raw_path, encoding="utf-8-sig")
    
    # Check strict equality
    if args.target_col not in df.columns:
        # Fallback check (strip?)
        found = False
        for c in df.columns:
            if c.strip() == args.target_col:
                args.target_col = c
                found = True
                break
        if not found:
            print(f"[FAIL] column '{args.target_col}' not found in {raw_path}")
            print(f"Available cols: {list(df.columns)}")
            sys.exit(2)
        
    # Standardize to date, z_score
    out = df[["date", args.target_col]].copy()
    out = out.rename(columns={args.target_col: "z_score"})
    
    # Ensure dir
    out_path = Path(args.out_csv)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    
    out.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"[OK] Normalized flow saved to: {out_path}")

if __name__ == "__main__":
    main()
