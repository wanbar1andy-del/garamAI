import argparse
import pandas as pd
from pathlib import Path
import subprocess
import json
import sys
from datetime import datetime, timedelta

def run_walkforward(start_year, start_month, months, universe, minute_dir):
    results = []
    
    current_date = datetime(start_year, start_month, 18) # Anchored to 18th
    
    for i in range(months):
        start_str = current_date.strftime("%Y%m%d")
        # 1 Month duration
        end_date = current_date + timedelta(days=30)
        end_str = end_date.strftime("%Y%m%d")
        
        print(f"\n[WalkForward] Month {i+1}/{months}: {start_str} ~ {end_str}")
        
        # 1. Run Replay (HOLD_1D)
        cmd_replay = [
            sys.executable, "-m", "scripts.replay_1month_test",
            "--start", start_str, "--end", end_str,
            "--universe", universe, "--minute_dir", minute_dir,
            "--exit", "HOLD_1D", "--cost_bps", "30"
        ]
        
        try:
            # Capture output to find Run ID
            proc = subprocess.run(cmd_replay, capture_output=True, text=True, check=True)
            output = proc.stdout
            
            # Parse Run ID
            run_id = None
            for line in output.splitlines():
                if "Run ID:" in line:
                    run_id = line.split("Run ID:")[-1].strip()
                    break
            
            if not run_id:
                print(f"[FAIL] Could not parse Run ID for month {i+1}")
                continue
                
            metrics_path = Path(f"results/replay/{run_id}/equity_curve.csv") # Used for verify
            
            # Verify Metrics
            verify_out = Path(f"results/replay/{run_id}/metrics_verified.json")
            cmd_verify = [
                sys.executable, "-m", "scripts.verify_replay_metrics",
                "--equity", str(metrics_path), "--out", str(verify_out)
            ]
            subprocess.run(cmd_verify, check=True, capture_output=True)
            
            with open(verify_out, "r") as f:
                metrics = json.load(f)
                
            # 2. Run Benchmark
            bench_out = Path(f"results/replay/{run_id}/benchmarks.json")
            cmd_bench = [
                sys.executable, "-m", "scripts.calc_benchmarks",
                "--start", start_str, "--end", end_str,
                "--universe", universe, "--minute_dir", minute_dir,
                "--out", str(bench_out)
            ]
            subprocess.run(cmd_bench, check=True, capture_output=True)
            
            with open(bench_out, "r") as f:
                bench = json.load(f)
                
            # data
            univ_ret = bench["metrics"]["Universe_EW"]["return_pct"] if bench["metrics"]["Universe_EW"] else 0.0
            samsung = bench["metrics"].get("Single_Name_005930")
            samsung_ret = samsung["return_pct"] if samsung else 0.0
            engine_ret = metrics["total_return_pct"]
            
            # Verdict
            beat_univ = engine_ret > univ_ret
            beat_samsung = engine_ret > samsung_ret
            
            row = {
                "period": f"{start_str}-{end_str}",
                "engine_ret": round(engine_ret, 2),
                "univ_ret": round(univ_ret, 2),
                "samsung_ret": round(samsung_ret, 2),
                "mdd": round(metrics["mdd_pct"], 2),
                "trades": manifest_trades(run_id), # Helper needed
                "beat_market": beat_univ
            }
            results.append(row)
            
            print(f"  Result: Engine {row['engine_ret']}% | Univ {row['univ_ret']}% | Samsung {row['samsung_ret']}%")
            
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] Subprocess failed: {e}")
            print(e.stderr)
            
        # Advance Month
        current_date = end_date # Approximate sliding window
        
    # Save Report
    df = pd.DataFrame(results)
    out_csv = Path("results/walkforward/summary.csv")
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_csv, index=False)
    print(f"\n[WalkForward] Completed. Saved to {out_csv}")
    print(df)

def manifest_trades(run_id):
    try:
        p = Path(f"results/replay/{run_id}/manifest.json")
        with open(p) as f:
            m = json.load(f)
            return m.get("total_trades", 0)
    except:
        return 0

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--months", type=int, default=3)
    # Default to recent history
    parser.add_argument("--start_year", type=int, default=2025)
    parser.add_argument("--start_month", type=int, default=9)
    
    args = parser.parse_args()
    
    # Universe/Data hardcoded or arg?
    # Using defaults from system
    UNIV = "GARAM_Data/real_universe_400.csv"
    MIN_DIR = "GARAM_Data/history/minute"
    
    run_walkforward(args.start_year, args.start_month, args.months, UNIV, MIN_DIR)
