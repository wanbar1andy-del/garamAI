# scripts/phase24/merge_flow_close.py
import pandas as pd
import numpy as np
import argparse
from pathlib import Path

def load_flow(csv_path: Path):
    # Load flow data (date, prog_net_buy_vol, prog_net_buy_amt)
    df = pd.read_csv(csv_path, dtype=str)
    # Rename cols for consistency if needed, or stick to KR names
    # Assuming columns: 일자, 프로그램순매수수량, 프로그램순매수금액
    df['date'] = pd.to_datetime(df['일자'], format='%Y%m%d')
    df['prog_amt'] = df['프로그램순매수금액'].astype(float)
    df = df.sort_values('date').set_index('date')
    return df[['prog_amt']]

def calc_regime(df_flow, window=20):
    # Calculate rolling Z-Score
    # mean, std
    r = df_flow['prog_amt'].rolling(window=window)
    m = r.mean()
    s = r.std()
    df_flow['z_score'] = (df_flow['prog_amt'] - m) / (s + 1e-9)
    return df_flow

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--flow_csv", required=True, help="Path to Program Flow CSV")
    ap.add_argument("--out_csv", required=True, help="Path to save Metrics CSV")
    ap.add_argument("--window", type=int, default=20)
    args = ap.parse_args()
    
    flow_path = Path(args.flow_csv)
    out_path = Path(args.out_csv)
    
    print(f"[MERGE] Loading {flow_path}...")
    df = load_flow(flow_path)
    
    # Calculate Z-Score
    print(f"[MERGE] Calculating Z-Score (window={args.window})...")
    df = calc_regime(df, window=args.window)
    
    # Save
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.reset_index().to_csv(out_path, index=False)
    print(f"[MERGE] Saved metrics to {out_path}")
    print(df.tail())

if __name__ == "__main__":
    main()
