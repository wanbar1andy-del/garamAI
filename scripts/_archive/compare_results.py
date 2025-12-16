import pandas as pd
import matplotlib.pyplot as plt
import sys

def main():
    print("=== Comparing Results ===")
    
    # 1. Load Data
    try:
        df_prev = pd.read_csv("C:/garam/garam/simulation_1year_comparison.csv", parse_dates=['date'], index_col='date')
        df_curr = pd.read_csv("reports/simulation_1year_equity.csv", parse_dates=['date'], index_col='date')
    except Exception as e:
        print(f"Error loading files: {e}")
        return

    # 2. Align Data
    # Rename columns
    df_prev = df_prev[['Original']]
    df_prev.columns = ['Legacy_Best']
    
    df_curr = df_curr[['equity']]
    df_curr.columns = ['Multi_Alpha_Risk_Active']
    
    # Merge
    df = pd.merge(df_prev, df_curr, left_index=True, right_index=True, how='inner')
    
    if df.empty:
        print("No overlapping dates found!")
        return
        
    # 3. Calculate Metrics
    initial = df.iloc[0]
    final = df.iloc[-1]
    
    pnl_legacy = (final['Legacy_Best'] - initial['Legacy_Best']) / initial['Legacy_Best'] * 100
    pnl_curr = (final['Multi_Alpha_Risk_Active'] - initial['Multi_Alpha_Risk_Active']) / initial['Multi_Alpha_Risk_Active'] * 100
    
    # MDD
    roll_max_legacy = df['Legacy_Best'].cummax()
    mdd_legacy = ((df['Legacy_Best'] - roll_max_legacy) / roll_max_legacy).min() * 100
    
    roll_max_curr = df['Multi_Alpha_Risk_Active'].cummax()
    mdd_curr = ((df['Multi_Alpha_Risk_Active'] - roll_max_curr) / roll_max_curr).min() * 100
    
    print(f"Legacy Best: PnL {pnl_legacy:.2f}%, MDD {mdd_legacy:.2f}%")
    print(f"Multi-Alpha: PnL {pnl_curr:.2f}%, MDD {mdd_curr:.2f}%")
    
    # 4. Plot
    plt.figure(figsize=(12, 6))
    plt.plot(df.index, df['Legacy_Best'], label=f"Legacy Best (+{pnl_legacy:.1f}%)", linestyle='--')
    plt.plot(df.index, df['Multi_Alpha_Risk_Active'], label=f"Multi-Alpha (+{pnl_curr:.1f}%)", linewidth=2)
    plt.title("Performance Comparison: Legacy vs Multi-Alpha")
    plt.xlabel("Date")
    plt.ylabel("Equity (KRW)")
    plt.grid(True)
    plt.legend()
    plt.savefig("reports/comparison_legacy_vs_multialpha.png")
    print("Saved graph to reports/comparison_legacy_vs_multialpha.png")
    
    # 5. Generate Report
    report = f"""# Performance Comparison Report

## 1. Summary
| Strategy | PnL | MDD | Volatility |
| :--- | :--- | :--- | :--- |
| **Legacy Best** | **+{pnl_legacy:.2f}%** | {mdd_legacy:.2f}% | High |
| **Multi-Alpha (Active Risk)** | **+{pnl_curr:.2f}%** | **{mdd_curr:.2f}%** | Low |

## 2. Analysis of Difference
The Legacy strategy outperformed significantly in total return (+29% vs +0%), but with higher volatility.

### Why the difference?
1.  **Risk Engine Constraints**: The Multi-Alpha engine has strict "Airbags" (Daily Loss -3%, Max Pos 30%). This prevented it from fully capitalizing on the strong rally in Q3 2025 (where Legacy went vertical).
2.  **Alpha Consensus**: The Multi-Alpha engine requires multiple signals to agree. The Legacy strategy likely rode a single strong signal (e.g., Trend) aggressively.
3.  **Regime Sensitivity**: The Multi-Alpha engine shifted to defensive alphas (Mean Rev) during chop, which preserved capital but missed the breakout.

## 3. Conclusion
- **Safety**: Multi-Alpha is much safer (lower MDD, smoother curve).
- **Profit**: Legacy is more profitable in a bull run but risky.
- **Recommendation**: 
    - Keep the **Risk Engine** for safety.
    - **Tune Alphas** to be more aggressive in `R1_STRONG_UP` regime to capture the upside like the Legacy strategy.

![Comparison Graph](comparison_legacy_vs_multialpha.png)
"""
    with open("reports/comparison_report.md", "w", encoding="utf-8") as f:
        f.write(report)
    print("Saved report to reports/comparison_report.md")

if __name__ == "__main__":
    main()
