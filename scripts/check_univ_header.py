import pandas as pd
from pathlib import Path

path = Path("GARAM_Data/real_universe_400.csv")
if path.exists():
    df = pd.read_csv(path)
    print(f"Columns: {df.columns.tolist()}")
    print(df.head(1))
else:
    print("File not found")
