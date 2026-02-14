import argparse
import pandas as pd
from pathlib import Path
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
# from tqdm import tqdm (Removed for 32-bit compat)

def audit_symbol(args):
    """
    Worker function to check a single symbol CSV.
    Returns dict of stats.
    """
    path, symbol = args
    try:
        if not path.exists():
            return {"symbol": symbol, "status": "MISSING", "rows": 0}
            
        # Read header and some rows
        df = pd.read_csv(path, usecols=["date", "open", "close", "volume"], dtype={"date": str})
        
        if df.empty:
            return {"symbol": symbol, "status": "EMPTY", "rows": 0}
            
        # 1. Quantity
        n_rows = len(df)
        
        # 2. Time
        dates = df["date"]
        start_date = dates.min()[:8] # YYYYMMDD
        end_date = dates.max()[:8]
        
        # 3. Consistency
        open_zeros = (pd.to_numeric(df["open"], errors='coerce').fillna(0) == 0).sum()
        
        # 4. Sorting
        is_sorted = dates.is_monotonic_increasing
        
        return {
            "symbol": symbol,
            "status": "OK",
            "rows": n_rows,
            "start": start_date,
            "end": end_date,
            "open_zeros": open_zeros,
            "sorted": is_sorted
        }
    except Exception as e:
        return {"symbol": symbol, "status": "ERROR", "reason": str(e)}

def calculate_expected_rows(start_date, end_date):
    return 0

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--universe", default="GARAM_Data/real_universe_400.csv")
    parser.add_argument("--data_dir", default="GARAM_Data/history/minute")
    args = parser.parse_args()
    
    univ_path = Path(args.universe)
    data_dir = Path(args.data_dir)
    
    if not univ_path.exists():
        print(f"[FAIL] Universe not found: {univ_path}")
        sys.exit(1)
        
    df_univ = pd.read_csv(univ_path)
    # Flexible column selection
    col_name = "Code" if "Code" in df_univ.columns else "symbol"
    symbols = [str(s).zfill(6) for s in df_univ[col_name]]
    
    print(f"[AUDIT] Checking {len(symbols)} symbols in {data_dir}...")
    
    tasks = []
    for sym in symbols:
        p = data_dir / f"{sym}.csv"
        tasks.append((p, sym))
        
    results = []
    # Use parallel processing
    with ProcessPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(audit_symbol, t): t[1] for t in tasks}
        
        print(f"[AUDIT] Scanning {len(tasks)} files...", flush=True)
        completed_count = 0
        for future in as_completed(futures):
            res = future.result()
            results.append(res)
            completed_count += 1
            if completed_count % 50 == 0:
                print(f"  Processed {completed_count}/{len(tasks)}", flush=True)
            
    # Aggregate
    df_res = pd.DataFrame(results)
    
    total_files = len(symbols)
    missing = df_res[df_res["status"] == "MISSING"]
    empty = df_res[df_res["status"] == "EMPTY"]
    ok = df_res[df_res["status"] == "OK"]
    
    print("\n" + "="*50)
    print(" 1-YEAR DATA AUDIT REPORT")
    print("="*50)
    print(f"Total Symbols: {total_files}")
    print(f"Available (OK): {len(ok)}")
    print(f"Missing: {len(missing)}")
    print(f"Empty: {len(empty)}")
    
    if not ok.empty:
        avg_rows = ok["rows"].mean()
        min_start = ok["start"].min()
        max_end = ok["end"].max()
        unsorted = ok[~ok["sorted"]]
        
        print(f"\n[Stats]")
        print(f"Avg Rows: {avg_rows:,.0f} (Approx 1 year ~ 90k-100k mins needed)")
        print(f"Global Range: {min_start} ~ {max_end}")
        
        if not unsorted.empty:
            print(f"\n[WARN] Unsorted Files Detected: {len(unsorted)}")
            print(unsorted[["symbol", "rows"]].head())
        
        # Zero Open Check
        bad_open = ok[ok["open_zeros"] > 0]
        if not bad_open.empty:
            print(f"\n[WARN] Symbols with Missing Open Prices (Zeros): {len(bad_open)}")
            print(bad_open[["symbol", "open_zeros", "rows"]].sort_values("open_zeros", ascending=False).head())
        
        # Save Report
        out_path = Path("results/audit/data_quality_report_1y.csv")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        df_res.to_csv(out_path, index=False)
        print(f"\n[Saved] Detailed report to {out_path}")
        
        # Pass/Fail Criteria
        if len(missing) < 5 and len(unsorted) == 0:
            print("\n[VERDICT] DATA IS USABLE (With minor caveats if any)")
        else:
            print("\n[VERDICT] DATA REQUIRES ATTENTION")

if __name__ == "__main__":
    main()
