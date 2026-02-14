import pandas as pd
from pathlib import Path

def fix_unsorted(symbol):
    path = Path(f"GARAM_Data/history/minute/{symbol}.csv")
    if not path.exists():
        print(f"File not found: {path}")
        return
        
    print(f"Loading {path}...")
    df = pd.read_csv(path, dtype={"date": str})
    
    # Sort
    print("Sorting...")
    df["dt_temp"] = pd.to_datetime(df["date"], format="%Y%m%d%H%M%S")
    df = df.sort_values("dt_temp").drop(columns=["dt_temp"])
    
    # Save
    print("Saving...")
    df.to_csv(path, index=False)
    print("Done.")

if __name__ == "__main__":
    fix_unsorted("010620")
