# scripts/verify_alpha_tuning.py
# ALPHA_TUNING_ROBUST
# Date: 2025-12-15
# Purpose: Tune k-factor and test Floor Logic with Dynamic Buckets and Robust Logging.

from __future__ import annotations

import sys
import shutil
from pathlib import Path
import pandas as pd
import numpy as np

# Allow importing from parent
sys.path.append(str(Path(__file__).resolve().parents[1]))

from garam_core.replay.replay_runner import run_replay, ReplaySpec
from garam_core.engine.regime import RegimeParams
from garam_core.engine.signal import SignalParams
from garam_core.engine.turbo import TurboParams
from garam_core.execution.fill_model import FillSpec
from garam_core.execution.cost_model import CostModel

TOP_10 = [
    "005930", "000660", "373220", "207940", "005380",
    "000270", "005490", "035420", "006400", "051910"
]

def find_project_root(start: Path) -> Path:
    p = start.resolve()
    for _ in range(10):
        if (p / "garam_core" / "config" / "paths.yaml").exists():
            return p / "garam_core"
        if (p / "config" / "paths.yaml").exists():
            return p
        p = p.parent
    fallback = Path("c:/garam/garam/garam_core")
    if (fallback / "config" / "paths.yaml").exists():
        return fallback
    raise FileNotFoundError("config/paths.yaml not found.")

def calc_dynamic_buckets(symbols, project_root):
    """
    Load recent stats for symbols and assign Low/Mid/High buckets based on Volatility.
    Robust data path search.
    """
    print(">>> CALCULATING DYNAMIC BUCKETS <<<", flush=True)
    
    # Potential paths
    candidates = [
        Path("g:/내 드라이브/garamdata/primary/minute"),
        project_root.parent / "GARAM_Data/primary/minute",
        project_root.parent.parent / "GARAM_Data/primary/minute",
        Path("c:/garam/GARAM_Data/primary/minute")
    ]
    
    data_dir = None
    for p in candidates:
        if p.exists():
            data_dir = p
            print(f"Found Data Dir: {data_dir}", flush=True)
            break
            
    stats = []
    if not data_dir:
        print("WARNING: Could not find primary/minute data for buckets. Using default 'Unknown'.", flush=True)
        return {s: "Unknown" for s in symbols}
    
    for sym in symbols:
        try:
             csv_path = data_dir / f"{sym}.csv"
             if not csv_path.exists():
                 stats.append({"symbol": sym, "vol": 0.0})
                 continue
                 
             # Fast approach: Read tail 5000
             df = pd.read_csv(csv_path, usecols=["close", "date"], parse_dates=['date']).tail(5000)
             vol = df['close'].pct_change().std()
             stats.append({"symbol": sym, "vol": vol})
             
        except Exception as e:
            print(f"Failed to load {sym}: {e}", flush=True)
            stats.append({"symbol": sym, "vol": 0.0})

    if not stats:
        return {s: "Unknown" for s in symbols}

    df = pd.DataFrame(stats)
    # If all vol are 0, return Unknown
    if df['vol'].sum() == 0:
         print("All volatilities 0.0. Buckets Unknown.", flush=True)
         return {s: "Unknown" for s in symbols}

    df = df.sort_values("vol")
    
    # Percentiles
    low_cut = df['vol'].quantile(0.33)
    high_cut = df['vol'].quantile(0.66)
    
    def get_bucket(v):
        if v <= low_cut: return "Low"
        if v <= high_cut: return "Mid"
        return "High"
        
    df['bucket'] = df['vol'].apply(get_bucket)
    print(df[['symbol', 'vol', 'bucket']], flush=True)
    return df.set_index("symbol")['bucket'].to_dict()


def run_batch(name, signal_params, symbols, buckets, project_root, collect_debug=False):
    print(f"\n>>> RUNNING BATCH: {name} (Debug={collect_debug}) <<<", flush=True)
    
    regime_params = RegimeParams(ma_fast=120, ma_slow=480, bear_buffer=-0.002)
    turbo_params = TurboParams(max_multiplier=2.0)
    cost_model = CostModel(commission_rate=0.00015, slippage_rate=0.00020, sell_tax_rate=0.00230)
    
    results = []
    
    for i, sym in enumerate(symbols):
        # Flush progress every symbol
        print(f"[{i+1}/{len(symbols)}] Processing {sym}...", end="", flush=True)
        
        replay_spec = ReplaySpec(
            symbol=sym,
            timeframe="minute",
            timezone="Asia/Seoul",
            warmup_bars=600,
            fill=FillSpec(method="NEXT_OPEN"),
            cost=cost_model,
            base_multiplier=1.0,
            max_bars=60 * 381, 
        )
        
        try:
            res = run_replay(
                project_root=project_root,
                replay=replay_spec,
                regime_params=regime_params,
                signal_params=signal_params,
                turbo_params=turbo_params,
                initial_equity=100_000_000.0,
                collect_debug=collect_debug
            )
            
            metrics = res.metrics
            trades = res.trades
            days = pd.Series(res.equity_curve.index.date).nunique()
            tpd = float(len(trades) / max(1, days))
            
            row = {
                "experiment": name,
                "symbol": sym,
                "bucket": buckets.get(sym, "Unknown"),
                "ret": metrics['total_return'],
                "tpd": tpd,
                "win_rate": metrics.get("win_rate", 0.0)
            }
            results.append(row)
            print(f" Ret: {row['ret']*100:>6.2f}% | TPD: {tpd:.2f}", flush=True)
            
            if collect_debug and res.debug_rows:
                debug_p = Path(f"results/tuning_debug/{name}_{sym}_debug.csv")
                debug_p.parent.mkdir(parents=True, exist_ok=True)
                pd.DataFrame(res.debug_rows).to_csv(debug_p, index=False)
                
        except Exception as e:
            print(f" FAIL: {e}", flush=True)
            
    return results

def main():
    project_root = find_project_root(Path(__file__))
    
    # Ensure results dir
    (Path(project_root).parent / "results").mkdir(parents=True, exist_ok=True)
    (Path(project_root).parent / "results/tuning_debug").mkdir(parents=True, exist_ok=True)
    
    # 0. Calculate Buckets
    buckets = calc_dynamic_buckets(TOP_10, project_root)
    
    all_results = []
    
    # NOTE: Params for cooldown clamp are now SignalParams defaults or user overrides
    # verify_alpha_tuning should use consistent params.
    
    base_params = {
        "cooldown_bars": 120,
        "cooldown_min": 30,
        "cooldown_max": 360,
        "vol_lookback": 20,
        "use_vol_scaled_cooldown": True,
        "cooldown_target_vol": 0.001
    }

    # Phase 1: DIAG (Samsung + Hynix)
    # Goal: Verify logic inputs (zscore, floor, cooldown_used)
    print("\n=== PHASE 1: DIAGNOSTIC RUN ===", flush=True)
    diag_params = SignalParams(
        **base_params,
        use_vol_scaled_momentum=True,
        min_momentum_k=1.0,
        abs_momentum_floor=0.002
    )
    # Run only 2 symbols
    run_batch("DIAG_FLOOR", diag_params, ["005930", "000660"], buckets, project_root, collect_debug=True)
    
    # Phase 2: GRID (Sensitivity K=1.0, 1.5, 2.0 + Floor 0.2%)
    print("\n=== PHASE 2: TUNING GRID ===", flush=True)
    
    configs = [
        ("K1.0_NO_FLOOR", 1.0, 0.0),
        ("K1.5_NO_FLOOR", 1.5, 0.0), # Sensitivity test
        ("K2.0_NO_FLOOR", 2.0, 0.0), # Sensitivity test
        ("K1.0_FLOOR_0.2", 1.0, 0.002) # Hardening test
    ]
    
    for name, k, floor in configs:
        p = SignalParams(
            **base_params,
            use_vol_scaled_momentum=True,
            min_momentum_k=k,
            abs_momentum_floor=floor
        )
        batch_res = run_batch(name, p, TOP_10, buckets, project_root, collect_debug=False)
        all_results.extend(batch_res)
        
    # Generate Report
    df = pd.DataFrame(all_results)
    df.to_csv("results/alpha_tuning_raw.csv", index=False)
    
    # Pivot Summary
    pivot = df.pivot_table(index=["bucket", "symbol"], columns="experiment", values="ret", aggfunc='mean') * 100
    pivot_tpd = df.pivot_table(index=["bucket", "symbol"], columns="experiment", values="tpd", aggfunc='mean')
    
    print("\n>>> PIVOT RESULT (RETURN %) <<<", flush=True)
    print(pivot.round(2), flush=True)
    
    pivot.to_csv("results/alpha_tuning_pivot.csv")
    
    # Markdown Report Gen
    generate_markdown_report(df, pivot, pivot_tpd)


def generate_markdown_report(df, pivot, pivot_tpd):
    path = "results/alpha_tuning_results.md"
    
    with open(path, "w", encoding="utf-8") as f:
        f.write("# Alpha Tuning Results (Bucket-Adaptive)\n\n")
        f.write("**Date:** 2025-12-15\n")
        f.write("**Scope:** Top 10 Liquid Assets (60 Days)\n\n")
        
        f.write("## 1. Bucket Distribution\n")
        # Bucket stats
        b_summary = df.groupby("bucket")["symbol"].unique().apply(lambda x: list(x))
        f.write(f"```\n{b_summary}\n```\n\n")
        
        f.write("## 2. Experiment Results (Return %)\n")
        f.write("Hypothesis:\n")
        f.write("- **Low Vol:** Needs Floor (K1.0_FLOOR) or High K (K2.0) to filter noise.\n")
        f.write("- **High Vol:** Needs Low K (K1.0) to capture alpha.\n\n")
        
        f.write(pivot.round(2).to_markdown())
        
        f.write("\n\n## 3. Experiment Results (TPD)\n")
        f.write(pivot_tpd.round(2).to_markdown())
        
        f.write("\n\n## 4. Conclusion\n")
        f.write("- **Samsung (Low Vol):** Check 'K1.0_FLOOR_0.2' vs 'K2.0'. Goal: Return > 0.\n")
        f.write("- **Hynix (High Vol):** Check 'K1.0' stability. Goal: Return > 40%.\n")
        f.write("- **Recommendation:** Pick the config that maximizes Low-Vol safety without killing High-Vol alpha.\n")
    
    print(f"Report generated: {path}", flush=True)

if __name__ == "__main__":
    main()
