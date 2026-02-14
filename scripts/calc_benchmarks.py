import pandas as pd
import numpy as np
from pathlib import Path
import json
from datetime import datetime
from scripts.load_minute_robust import MinuteDataLoader

def calculate_benchmarks(start_str, end_str, universe_csv, minute_dir, out_path):
    print(f"[Benchmarks] Period: {start_str} ~ {end_str}")
    
    loader = MinuteDataLoader(minute_dir)
    universe = pd.read_csv(universe_csv)
    # Check column "Code" or "symbol"
    col = "Code" if "Code" in universe.columns else "symbol"
    symbols = universe[col].astype(str).str.zfill(6).tolist()
    
    start_dt = datetime.strptime(start_str, "%Y%m%d")
    end_dt = datetime.strptime(end_str, "%Y%m%d")
    eod_end = end_dt + pd.Timedelta(days=1) # coverage
    
    # 1. Single Name: 005930 (Samsung Elec)
    # Check if in universe?
    if "005930" not in symbols:
        print("[WARN] 005930 not in universe. Trying to load anyway...")
        samsung_sym = "005930"
    else:
        samsung_sym = "005930"
        
    # Calculate Daily Returns for Samsung
    samsung_metrics = calc_single_stock(loader, samsung_sym, start_dt, end_dt)
    
    # 2. Universe Equal Weight
    # We need daily returns for ALL symbols.
    # To save memory/time, we can process symbol by symbol and accumulate sums?
    # Daily Return = (Close_t / Close_t-1) - 1.
    # We need a common index of "Trading Days".
    
    # First, get trading days from Samsung (most reliable)
    if samsung_metrics:
        trading_days = samsung_metrics["dates"]
    else:
        # Fallback query
        print("[WARN] Samsung metrics failed. Trying first symbol in universe.")
        df, _ = loader.load_symbol(symbols[0], lookback_days=400)
        mask = (df["dt"] >= start_dt) & (df["dt"] <= eod_end)
        df = df[mask].copy()
        df["date_only"] = df["dt"].dt.date
        trading_days = sorted(df["date_only"].unique())
        
    date_map = {d: i for i, d in enumerate(trading_days)}
    n_days = len(trading_days)
    
    sum_returns = np.zeros(n_days)
    count_returns = np.zeros(n_days)
    
    print(f"[Benchmarks] Processing {len(symbols)} symbols for Universe EW...")
    
    processed = 0
    for sym in symbols:
        df, _ = loader.load_symbol(sym, lookback_days=400)
        if df.empty: continue
        
        # Filter range
        mask = (df["dt"] >= start_dt) & (df["dt"] <= eod_end)
        sub = df[mask].copy()
        if sub.empty: continue
        
        # Resample to Daily Close
        sub["date_only"] = sub["dt"].dt.date
        daily = sub.groupby("date_only")["close"].last()
        
        # Calculate pct_change
        rets = daily.pct_change().dropna()
        
        # Accumulate
        for d, r in rets.items():
            if d in date_map:
                idx = date_map[d]
                sum_returns[idx] += r
                count_returns[idx] += 1
                
        processed += 1
        if processed % 50 == 0:
            print(f"  Processed {processed}...")
            
    # Compute Avg
    # Avoid div by zero
    valid_mask = count_returns > 0
    avg_returns = np.zeros(n_days)
    avg_returns[valid_mask] = sum_returns[valid_mask] / count_returns[valid_mask]
    
    # Compute Cumulative
    # Start at 1.0 (Day 0 is start). Returns start from Day 1.
    # index 0 matches date 0.
    # pct_change gives return for Day i (vs i-1).
    # If using date_map logic, rets[d] is return ON day d.
    # We apply it to equity.
    
    cumulative = [1.0]
    for r in avg_returns: # This array logic might be offset by 1?
        # rets.items() has dates.
        # If trading_days[0] is Nov 18.
        # pct_change is NaN for Nov 18 (no prev).
        # So rets has Nov 19, 20...
        # So avg_returns[0] (Nov 18) should be 0? Or NaN?
        # My loop: `for d, r in rets.items():`.
        # Nov 18 is not in rets.
        # Nov 19 is.
        # So avg_returns[date_map[Nov 19]] has value.
        # We start equity at 1.0 on Nov 18.
        pass
        
    cumulative = 1.0
    eq_curve = []
    
    # Re-align:
    # trading_days[0] = Start (Nov 18). Equity 1.0.
    # trading_days[1] = Nov 19. Return is avg_returns[1].
    # Equity[1] = Equity[0] * (1 + avg_returns[1]).
    
    for i in range(n_days):
        if i == 0:
            eq_curve.append({"date": trading_days[i].strftime("%Y-%m-%d"), "equity": 1.0})
        else:
            r = avg_returns[i]
            cumulative *= (1 + r)
            eq_curve.append({"date": trading_days[i].strftime("%Y-%m-%d"), "equity": cumulative})
            
    # Calculate Metrics for Univ EW
    final_eq = eq_curve[-1]["equity"]
    univ_ret = (final_eq - 1.0) * 100
    
    # Quick MDD
    eqs = [e["equity"] for e in eq_curve]
    peak = -99999
    mdd = 0
    for e in eqs:
        if e > peak: peak = e
        dd = (e - peak) / peak
        if dd < mdd: mdd = dd
    univ_mdd = mdd * 100
    
    results = {
        "metrics": {
            "Universe_EW": {
                "return_pct": univ_ret,
                "mdd_pct": univ_mdd
            },
            "Single_Name_005930": samsung_metrics["metrics"] if samsung_metrics else None
        },
        "universe_equity": eq_curve,
        "samsung_equity": samsung_metrics["equity"] if samsung_metrics else None
    }
    
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"[Benchmarks] Saved to {out_path}")
    print(f"  Univ EW: {univ_ret:.2f}%")
    if samsung_metrics:
        print(f"  Samsung: {samsung_metrics['metrics']['return_pct']:.2f}%")

def calc_single_stock(loader, symbol, start_dt, end_dt):
    eod_end = end_dt + pd.Timedelta(days=1)
    df, _ = loader.load_symbol(symbol, lookback_days=400)
    if df.empty: return None
    
    mask = (df["dt"] >= start_dt) & (df["dt"] <= eod_end)
    sub = df[mask].copy()
    if sub.empty: return None
    
    sub["date_only"] = sub["dt"].dt.date
    daily = sub.groupby("date_only")["close"].last()
    
    dates = daily.index.tolist()
    prices = daily.values
    
    # Start price and End price
    start_p = prices[0]
    end_p = prices[-1]
    ret = (end_p / start_p - 1) * 100
    
    # MDD
    peak = prices[0]
    mdd = 0
    cumulative = prices / prices[0]
    
    eq_curve = []
    
    peak = -9999
    dd_max = 0
    
    for i, d in enumerate(dates):
        p = prices[i]
        val = p / start_p
        check_p = val
        if check_p > peak: peak = check_p
        dd = (check_p - peak) / peak
        if dd < dd_max: dd_max = dd
        eq_curve.append({"date": d.strftime("%Y-%m-%d"), "equity": val})
        
    return {
        "metrics": {"return_pct": ret, "mdd_pct": dd_max * 100},
        "equity": eq_curve,
        "dates": dates
    }

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", required=True)
    parser.add_argument("--end", required=True)
    parser.add_argument("--universe", required=True)
    parser.add_argument("--minute_dir", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    
    calculate_benchmarks(args.start, args.end, args.universe, args.minute_dir, args.out)
