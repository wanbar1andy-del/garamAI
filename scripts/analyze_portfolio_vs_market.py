import pandas as pd
import matplotlib.pyplot as plt
import FinanceDataReader as fdr
from pathlib import Path
import os
import glob

def main():
    # 1. Setup
    reports_dir = Path("garam_core/reports")
    results_dir = Path("results")
    results_dir.mkdir(exist_ok=True)
    
    print(f"Scanning {reports_dir} for equity curves...")
    
    # 2. Load Equity Curves
    equity_files = list(reports_dir.glob("verify_turbo_v3_*/equity_*.csv"))
    print(f"Found {len(equity_files)} equity files.")
    
    if not equity_files:
        print("No equity files found.")
        return

    dfs = []
    valid_count = 0
    
    for f in equity_files:
        try:
            # Read CSV, handle mocked dates
            df = pd.read_csv(f, names=["timestamp", "equity"], header=0)
            df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
            
            # Filter out 1970 dates (Mock)
            if df["timestamp"].min().year < 2024:
                continue
                
            # Set index and resample to 1min to align
            df.set_index("timestamp", inplace=True)
            df = df.resample("1T").last().ffill()
            
            # Calculate return series (normalized to 0 start) - simple return log
            # Actually, to aggregate properly, we should sum Equities if we assume equal allocation?
            # Or average the returns. 
            # Let's sum Equity assuming 100M start for each.
            
            # Symbol name from filename
            sym = f.name.replace("equity_", "").replace(".csv", "")
            df.rename(columns={"equity": sym}, inplace=True)
            
            dfs.append(df)
            valid_count += 1
            
        except Exception as e:
            print(f"Error loading {f}: {e}")
            
    print(f"Loaded {valid_count} valid equity curves (filtered out mocks).")
    
    if not dfs:
        print("No valid data after filtering.")
        return

    # 3. Aggregate Portfolio
    # Concatenate all (outer join to keep full range)
    portfolio = pd.concat(dfs, axis=1)
    
    # Forward fill missing data (hold position)
    portfolio.ffill(inplace=True)
    portfolio.fillna(100_000_000, inplace=True) # Fill NaNs with initial capital
    
    # Sum Total Equity
    portfolio["Total_Equity"] = portfolio.sum(axis=1)
    
    # Calculate Cumulative Return (%)
    initial_equity = portfolio["Total_Equity"].iloc[0]
    portfolio["Portfolio_Return"] = (portfolio["Total_Equity"] / initial_equity - 1) * 100
    
    # 4. Fetch KOSPI Benchmark
    start_date = portfolio.index.min()
    end_date = portfolio.index.max()
    
    print(f"Data Range: {start_date} ~ {end_date}")
    
    try:
        # Fetch KS11 (KOSPI)
        kospi = fdr.DataReader("KS11", start_date, end_date)
        # Normalize to % return
        kospi_start = kospi['Close'].iloc[0]
        kospi["KOSPI_Return"] = (kospi['Close'] / kospi_start - 1) * 100
        
        # Merge for plotting (Match timezone if needed)
        # KOSPI is usually daily, Portfolio is minute.
        # We can plot them on same axis.
        index_data = kospi[["KOSPI_Return"]]
    except Exception as e:
        print(f"Failed to fetch KOSPI: {e}")
        index_data = None

    # 5. Visualization
    plt.figure(figsize=(14, 7))
    
    # Plot Portfolio (Minute resolution)
    plt.plot(portfolio.index, portfolio["Portfolio_Return"], label=f"GARAM Portfolio ({valid_count} Symbols)", color="#007bff", linewidth=1.5)
    
    # Plot KOSPI (Daily resolution, overlay)
    if index_data is not None:
        # Reindex index_data to match portfolio time range for better plotting?
        # Just creating a new axis or plotting directly since x-axis is datetime.
        plt.plot(index_data.index, index_data["KOSPI_Return"], label="KOSPI Index", color="#dc3545", linewidth=2, linestyle="--", alpha=0.8)
    
    plt.title("GARAM 400 Consolidated Performance vs KOSPI", fontsize=16)
    plt.xlabel("Date")
    plt.ylabel("Cumulative Return (%)")
    plt.legend(fontsize=12)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    save_path = results_dir / "portfolio_vs_market.png"
    plt.savefig(save_path)
    print(f"Graph Saved: {save_path}")
    
    # Save CSV Data for Analysis
    stats_csv = results_dir / "portfolio_stats.csv"
    portfolio["KOSPI_Return"] = float("nan") # Placeholder
    # Try to merge properly for CSV
    # ... (Simplified for speed)
    # Just save the portfolio curve
    portfolio[["Total_Equity", "Portfolio_Return"]].to_csv(stats_csv)
    print(f"Data Saved: {stats_csv}")

    # 6. Print Key Stats
    final_ret = portfolio["Portfolio_Return"].iloc[-1]
    print("="*40)
    print(f"Final Portfolio Return: {final_ret:.2f}%")
    print("="*40)

if __name__ == "__main__":
    main()
