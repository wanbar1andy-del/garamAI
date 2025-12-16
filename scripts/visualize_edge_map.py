import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from pathlib import Path
import os

def main():
    if not Path("edge_map_overall_400.csv").exists():
        print("CSV not found: edge_map_overall_400.csv")
        return

    df = pd.read_csv("edge_map_overall_400.csv")
    
    # Create results dir for saving plots
    os.makedirs("results", exist_ok=True)

    # 1) 전략 기대값 분포
    plt.figure(figsize=(10,6))
    sns.histplot(df["net_expectancy"], bins=50, kde=True)
    plt.title("400 Symbols Net Expectancy Distribution")
    plt.xlabel("Net Expectancy")
    plt.ylabel("Frequency")
    plt.tight_layout()
    plt.savefig("results/edge_map_expectancy_dist.png")
    print("Saved results/edge_map_expectancy_dist.png")
    # plt.show() # Commented out for headless

    # 2) 비용 대비 엣지
    plt.figure(figsize=(8,5))
    sns.scatterplot(x="cost_avg", y="net_expectancy", data=df)
    plt.title("Cost vs Net Expectancy (400 Symbols)")
    plt.xlabel("Avg Cost")
    plt.ylabel("Net Expectancy")
    plt.tight_layout()
    plt.savefig("results/edge_map_cost_vs_net.png")
    print("Saved results/edge_map_cost_vs_net.png")
    # plt.show()

    # 3) 레짐별 기대값
    if Path("edge_map_by_regime_400.csv").exists():
        dfr = pd.read_csv("edge_map_by_regime_400.csv")
        plt.figure(figsize=(12,6))
        sns.boxplot(x="regime", y="net_expectancy", data=dfr)
        plt.title("Net Expectancy by Regime (400 Symbols)")
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig("results/edge_map_regime_boxplot.png")
        print("Saved results/edge_map_regime_boxplot.png")
        # plt.show()

if __name__ == "__main__":
    main()
