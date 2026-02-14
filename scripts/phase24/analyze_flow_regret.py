# scripts/phase24/analyze_flow_regret.py
import pandas as pd
import argparse
from pathlib import Path
import matplotlib.pyplot as plt

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--regret_csv", required=True, help="Simulation Regret CSV (ts, regret_h, etc)")
    ap.add_argument("--flow_metrics_csv", required=True, help="Flow Z-Score CSV (date, z_score)")
    ap.add_argument("--out_dir", required=True, help="Output directory for reports/charts")
    args = ap.parse_args()

    regret_path = Path(args.regret_csv)
    flow_path = Path(args.flow_metrics_csv)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Load Data
    if not regret_path.exists():
        print(f"[ERR] Regret file not found: {regret_path}")
        return
    if not flow_path.exists():
        print(f"[ERR] Flow file not found: {flow_path}")
        return

    df_regret = pd.read_csv(regret_path)
    df_flow = pd.read_csv(flow_path)

    # 2. Preprocess & Merge
    # Ensure date formats match for merging
    # Regret usually has 'ts' (datetime). We need 'date' (YYYY-MM-DD)
    if 'ts' in df_regret.columns:
        df_regret['ts'] = pd.to_datetime(df_regret['ts'])
        df_regret['date'] = df_regret['ts'].dt.strftime('%Y-%m-%d')
    elif 'date' in df_regret.columns:
         df_regret['date'] = pd.to_datetime(df_regret['date']).dt.strftime('%Y-%m-%d')
    
    # Flow has 'date' (YYYY-MM-DD or similar) -> Normalize
    df_flow['date'] = pd.to_datetime(df_flow['date']).dt.strftime('%Y-%m-%d')

    # Merge
    # We want to analyze Regret GIVEN Flow Regime, so inner join or left join on regret
    df_merged = pd.merge(df_regret, df_flow[['date', 'z_score']], on='date', how='inner')
    
    if df_merged.empty:
        print("[WARN] Merged DataFrame is empty. Check date formats.")
        return

    # 3. Define Regimes
    # INFLOW: Z > 1.0
    # OUTFLOW: Z < -1.0
    # NEUTRAL: -1.0 <= Z <= 1.0
    conditions = [
        (df_merged['z_score'] > 1.0),
        (df_merged['z_score'] < -1.0)
    ]
    choices = ['INFLOW', 'OUTFLOW']
    df_merged['regime'] = 'NEUTRAL' # Default
    # Use numpy select or loc
    df_merged.loc[df_merged['z_score'] > 1.0, 'regime'] = 'INFLOW'
    df_merged.loc[df_merged['z_score'] < -1.0, 'regime'] = 'OUTFLOW'
    
    # 4. Analyze Regret by Regime
    # Assuming 'regret' column exists. If strictly oracle-policy, might need calculation.
    # We'll assume 'regret' is already calculated in the input csv.
    target_col = 'regret' 
    if 'regret' not in df_merged.columns:
        # Fallback: look for common metric columns
        candidates = [c for c in df_merged.columns if 'regret' in c.lower()]
        if candidates:
            target_col = candidates[0]
            print(f"[INFO] Using '{target_col}' as regret metric.")
        else:
             print("[ERR] No 'regret' column found.")
             print(df_merged.columns)
             return

    stats = df_merged.groupby('regime')[target_col].describe()
    print("\n--- Regret Statistics by Flow Regime ---")
    print(stats)
    
    stats_csv = out_dir / "regret_by_flow_regime.csv"
    stats.to_csv(stats_csv)
    print(f"[saved] {stats_csv}")

    # 5. Plot
    try:
        fig, ax = plt.subplots(figsize=(8, 6))
        df_merged.boxplot(column=target_col, by='regime', ax=ax)
        plt.title(f'Regret Distribution by Flow Regime')
        plt.suptitle('') # Get rid of default pandas subtitle
        plt.ylabel(target_col)
        
        plot_path = out_dir / "regret_boxplot.png"
        plt.savefig(plot_path)
        print(f"[saved] {plot_path}")
    except Exception as e:
        print(f"[WARN] Plotting failed: {e}")

if __name__ == "__main__":
    main()
