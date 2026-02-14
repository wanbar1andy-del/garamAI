# scripts/phase25/ops_gate_check.py
# -*- coding: utf-8 -*-
import argparse
from pathlib import Path
import pandas as pd

def norm_symbol(x) -> str:
    s = str(x).strip()
    if s.isdigit():
        s = s.zfill(6)
    return s

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw_opt10059_csv", required=True)
    ap.add_argument("--tape_csv", required=True)
    ap.add_argument("--hold_symbol", default="005930")
    args = ap.parse_args()

    raw_csv = Path(args.raw_opt10059_csv)
    tape_csv = Path(args.tape_csv)
    hold = norm_symbol(args.hold_symbol)

    print("=== Gate A: OPT10059 raw check ===")
    if not raw_csv.exists():
        raise SystemExit(f"ERROR: raw csv not found: {raw_csv}")
        
    df = pd.read_csv(raw_csv)
    if "일자" not in df.columns:
        raise SystemExit("ERROR: raw csv missing '일자'")
    df["date"] = pd.to_datetime(df["일자"].astype(str), format="%Y%m%d", errors="coerce")
    df = df.dropna(subset=["date"]).copy()
    df = df.sort_values("date")
    dup = int(df.duplicated(subset=["date"]).sum())
    dmin, dmax = df["date"].min(), df["date"].max()
    print(f"- rows(raw parsed): {len(df)}")
    print(f"- date range      : {dmin.date()} ~ {dmax.date()}")
    print(f"- dup(date) count : {dup}")
    if dup > 0:
        # 최신행 유지로 dedupe
        df2 = df.drop_duplicates(subset=["date"], keep="last")
        print(f"- dedup rows      : {len(df2)} (keep last)")

    print("\n=== Gate B: decision tape symbol check ===")
    if not tape_csv.exists():
         raise SystemExit(f"ERROR: tape csv not found: {tape_csv}")

    tape = pd.read_csv(tape_csv)
    if "ts" not in tape.columns or "symbol" not in tape.columns or "score" not in tape.columns:
        raise SystemExit("ERROR: tape csv must have ts,symbol,score")
    tape["symbol_norm"] = tape["symbol"].apply(norm_symbol)
    bad_len = int((tape["symbol_norm"].str.len() != 6).sum())
    uniq = tape["symbol_norm"].nunique()
    has_hold = int((tape["symbol_norm"] == hold).any())

    print(f"- rows(tape): {len(tape)}")
    print(f"- uniq symbols: {uniq}")
    print(f"- bad symbol len(!=6): {bad_len}")
    print(f"- hold_symbol({hold}) present: {bool(has_hold)}")

    # 샘플 출력
    print("\n[Sample symbols]")
    print(tape["symbol_norm"].value_counts().head(10).to_string())

    print("\n=== Verdict ===")
    if dup > 0:
        print("WARN: raw csv has duplicate dates -> nightly must sort+dedupe before metrics.")
    if bad_len > 0 or not has_hold:
        print("FAIL: tape symbol normalization issue -> switching can be invalid.")
    else:
        print("OK: symbols look consistent (6-digit) and hold_symbol exists in tape.")

if __name__ == "__main__":
    main()
