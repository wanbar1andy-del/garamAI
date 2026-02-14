import pandas as pd
from pathlib import Path
import sys

# Define path
data_dir = Path('GARAM_Data/60day_replay_kst')

if not data_dir.exists():
    print(f"Error: Directory {data_dir} does not exist.")
    sys.exit(1)

clean_list = []
print(f"Scanning {data_dir}...")
files = list(data_dir.glob('*.csv'))
print(f"Found {len(files)} files.")

for f in files:
    try:
        # Optimization: Read only 'ts' column
        df = pd.read_csv(f, usecols=['ts'])
        # Check unique days. Format is YYYY-MM-DD HH:MM:SS.
        # Slice(0, 10) gives YYYY-MM-DD.
        if df['ts'].astype(str).str.slice(0, 10).nunique() >= 60:
            clean_list.append(f.stem)
    except Exception as e:
        # print(f"Error reading {f.name}: {e}")
        continue

output_path = Path('config/clean_universe.csv')
# Ensure config dir exists
output_path.parent.mkdir(parents=True, exist_ok=True)

pd.DataFrame(clean_list, columns=['ticker']).to_csv(output_path, index=False)
print(f'Audit Complete: {len(clean_list)} tickers are 100% complete.')
