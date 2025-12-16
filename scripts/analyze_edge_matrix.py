import json
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from pathlib import Path

def load_report(path="garam_core/reports/latest.json"):
    p = Path(path)
    if not p.exists():
        # Fallback for running from scripts dir
        p = Path("../garam_core/reports/latest.json")
    
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)

def plot_expectancy_by_regime(report):
    by_regime = report["edge_analysis"]["by_regime"]
    data_list = []
    
    for name, data in by_regime.items():
        if data["trades"] > 0:
            data_list.append({
                "regime": name,
                "expectancy_net": data["expectancy_net"],
                "trades": data["trades"],
                "win_rate": data["win_rate"]
            })
    
    if not data_list:
        print("No trades in any regime to plot.")
        return

    df = pd.DataFrame(data_list)
    
    plt.figure(figsize=(10,6))
    sns.barplot(x="regime", y="expectancy_net", data=df, palette="RdBu")
    plt.axhline(0, color='black', linewidth=1)
    
    # Add labels
    for i, row in df.iterrows():
        plt.text(i, row.expectancy_net, f"n={row.trades}", 
                 ha='center', va='bottom' if row.expectancy_net > 0 else 'top')

    plt.title(f"Net Expectancy by Regime (Overall: {report['edge_analysis']['overall']['expectancy_net']:.4f})")
    plt.ylabel("Expectancy (net)")
    plt.xlabel("Regime")
    plt.tight_layout()
    plt.show()

def plot_cost_vs_expectancy(report):
    over = report["edge_analysis"]["overall"]
    # Single point plot isn't very useful unless comparing multiple runs/strategies.
    # But for a single report, we can compare Gross vs Net vs Cost
    
    metrics = {
        "Gross Exp": over["expectancy_gross"],
        "Net Exp": over["expectancy_net"],
        "Avg Cost": over["cost_per_trade_avg"]
    }
    
    plt.figure(figsize=(8,5))
    bars = plt.bar(metrics.keys(), metrics.values(), color=['blue', 'red', 'orange'])
    plt.axhline(0, color='black', linewidth=0.8)
    plt.title("Expectancy Components (Avg per Trade)")
    
    for bar in bars:
        h = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, h, f"{h:.5f}", ha='center', va='bottom' if h>0 else 'top')
        
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    try:
        rpt = load_report()
        print(f"Loaded Report: {rpt['meta']['run_id']}")
        
        # Tags
        tags = rpt['edge_analysis']['collapse_tags']
        if tags:
            print(f"Collapse Tags: {tags}")
            
        plot_expectancy_by_regime(rpt)
        plot_cost_vs_expectancy(rpt)
    except Exception as e:
        print(f"Error: {e}")
