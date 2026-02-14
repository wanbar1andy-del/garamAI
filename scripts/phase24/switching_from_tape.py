# scripts/phase24/switching_from_tape.py
import pandas as pd
import numpy as np
import argparse
from pathlib import Path

def simulate_switching_from_tape(tape_csv: Path, metric_csv: Path, out_dir: Path, symbol: str, boost_weight=10.0, gap=2.0, top_n=3):
    """
    Simulate switching using Decision Tape (Candidate Pool) + Flow Metric.
    
    Outputs:
    - summary.csv: Overall stats
    - regime_breakdown.csv: Stats by Inflow/Outflow/Neutral
    - switch_events.csv: Daily log
    """
    
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Load Metrics
    if not metric_csv.exists():
        print(f"[ERR] Metric CSV not found: {metric_csv}")
        return

    df_flow = pd.read_csv(metric_csv)
    # Ensure date/z_score
    if 'date' in df_flow.columns:
        df_flow['date'] = pd.to_datetime(df_flow['date'])
    elif '일자' in df_flow.columns:
        df_flow['date'] = pd.to_datetime(df_flow['일자'], format='%Y%m%d')
        
    df_flow = df_flow.sort_values('date').fillna(0)
    
    # Map Date -> Z-Score
    flow_map = dict(zip(df_flow['date'].dt.strftime('%Y-%m-%d'), df_flow['z_score']))
    
    # 2. Load Tape (Optional, or Mock if missing)
    if not tape_csv.exists():
        print(f"[WARN] Tape {tape_csv} not found. Using Dummy Tape for verification.")
        # Dummy: Date range from flow
        dates = df_flow['date']
        records = []
        np.random.seed(42) # Fixed seed for baseline vs booster comparison
        for d in dates:
            # 005930 Score: Random 50~70
            s_hero = np.random.uniform(50, 70)
            # Market Best (Challenger): Random 50~75. Often better than hero.
            s_market = np.random.uniform(50, 75)
            records.append({'date': d, 'score_hero': s_hero, 'score_market': s_market})
        df = pd.DataFrame(records)
    else:
        # If Real Tape exists, load and extract (Hero Score vs Top 1 Competitor Score)
        # Placeholder for real tape logic
        # For Phase 24 analysis, we often just want correct date alignment and scores.
        # Assuming the CSV has columns: date, score_hero, score_market for simplicity
        # Or parse standard decision tape format.
        try:
            df = pd.read_csv(tape_csv)
            df['date'] = pd.to_datetime(df['date'])
        except:
             print("[ERR] Failed to read Tape CSV")
             return

    # 3. Apply Logic
    results = []
    
    for _, row in df.iterrows():
        d_str = row['date'].strftime('%Y-%m-%d')
        z = flow_map.get(d_str, 0.0)
        
        # Determine Regime
        regime = 'NEUTRAL'
        if z > 1.0: regime = 'INFLOW'
        elif z < -1.0: regime = 'OUTFLOW'
        
        # Boost: clip(z, -2, 2) * weight
        boost = np.clip(z, -2, 2) * boost_weight
        
        # Switching Logic
        # We HOLD Hero. Switch if Market Top > Hero + Gap
        
        # Standard (Weight=0 equivalent if boost=0)
        s_hero_std = row['score_hero']
        diff_std = row['score_market'] - s_hero_std
        switch_std = diff_std > gap
        
        # Boosted
        s_hero_boost = row['score_hero'] + boost
        diff_boost = row['score_market'] - s_hero_boost
        switch_boost = diff_boost > gap
        
        results.append({
            'date': d_str,
            'regime': regime,
            'z_score': z,
            'score_hero': s_hero_std,
            'score_market': row['score_market'],
            'boost': boost,
            'diff_std': diff_std,
            'diff_boost': diff_boost,
            'switch_std': int(switch_std),
            'switch_boost': int(switch_boost)
        })
        
    res_df = pd.DataFrame(results)
    res_df.to_csv(out_dir / "switch_events.csv", index=False)
    
    # 4. Aggregation
    
    # Overall Summary
    total_days = len(res_df)
    sw_std_sum = res_df['switch_std'].sum()
    sw_bst_sum = res_df['switch_boost'].sum()
    
    summary = pd.DataFrame([{
        'weight': boost_weight,
        'gap': gap,
        'total_days': total_days,
        'switches_std': sw_std_sum,
        'switches_boost': sw_bst_sum,
        'rate_std': sw_std_sum / total_days if total_days else 0,
        'rate_boost': sw_bst_sum / total_days if total_days else 0,
        'delta_switches': sw_bst_sum - sw_std_sum
    }])
    summary.to_csv(out_dir / "summary.csv", index=False)

    # Regime Breakdown
    regime_stats = res_df.groupby('regime')[['switch_std', 'switch_boost']].sum()
    regime_counts = res_df['regime'].value_counts()
    regime_stats['count'] = regime_counts
    regime_stats['rate_std'] = regime_stats['switch_std'] / regime_stats['count']
    regime_stats['rate_boost'] = regime_stats['switch_boost'] / regime_stats['count']
    regime_stats['delta'] = regime_stats['switch_boost'] - regime_stats['switch_std']
    
    regime_stats.to_csv(out_dir / "regime_breakdown.csv")
    
    print(f"\n[Simulation Complete] Weight={boost_weight}")
    print(summary.to_string(index=False))
    print("\n[Regime Breakdown]")
    print(regime_stats[['count', 'switch_std', 'switch_boost', 'delta']])

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tape_csv", required=True, help="Path to Decision Tape (or dummy path)")
    ap.add_argument("--flow_metrics_csv", required=True, help="Path to Flow Z-Score CSV")
    ap.add_argument("--out_dir", required=True, help="Output directory") 
    ap.add_argument("--symbol", default="005930")
    ap.add_argument("--weight", type=float, default=0.0)
    ap.add_argument("--gap", type=float, default=2.0)
    
    args = ap.parse_args()
    
    simulate_switching_from_tape(
        Path(args.tape_csv),
        Path(args.flow_metrics_csv),
        Path(args.out_dir),
        args.symbol,
        boost_weight=args.weight,
        gap=args.gap,
        top_n=3
    )

if __name__ == "__main__":
    main()
