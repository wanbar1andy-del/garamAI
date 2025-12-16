import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import os

def main():
    if not Path("edge_map_overall_400.csv").exists():
        print("CSV not found: edge_map_overall_400.csv")
        return

    # 데이터 로드
    df = pd.read_csv("edge_map_overall_400.csv")

    # 1) 기본 통계
    summary = df.describe()

    # 저장 폴더 준비
    out_dir = Path("reports/overall_summary")
    out_dir.mkdir(parents=True, exist_ok=True)

    # 2) Net Expectancy Distribution 그래프
    plt.figure(figsize=(8,4))
    sns.histplot(df["net_expectancy"], bins=50, kde=True)
    plt.title("Net Expectancy Distribution (400 symbols)")
    plt.xlabel("Net Expectancy")
    plt.ylabel("Frequency")
    plt.savefig(out_dir/"net_expectancy_dist.png", dpi=150)
    plt.close()

    # 3) Win Rate Distribution
    plt.figure(figsize=(8,4))
    sns.histplot(df["win_rate"], bins=40, kde=True)
    plt.title("Win Rate Distribution")
    plt.xlabel("Win Rate")
    plt.ylabel("Frequency")
    plt.savefig(out_dir/"win_rate_dist.png", dpi=150)
    plt.close()

    # 4) Trades Per Day
    plt.figure(figsize=(8,4))
    sns.histplot(df["trades_per_day"], bins=40)
    plt.title("Trades Per Day (400 symbols)")
    plt.xlabel("Trades Per Day")
    plt.ylabel("Frequency")
    plt.savefig(out_dir/"trades_per_day_dist.png", dpi=150)
    plt.close()

    # CSV 저장
    summary.to_csv(out_dir/"overall_summary_stats.csv", index=True)

    print("Overall summary report generated at:", out_dir)

if __name__ == "__main__":
    main()
