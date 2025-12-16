import json
import subprocess
import sys
import pandas as pd
from pathlib import Path
from datetime import datetime
import time

def load_universe():
    path = Path("config/universe_top50.json")
    if not path.exists():
        print("Universe file not found.")
        return []
    with open(path, "r") as f:
        return json.load(f)

def run_verify(symbol, days=365):
    print(f"[{symbol}] Running 1-Year Map ({days} days)...")
    try:
        # Run verify_turbo_v3.py
        result = subprocess.run(
            [sys.executable, "scripts/verify_turbo_v3.py", "--symbol", symbol, "--days", str(days)],
            capture_output=True, text=True, check=True
        )
        # Parse stdout for report path
        # Look for: [SSOT] Report generated at: ...
        report_dir = None
        for line in result.stdout.splitlines():
            if "[SSOT] Report generated at: " in line:
                report_dir = line.split(": ")[1].strip()
                break
        
        return report_dir
    except subprocess.CalledProcessError as e:
        print(f"[{symbol}] Failed: {e}")
        print(e.stderr)
        return None

def analyze_report(report_dir):
    if not report_dir:
        return None
        
    p = Path(report_dir) / "report.json"
    if not p.exists():
        # Maybe verify_turbo_v3 names it differently inside the dir?
        # It calls write_report_bundle which makes report.json usually.
        # Check for any .json
        jsons = list(Path(report_dir).glob("*.json"))
        if jsons:
            p = jsons[0]
        else:
            return None
            
    with open(p, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    edge = data["edge_analysis"]
    over = edge["overall"]
    
    return {
        "symbol": data["meta"]["data"]["universe"],
        "expectancy_net": over["expectancy_net"],
        "trades": over["trades"],
        "win_rate": over["win_rate"],
        "cost_avg": over["cost_per_trade_avg"],
        "mdd": over.get("mdd", 0.0),
        "tags": ", ".join(edge["collapse_tags"]),
        "integrity_check": "PASS" if abs(over["net_pnl_total"] - (over["expectancy_net"]*over["trade_sum_net_return"]) < 0.1) else "WARN" # Rough check logic
    }

import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=0, help="Limit number of symbols")
    parser.add_argument("--days", type=int, default=365, help="Simulation days")
    args = parser.parse_args()

    universe = load_universe()
    if args.limit > 0:
        universe = universe[:args.limit]
        
    results = []
    
    start_total = time.time()
    
    for i, sym in enumerate(universe):
        print(f"Processing {i+1}/{len(universe)}: {sym}")
        report_dir = run_verify(sym, days=args.days)
        
        if report_dir:
            metrics = analyze_report(report_dir)
            if metrics:
                results.append(metrics)
        else:
            print(f"[{sym}] No report generated.")
            
    elapsed = time.time() - start_total
    print(f"Batch Complete in {elapsed:.1f}s")
    
    if results:
        df = pd.DataFrame(results)
        out_path = Path("results/edge_map_1y_summary.csv")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(out_path, index=False)
        print(f"Saved Edge Map to: {out_path}")
        print(df.describe())
    else:
        print("No results collected.")

if __name__ == "__main__":
    main()
