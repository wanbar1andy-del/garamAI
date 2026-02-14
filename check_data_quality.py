import pandas as pd
import numpy as np
import glob
from pathlib import Path

data_dir = Path("c:/garam/garam/GARAM_Data/history/minute")
files = glob.glob(str(data_dir / "*.csv"))[:10]

print(f"--- Data Quality Check ({len(files)} samples) ---")
for f in files:
    df = pd.read_csv(f)
    print(f"File: {Path(f).name} | Rows: {len(df)} | Last Date: {df.iloc[-1, 0]}")
    # Check for Price 0 or NaN
    zeros = (df['close'] == 0).sum()
    nans = df['close'].isnull().sum()
    print(f"   Zeros: {zeros} | NaNs: {nans}")
