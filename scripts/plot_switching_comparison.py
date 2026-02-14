
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

def plot_comparison():
    # 1. Load Data
    try:
        print("Loading GARAM_Data/60day_equity.csv...")
        baseline_df = pd.read_csv("GARAM_Data/60day_equity.csv", parse_dates=['ts'])
        print(f"Baseline: {len(baseline_df)} rows")
        
        print("Loading GARAM_Data/switching_equity.csv (Failed) -> Using Reconstructed...")
        alpha_df = pd.read_csv("GARAM_Data/reconstructed_alpha.csv", parse_dates=['ts'])
        print(f"Alpha: {len(alpha_df)} rows")
        
        if baseline_df.empty or alpha_df.empty:
            print("One of the dataframes is empty.")
            return

    except Exception as e:
        print(f"Error loading files: {e}")
        import traceback
        traceback.print_exc()
        return

    # 2. Resample to 5min for cleaner plot
    baseline_df.set_index('ts', inplace=True)
    alpha_df.set_index('ts', inplace=True)
    
    b_res = baseline_df['Total_Equity'].resample('30T').last().dropna()
    a_res = alpha_df['Total_Equity'].resample('30T').last().dropna()
    
    # 3. Plot
    plt.figure(figsize=(12, 6))
    
    plt.plot(b_res.index, b_res.values / 1000000, label='Baseline (Phase 35)', color='gray', linestyle='--')
    plt.plot(a_res.index, a_res.values / 1000000, label='Alpha Mode (Phase 36-A)', color='blue', linewidth=2)
    
    # 4. Highlight Max Drawdown areas if possible? (Simpler: just text)
    b_final = b_res.iloc[-1]
    a_final = a_res.iloc[-1]
    
    plt.title(f"Strategy Comparison (60-Day): Baseline vs Alpha Mode\nAlpha Mode: {a_final/1000000:.2f}M vs Baseline: {b_final/1000000:.2f}M")
    plt.ylabel("Equity (Million KRW)")
    plt.grid(True, alpha=0.3)
    plt.legend()
    
    # Date formatting
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
    plt.gcf().autofmt_xdate()
    
    plt.savefig("GARAM_Data/comparison_plot.png")
    print("Saved GARAM_Data/comparison_plot.png")

if __name__ == "__main__":
    plot_comparison()
