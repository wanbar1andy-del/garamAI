import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Setup Paths
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))
mining_dir = project_root / "results" / "mining" / "week1"

def analyze_features(filename, target_name):
    path = mining_dir / filename
    if not path.exists():
        print(f"File not found: {filename}")
        return

    df = pd.read_csv(path)
    print(f"\n[{target_name} Analysis] Total Samples: {len(df)}")
    
    # Split by Label
    pos = df[df['label'] == 1]
    neg = df[df['label'] == 0]
    
    features = ['vol_accel', 'vwap_div', 'roc_5m']
    
    print(f"Positive (Event): {len(pos)} | Negative (Control): {len(neg)}")
    
    for feat in features:
        print(f"\n>>> Feature: {feat}")
        p_mean = pos[feat].mean()
        n_mean = neg[feat].mean()
        p_std = pos[feat].std()
        
        print(f"  Pos Mean: {p_mean:.4f} (+/- {p_std:.4f})")
        print(f"  Neg Mean: {n_mean:.4f}")
        print(f"  Delta: {p_mean - n_mean:.4f}")
        
        # Percentiles
        print(f"  Pos [25%, 50%, 75%]: {np.percentile(pos[feat], [25, 50, 75])}")
        print(f"  Neg [25%, 50%, 75%]: {np.percentile(neg[feat], [25, 50, 75])}")

def run_analysis():
    analyze_features("mining_birth_features.csv", "Birth (Entry)")
    analyze_features("mining_death_features.csv", "Death (Exit)")

if __name__ == "__main__":
    run_analysis()
