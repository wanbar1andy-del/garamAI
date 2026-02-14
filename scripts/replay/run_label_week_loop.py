import sys
import subprocess
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta

# Setup Paths
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

def run_week1_loop():
    # Target Range: 2025-12-15 (Mon) ~ 2025-12-19 (Fri)
    # Check if data exists for these dates first
    start_date = pd.Timestamp("2025-12-15")
    end_date = pd.Timestamp("2025-12-19")
    
    current = start_date
    results_map = {}
    
    print(f"=== Week-1 Label Loop ({start_date.date()} ~ {end_date.date()}) ===")
    
    while current <= end_date:
        d_str = current.strftime("%Y-%m-%d")
        print(f"\n>> Processing {d_str}...")
        
        # Call Subprocess (Memory Safety)
        cmd = [sys.executable, "-m", "scripts.replay.run_label_day1", "--date", d_str]
        try:
            subprocess.run(cmd, check=True, cwd=str(project_root))
            results_map[d_str] = "DONE"
        except subprocess.CalledProcessError:
            print(f"  [ERR] Failed {d_str}")
            results_map[d_str] = "FAIL"
            
        current += timedelta(days=1)
        
    print("\n=== Loop Complete ===")
    print(results_map)
    
    # Consolidate
    consolidate_week(start_date, end_date)

def consolidate_week(start, end):
    print("\n[Consolidating Reports...]")
    all_ranks = []
    
    current = start
    while current <= end:
        ymd = current.strftime("%Y%m%d")
        rank_path = project_root / "results" / "labels" / f"day={ymd}" / "hero_rank.csv"
        if rank_path.exists():
            df = pd.read_csv(rank_path)
            df['date'] = current.strftime("%Y-%m-%d")
            all_ranks.append(df)
        current += timedelta(days=1)
        
    if all_ranks:
        df_week = pd.concat(all_ranks, ignore_index=True)
        out_path = project_root / "results" / "reports" / "week_hero_summary.csv"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        df_week.to_csv(out_path, index=False)
        print(f"Saved Consolidated Report: {out_path}")
        print(f"Total Segments: {len(df_week)}")
        
        # Simple Stats
        print("\n[Week-1 Stats]")
        print(f"Avg Segment Score: {df_week['segment_score'].mean():.3f}")
        print(f"Max Segment Score: {df_week['segment_score'].max():.3f}")
        print(f"Avg Duration: {df_week['duration_min'].mean():.1f} min")
        
        # Most Frequent Heroes
        print("\n[Top Frequent Heroes]")
        print(df_week['symbol'].value_counts().head(5))

if __name__ == "__main__":
    run_week1_loop()
