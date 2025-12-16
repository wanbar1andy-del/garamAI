import FinanceDataReader as fdr
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import os

def main():
    print("Fetching KOSPI data...")
    # 2 Years + buffer
    start_date = (datetime.now() - timedelta(days=800)).strftime('%Y-%m-%d')
    end_date = datetime.now().strftime('%Y-%m-%d')
    output_dir = Path("c:/garam/garam/GARAM_Data/kr/index")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "kospi_dashboard.csv"

    try:
        # Fetch KOSPI (KS11)
        df = fdr.DataReader('KS11', start_date, end_date)
        
        # Save simply: date, close
        if 'Close' in df.columns:
            df = df[['Close']]
            df.reset_index(inplace=True)
            df.columns = ['date', 'close'] # Lowercase for consistency
            
            df.to_csv(output_path, index=False)
            print(f"Saved KOSPI data to {output_path}")
            print(df.tail())
        else:
            print("Error: 'Close' column not found in data")
            
    except Exception as e:
        print(f"Failed to fetch KOSPI: {e}")

if __name__ == "__main__":
    main()
