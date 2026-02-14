
import pandas as pd
import os

CSV_PATH = "GARAM_Data/5day_equity_hybrid.csv"

def check_evidence():
    if not os.path.exists(CSV_PATH):
        print("No CSV found.")
        return

    df = pd.read_csv(CSV_PATH)
    df["ts"] = pd.to_datetime(df["ts"])
    
    # 1. Daily EOD Equity
    print("--- Daily EOD Equity ---")
    df['date'] = df['ts'].dt.date
    daily_groups = df.groupby('date')
    
    for date, group in daily_groups:
        # Get last entry of the day
        last_entry = group.iloc[-1]
        print(f"{date}: {last_entry['Total_Equity']:.0f} KRW")

    # 2. Timezone Check
    print("\n--- Timezone Check ---")
    print(f"Min: {df['ts'].min()}")
    print(f"Max: {df['ts'].max()}")
    print("Top 5 Frequent Times:")
    print(df["ts"].dt.time.value_counts().head(5))

if __name__ == "__main__":
    check_evidence()
