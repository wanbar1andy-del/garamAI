# scripts/phase24/switching_sandbox.py
import pandas as pd
import numpy as np
import argparse
from pathlib import Path

def simulate_switching(df, boost_weight=0.0):
    """
    Simulate switching with Flow Booster.
    Assumptions for Sandbox:
    - We have a 'current score' (simulated baseline)
    - We have a 'candidate score' (simulated alternative)
    - Flow Booster affects the Candidate Score (or lowers barrier)
    
    Here we generate dummy scores to prove the logic if real scores aren't provided.
    In real usage, this would attach to the Decision Tape.
    """
    
    np.random.seed(42)
    n = len(df)
    
    # Mocking Decision Tape Data
    # Base Score: 0 ~ 100
    df['score_current'] = np.random.uniform(50, 80, n)
    df['score_candidate'] = df['score_current'] + np.random.normal(0, 5, n) # Candidate is similar (+- noise)
    
    # Default Gap necessary to switch (Cost + buffer)
    GAP_THRESHOLD = 2.0 
    
    # 1. Standard Logic (No Booster)
    # Switch if Candidate > Current + Gap
    df['switch_standard'] = df['score_candidate'] > (df['score_current'] + GAP_THRESHOLD)
    
    # 2. Flow Booster Logic
    # boost = clip(z_score, -2, 2) * weight
    # Adjusted Candidate Score = Candidate + Boost
    # If Inflow (Positive Z), Candidate gets a boost -> Easier to switch TO
    # If Outflow (Negative Z), Candidate gets penalty -> Harder to switch (Hold current)
    # NOTE: This assumes 'Candidate' is the stock with the flow. 
    # If the flow is market-wide, it might apply differently. 
    # Let's assume this Z-score helps Valid Candidates.
    
    df['flow_boost'] = df['z_score'].clip(-2, 2) * boost_weight
    df['score_candidate_boosted'] = df['score_candidate'] + df['flow_boost']
    
    df['switch_boosted'] = df['score_candidate_boosted'] > (df['score_current'] + GAP_THRESHOLD)
    
    return df

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--metrics_csv", required=True)
    ap.add_argument("--weight", type=float, default=5.0, help="Weight for Flow Z-Score Booster")
    args = ap.parse_args()
    
    p = Path(args.metrics_csv)
    if not p.exists():
        print("Metrics file not found")
        return

    df = pd.read_csv(p)
    # Fill NA for calculation
    df['z_score'] = df['z_score'].fillna(0)
    
    print(f"--- Switching Logic Sandbox (Weight={args.weight}) ---")
    
    # Run Simulation
    res = simulate_switching(df.copy(), boost_weight=args.weight)
    
    # Stats
    n_total = len(res)
    n_switch_std = res['switch_standard'].sum()
    n_switch_boost = res['switch_boosted'].sum()
    
    print(f"Total Days: {n_total}")
    print(f"Switches (Standard): {n_switch_std} ({n_switch_std/n_total*100:.1f}%)")
    print(f"Switches (Boosted) : {n_switch_boost} ({n_switch_boost/n_total*100:.1f}%)")
    
    # Impact Analysis
    # Did Inflow regimes trigger more switches?
    inflow_mask = res['z_score'] > 1.0
    outflow_mask = res['z_score'] < -1.0
    
    print("\n[Regime Impact]")
    print(f"Inflow Days (Z>1) Switches: {res.loc[inflow_mask, 'switch_boosted'].sum()} / {inflow_mask.sum()}")
    print(f"Outflow Days (Z<-1) Switches: {res.loc[outflow_mask, 'switch_boosted'].sum()} / {outflow_mask.sum()}")
    
    # Show diff examples
    diffs = res[res['switch_standard'] != res['switch_boosted']]
    if not diffs.empty:
        print("\n[Switching Logic Deltas (Standard vs Boosted)]")
        print(diffs[['date', 'z_score', 'flow_boost', 'switch_standard', 'switch_boosted']].head())
    else:
        print("\n[No logic difference observed on this sample]")

if __name__ == "__main__":
    main()
