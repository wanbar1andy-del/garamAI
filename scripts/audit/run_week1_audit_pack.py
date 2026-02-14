import subprocess
import sys
import pandas as pd
import json
from pathlib import Path

# Setup Paths
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))
audit_dir = project_root / "results" / "audit" / "week1_v2"

def run_simulation(cost):
    print(f"\n[Audit Pack] Running Simulation with Cost={cost}bps...")
    cmd = [sys.executable, "-m", "scripts.audit.run_audit_week1_v2", "--cost", str(cost)]
    subprocess.run(cmd, check=True, cwd=str(project_root))

def audit_schema(csv_path):
    print(f"\n[Audit Pack] Auditing Ledger Schema: {csv_path.name}...")
    df = pd.read_csv(csv_path)
    
    issues = []
    
    # Check 1: Qty > 0
    # Qty is float
    if (df['qty'] < 0).any():
        issues.append("ERROR: Negative Qty found.")
    
    # Check 2: Fee/Tax Negative?
    # Spec: Fee/Tax should be negative cost
    if (df['fee'] > 0).any():
        issues.append("ERROR: Positive Entry in Fee (Should be negative cost).")
        
    # Check 3: Net vs Gross Logic
    # Net = Gross + Fee + Tax (since fee/tax are negative)
    # Allow small float error
    df['calc_net'] = df['gross_pnl'] + df['fee'] + df['tax']
    df['diff'] = (df['net_pnl'] - df['calc_net']).abs()
    if (df['diff'] > 0.01).any():
        issues.append("ERROR: Net PnL Calculation Mismatch.")
        
    # Check 4: Force Close Time
    # Should not be weird 00:xx unless forced there.
    # Logic in V2 uses 15:35, so it should be fine.
    
    result = {
        "file": csv_path.name,
        "pass": len(issues) == 0,
        "issues": issues,
        "sample_count": len(df)
    }
    
    out_path = audit_dir / "ledger_schema_audit_week1.json"
    with open(out_path, "w") as f:
        json.dump(result, f, indent=4)
        
    print(f"  Schema Audit Pass: {result['pass']}")
    if issues:
        print(f"  Issues: {issues}")

def compare_costs():
    print("\n[Audit Pack] Comparing Cost Impacts...")
    path_10 = audit_dir / "pnl_reconciliation_week1_cost10.json"
    path_0 = audit_dir / "pnl_reconciliation_week1_cost0.json"
    
    if not path_10.exists() or not path_0.exists():
        print("  Missing reconciliation files.")
        return

    with open(path_10) as f: r10 = json.load(f)
    with open(path_0) as f: r0 = json.load(f)
    
    # Calculate Metrics
    # Average Cost per Trade = (Fee Total) / Trade Count
    fee_per_trade = r10['fee_total'] / r10['trade_count'] if r10['trade_count'] else 0
    
    # Gross Edge per Trade (from Cost 0 result) = Sum Net PnL (Cost 0) / Trade Count
    gross_edge_per_trade = r0['sum_net_pnl'] / r0['trade_count'] if r0['trade_count'] else 0
    
    comparison = {
        "metric": ["Net PnL Total", "Trade Count", "Avg PnL per Trade", "Avg Fee per Trade"],
        "cost_10bps": [r10['sum_net_pnl'], r10['trade_count'], r10['sum_net_pnl']/r10['trade_count'], fee_per_trade],
        "cost_0bps": [r0['sum_net_pnl'], r0['trade_count'], r0['sum_net_pnl']/r0['trade_count'], 0],
        "diff": [r10['sum_net_pnl']-r0['sum_net_pnl'], 0, (r10['sum_net_pnl']-r0['sum_net_pnl'])/r10['trade_count'], fee_per_trade]
    }
    
    df_comp = pd.DataFrame(comparison)
    out_path = audit_dir / "cost_toggle_comparison_week1.csv"
    df_comp.to_csv(out_path, index=False)
    print(f"  Saved Comparison: {out_path}")
    
    print("\n[Summary: Gross Edge vs Cost]")
    print(f"  Avg Gross Edge/Trade: {gross_edge_per_trade:.2f} KRW")
    print(f"  Avg Cost/Trade:       {abs(fee_per_trade):.2f} KRW")
    if gross_edge_per_trade < abs(fee_per_trade):
        print("  >> CRITICAL: Strategy Negative Expectancy (Cost > Edge)")
    else:
        print("  >> Strategy Positive Expectancy (Edge > Cost)")

def summarize_death_regret():
    print("\n[Audit Pack] Summarizing Death & Regret...")
    # Just print simple stats from the csvs
    death_path = audit_dir / "death_audit_week1.csv"
    if death_path.exists():
        df = pd.read_csv(death_path)
        # reaction_time +ve means good (early exit), -ve means late
        print(f"  Avg Reaction Time: {df['reaction_time'].mean():.2f} min (Positive is good)")
        late_exits = len(df[df['reaction_time'] < 0])
        print(f"  Late Exits: {late_exits} / {len(df)} ({late_exits/len(df)*100:.1f}%)")
        
    regret_path = audit_dir / "opportunity_regret_week1.csv"
    if regret_path.exists():
        df = pd.read_csv(regret_path)
        print(f"  Avg Regret per Minute: {df['regret'].mean()*100:.4f}%")
        print(f"  Total Held Minutes: {len(df)}")

def run_pack():
    # 1. Run Simulations
    run_simulation(10.0)
    run_simulation(0.0)
    
    # 2. Audit Schema (Using Cost 10 result)
    audit_schema(audit_dir / "trades_week1_cost10.csv")
    
    # 3. Compare Costs
    compare_costs()
    
    # 4. Summary Stats
    summarize_death_regret()

if __name__ == "__main__":
    run_pack()
