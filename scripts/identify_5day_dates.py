
import pandas as pd
import os

FILE_PATH = "GARAM_Data/minute/kr/005930.csv"

def identify_dates():
    if not os.path.exists(FILE_PATH):
        print(f"File not found: {FILE_PATH}")
        return

    # Read distinct dates (optimization: read 'date' or 'timestamp' col)
    # File likely has no header or specific header.
    # Previous task showed: datetime, open, high, low, close, volume (descending)
    
    df = pd.read_csv(FILE_PATH)
    # Col 0 is datetime (int or str)
    col0 = df.columns[0]
    
    # Check format
    sample = df[col0].iloc[0]
    print(f"Sample TS: {sample}")
    
    # Convert to datetime
    if isinstance(sample, (int, float)):
        df['dt'] = pd.to_datetime(df[col0].astype(str), format='%Y%m%d%H%M%S')
    else:
        df['dt'] = pd.to_datetime(df[col0])
        
    # Get unique dates
    unique_dates = df['dt'].dt.date.unique()
    unique_dates.sort()
    
    last_5 = unique_dates[-5:]
    print("Last 5 Business Days:")
    for d in last_5:
        print(d)

if __name__ == "__main__":
    identify_dates()
