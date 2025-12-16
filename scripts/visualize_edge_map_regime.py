import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from pathlib import Path
import os

def main():
    if not Path("edge_map_by_regime_400.csv").exists():
        print("CSV not found: edge_map_by_regime_400.csv. Please run edge_map_400.py first (after batch run).")
        return

    # 1) Load data
    df = pd.read_csv("edge_map_by_regime_400.csv")

    # 2) Ensure regime categorical order
    regime_order = [
        "TREND_UP", "TREND_DOWN",
        "CHOP_HIGHVOL", "CHOP_LOWVOL", "PANIC", "UNCERTAIN"
    ]
    # Filter only existing regimes to avoid error if some are missing, but keeping order logic
    existing_regimes = [r for r in regime_order if r in df["regime"].unique()]
    # Add any others found
    others = [r for r in df["regime"].unique() if r not in regime_order]
    final_order = existing_regimes + others
    
    df["regime"] = pd.Categorical(df["regime"], categories=final_order, ordered=True)
    
    # Save directory
    os.makedirs("results/viz_regime", exist_ok=True)

    # 3) Basic distribution by regime
    plt.figure(figsize=(12,6))
    sns.boxplot(x="regime", y="net_expectancy", data=df)
    sns.stripplot(
        x="regime", y="net_expectancy",
        data=df, color="black", alpha=0.3, jitter=0.2
    )
    plt.title("Net Expectancy by Regime (400 Symbols)")
    plt.ylabel("Net Expectancy")
    plt.xlabel("Regime")
    plt.axhline(0, color="red", linestyle="--")
    plt.tight_layout()
    plt.savefig("results/viz_regime/net_expectancy_dist.png")
    # plt.show()
    print("Saved results/viz_regime/net_expectancy_dist.png")

    # 4) Trade count by regime
    plt.figure(figsize=(12,6))
    sns.barplot(x="regime", y="trades", data=df, errorbar=None) # ci=None deprecated in new seaborn
    plt.title("Trade Count per Regime (Sum/Avg)")
    plt.ylabel("Trades")
    plt.xlabel("Regime")
    plt.tight_layout()
    plt.savefig("results/viz_regime/trade_count.png")
    # plt.show()
    print("Saved results/viz_regime/trade_count.png")

    # 5) Regime vs Win Rate
    plt.figure(figsize=(12,6))
    sns.barplot(x="regime", y="win_rate", data=df, errorbar=None)
    plt.title("Win Rate by Regime")
    plt.ylabel("Win Rate")
    plt.xlabel("Regime")
    plt.tight_layout()
    plt.savefig("results/viz_regime/win_rate.png")
    # plt.show()
    print("Saved results/viz_regime/win_rate.png")

    # 6) Cost vs Net Expectancy per regime
    plt.figure(figsize=(12,6))
    sns.scatterplot(
        x="cost_avg", y="net_expectancy",
        hue="regime", data=df, palette="tab10", alpha=0.6
    )
    plt.title("Cost vs Net Expectancy by Regime")
    plt.xlabel("Cost per Trade (avg)")
    plt.ylabel("Net Expectancy")
    plt.tight_layout()
    plt.savefig("results/viz_regime/cost_vs_net_by_regime.png")
    # plt.show()
    print("Saved results/viz_regime/cost_vs_net_by_regime.png")

if __name__ == "__main__":
    main()
