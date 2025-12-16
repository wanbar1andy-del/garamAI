import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

def main():
    if not Path("edge_map_by_regime_400.csv").exists():
        print("CSV not found: edge_map_by_regime_400.csv")
        return
    if not Path("edge_map_overall_400.csv").exists():
        print("CSV not found: edge_map_overall_400.csv")
        return

    df_reg = pd.read_csv("edge_map_by_regime_400.csv")
    df_overall = pd.read_csv("edge_map_overall_400.csv")

    out_dir = Path("reports/regime_guard_reco")
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1) Regime Net Expectancy Dispersion
    plt.figure(figsize=(12,6))
    sns.boxplot(x="regime", y="net_expectancy", data=df_reg)
    plt.title("Regime-wise Net Expectancy (400 symbols)")
    plt.xlabel("Regime")
    plt.ylabel("Net Expectancy")
    plt.xticks(rotation=45)
    plt.savefig(out_dir/"regime_net_expectancy_box.png", dpi=150)
    plt.close()

    # 2) Regime Trade Count
    plt.figure(figsize=(12,6))
    sns.barplot(x="regime", y="trades", data=df_reg, errorbar=None)
    plt.title("Total Trade Count by Regime")
    plt.xlabel("Regime")
    plt.ylabel("Trades")
    plt.xticks(rotation=45)
    plt.savefig(out_dir/"regime_trade_count.png", dpi=150)
    plt.close()

    # 3) Guard Parameter Recommendation
    # (Reuse earlier reco logic/stats)
    df_over = df_overall.copy()

    guard_min_th = float(df_over["net_expectancy"].quantile(0.10))
    crash_mdd_th = float(df_over.get("mdd", pd.Series(dtype=float)).quantile(0.05))
    tpd_th = float(df_over["trades_per_day"].quantile(0.90))
    win_rate_th = float(df_over["win_rate"].quantile(0.10))

    # Regime spread
    spread = df_reg.groupby("symbol")["net_expectancy"].agg(lambda s: s.std() if len(s)>1 else 0)
    regime_spread_th = float(spread.quantile(0.75))

    params = {
        "guard_min_threshold": guard_min_th,
        "crash_mdd": crash_mdd_th,
        "overtrade_trades_per_day": tpd_th,
        "signal_noise_win_rate": win_rate_th,
        "regime_spread_exp_net": regime_spread_th
    }

    param_df = pd.DataFrame.from_dict(params, orient="index", columns=["recommended"])
    param_df.to_csv(out_dir/"regime_guard_recommendation.csv")
    print(f"Stats saved to {out_dir/'regime_guard_recommendation.csv'}")

    # 4) Regime Spread Distribution
    plt.figure(figsize=(8,4))
    sns.histplot(spread, bins=40, kde=True)
    plt.title("Regime Net Expectancy Spread Distribution")
    plt.xlabel("Standard Deviation of Regime Net Expectancy")
    plt.ylabel("Counts")
    plt.savefig(out_dir/"regime_spread_dist.png", dpi=150)
    plt.close()

    print("Regime guard recommendation report generated at:", out_dir)

if __name__ == "__main__":
    main()
