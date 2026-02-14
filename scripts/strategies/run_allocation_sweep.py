
import subprocess
import pandas as pd
from pathlib import Path
import sys

SCRIPT_PATH = "scripts/strategies/simulate_phase4_hero.py"
LOG_DIR = Path("logs/phase4_sweep")

def run_sweep():
    configs = [
        ("FIXED", 0.3),
        ("FIXED", 0.4),
        ("FIXED", 0.5),
        ("FIXED", 0.6),
        ("FIXED", 0.7),
        ("PYRAMID", 0.7)
    ]
    
    results = []
    
    for mode, w in configs:
        print(f"Running {mode} {w}...")
        cmd = [sys.executable, SCRIPT_PATH, "--mode", mode, "--weight", str(w)]
        subprocess.run(cmd, check=True)
        
        # Analyze Result
        suffix = f"{mode}_{w}"
        eq_file = LOG_DIR / f"equity_{suffix}.csv"
        if eq_file.exists():
            df = pd.read_csv(eq_file)
            initial = df['equity'].iloc[0]
            final = df['equity'].iloc[-1]
            ret = (final - initial) / initial
            
            # MDD
            roll_max = df['equity'].cummax()
            dd = (df['equity'] - roll_max) / roll_max
            mdd = dd.min()
            
            mar = ret / abs(mdd) if mdd != 0 else 0
            
            results.append({
                "Mode": mode,
                "MaxWeight": w,
                "Return": ret * 100,
                "MDD": mdd * 100,
                "MAR": mar,
                "FinalEquity": final
            })
            
    # Report
    print("\n=== Allocation Sweep Results ===")
    res_df = pd.DataFrame(results)
    print(res_df.sort_values("MAR", ascending=False).to_string(index=False, float_format="%.2f"))
    
    best = res_df.loc[res_df['MAR'].idxmax()]
    print(f"\nGolden Ratio Found: {best['Mode']} with MaxWeight {best['MaxWeight']}")

if __name__ == "__main__":
    run_sweep()
