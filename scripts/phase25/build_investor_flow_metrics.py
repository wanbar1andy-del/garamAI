# -*- coding: utf-8 -*-
import argparse
from pathlib import Path
import pandas as pd
import numpy as np

def zscore_rolling(s: pd.Series, win: int = 20, minp: int = 5):
    mu = s.rolling(win, min_periods=minp).mean()
    sd = s.rolling(win, min_periods=minp).std().replace(0, np.nan)
    return (s - mu) / sd

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--investor_csv", required=True)      # OPT10059 output
    ap.add_argument("--turnover_csv", required=False)     # optional: date, turnover (or merge_flow_close output)
    ap.add_argument("--out_csv", required=True)
    ap.add_argument("--window", type=int, default=20)
    args = ap.parse_args()

    df = pd.read_csv(args.investor_csv, dtype=str, encoding="utf-8-sig")
    # date normalize
    if "일자" in df.columns:
        df["date"] = pd.to_datetime(df["일자"].astype(str), format="%Y%m%d", errors="coerce")
    elif "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
    else:
        raise RuntimeError("No date key (일자/date) in investor_csv")

    df = df.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)

    # numeric convert (investor flow columns)
    flow_cols = [c for c in df.columns if c not in ("일자", "date")]
    for c in flow_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    # optional turnover merge to normalize by liquidity (unit-robust)
    if args.turnover_csv:
        td = pd.read_csv(args.turnover_csv, encoding="utf-8-sig")
        if "date" not in td.columns:
            if "일자" in td.columns:
                td["date"] = pd.to_datetime(td["일자"].astype(str), format="%Y%m%d", errors="coerce")
            else:
                raise RuntimeError("turnover_csv must have date or 일자")
        else:
            td["date"] = pd.to_datetime(td["date"], errors="coerce")

        # expect turnover column name
        tcol = None
        for cand in ("turnover", "거래대금"):
            if cand in td.columns:
                tcol = cand
                break
        if tcol:
            td = td[["date", tcol]].dropna().rename(columns={tcol: "turnover"})
            df = df.merge(td, on="date", how="left")
        else:
            df["turnover"] = np.nan
    else:
        df["turnover"] = np.nan

    out = pd.DataFrame({"date": df["date"].dt.strftime("%Y-%m-%d")})

    for c in flow_cols:
        s = df[c]
        out[f"{c}_amt"] = s

        # ratio (unit-robust) if turnover exists
        ratio = s / df["turnover"].replace(0, np.nan)
        out[f"{c}_ratio"] = ratio

        # z-scores
        out[f"{c}_z{args.window}"] = zscore_rolling(s, win=args.window)
        out[f"{c}_ratio_z{args.window}"] = zscore_rolling(ratio, win=args.window)

    out_path = Path(args.out_csv)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"[OK] saved {out_path} rows={len(out)}")

if __name__ == "__main__":
    main()
