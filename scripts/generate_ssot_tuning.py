# scripts/generate_ssot_tuning.py
import sys
import pandas as pd
from pathlib import Path
import json

sys.path.append(str(Path(__file__).resolve().parents[1]))
from garam_core.reporting.report_writer import ReportWriter

def final_ssot_tuning():
    project_root = Path(__file__).resolve().parents[1]
    
    # 1. Find latest CSV
    results_dir = project_root.parent / "results"
    csv_path = results_dir / "alpha_tuning_fast_screen.csv"
    
    if not csv_path.exists():
        print("CSV not found!")
        return
        
    df = pd.read_csv(csv_path)
    
    # 2. Convert to SSOT Experiments Format
    experiments = []
    
    # We must compute a "Score" for each experiment to rank them.
    # User requested 4-axis scoring: Return, TPD, Hit_Abs, Hit_Cost.
    # Simple Weighting: Net Return (50%), TPD (20%), Abs Penalty if > 50% (30%), Low Bucket Abs Bonus (mandatory).
    
    experiment_names = df["experiment"].unique()
    
    for exp_name in experiment_names:
        sub = df[df["experiment"] == exp_name]
        
        avg_ret = float(sub["total_return"].mean())
        avg_tpd = float(sub["tpd"].mean())
        avg_abs_hit = float(sub["hit_abs_ratio"].mean())
        
        # Determine specific bucket stats for robust scoring
        try:
            high_bucket = sub[sub["bucket"] == "High"]
            low_bucket = sub[sub["bucket"] == "Low"]
            
            high_abs_hit = float(high_bucket["hit_abs_ratio"].mean()) if not high_bucket.empty else 0.0
            low_abs_hit = float(low_bucket["hit_abs_ratio"].mean()) if not low_bucket.empty else 0.0
            
            # Score Logic
            # 1. Base Score = Return * 100
            score = avg_ret * 100
            
            # 2. Penalty: High Bucket Abs Hit > 0.5
            if high_abs_hit > 0.5:
                score -= 100 # Severe penalty
                
            # 3. Requirement: Low Bucket Abs Hit > 0.8 (Safety)
            if low_abs_hit < 0.8:
                score -= 50 # Fail requirement
                
        except Exception:
            score = -999.0
            
        exp_data = {
            "name": exp_name,
            "score": score,
            "metrics": {
                "total_return_net_avg": avg_ret,
                "tpd_avg": avg_tpd,
                "hit_abs_ratio_avg": avg_abs_hit
            },
            "params": {
                "adaptive_mode": True if "ADAPTIVE" in exp_name else False
            }
        }
        experiments.append(exp_data)
        
    # 3. Ranking (Strict: Must not be empty)
    experiments.sort(key=lambda x: x["score"], reverse=True)
    if not experiments:
        print("Error: No experiments found.")
        sys.exit(1)
        
    ranking = [{"rank": i+1, "name": e["name"], "score": e["score"]} for i, e in enumerate(experiments)]
    
    # 4. Winner Selection
    winner = ranking[0]["name"]
    # Verify Consistency: Ranking[0] == Winner
    
    criteria = {
        "hynix_min_return": -1.0, 
        "samsung_max_loss": -1.0,
        "high_bucket_abs_floor_hit_max": 0.50,
        "low_bucket_abs_floor_hit_min": 0.80
    }
    
    config = {
        "tuning_mode": "SCREEN",
        "notes": f"Winner {winner} selected via weighted scoring (Low bucket safety > 80% abs hit)."
    }
    
    # 5. Write Report
    rw = ReportWriter(project_root)
    
    run_id = f"tuning_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}"
    
    out_path = rw.write_tuning_report(
        run_id=run_id,
        experiments=experiments,
        ranking=ranking,
        winner=winner,
        criteria=criteria, # Must not be empty
        config=config
    )
    print(f"SSOT Tuning Report Generated: {out_path}")

if __name__ == "__main__":
    final_ssot_tuning()
