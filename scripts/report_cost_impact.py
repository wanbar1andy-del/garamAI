import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

def main():
    if not Path("edge_map_overall_400.csv").exists():
        print("CSV not found: edge_map_overall_400.csv")
        return

    df = pd.read_csv("edge_map_overall_400.csv")
    out_dir = Path("reports/cost_impact_detail")
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1) Cost vs Net Expectancy Scatter
    plt.figure(figsize=(8,6))
    sns.scatterplot(x="cost_avg", y="net_expectancy", data=df, alpha=0.6)
    plt.title("Cost per Trade vs Net Expectancy (400 symbols)")
    plt.xlabel("Average Cost per Trade")
    plt.ylabel("Net Expectancy")
    plt.savefig(out_dir/"cost_vs_net_expectancy.png", dpi=150)
    plt.close()

    # 2) Cost vs Win Rate
    plt.figure(figsize=(8,6))
    sns.scatterplot(x="cost_avg", y="win_rate", data=df, alpha=0.6)
    plt.title("Average Cost vs Win Rate (400 symbols)")
    plt.xlabel("Average Cost")
    plt.ylabel("Win Rate")
    plt.savefig(out_dir/"cost_vs_win_rate.png", dpi=150)
    plt.close()

    # 3) Cost Categorized Distributions
    # Check if cost_avg has variance
    if df["cost_avg"].nunique() > 1:
        try:
            df["cost_bucket"] = pd.qcut(df["cost_avg"], 5, duplicates='drop')
        except ValueError:
            # Fallback if too few unique values
            df["cost_bucket"] = df["cost_avg"]
            
        plt.figure(figsize=(10,5))
        sns.boxplot(x="cost_bucket", y="net_expectancy", data=df)
        plt.title("Net Expectancy by Cost Bucket")
        plt.xlabel("Cost Bucket (Quintiles)")
        plt.xticks(rotation=45)
        plt.savefig(out_dir/"cost_bucket_net_expectancy.png", dpi=150)
        plt.close()

    # Summary CSV
    df[["symbol","cost_avg","net_expectancy","win_rate"]].to_csv(out_dir/"cost_impact_summary.csv", index=False)

    print("Cost impact report generated at:", out_dir)

if __name__ == "__main__":
    main()
