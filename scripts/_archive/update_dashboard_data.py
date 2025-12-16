import sys
import pandas as pd
from pathlib import Path

sys.path.insert(0, 'c:/garam')
from garam.config import PATHS

# 1. Load Comparison Data
comp_path = Path("C:/Users/wanba/.gemini/antigravity/brain/cd157bd2-0327-40b0-8357-ad55c78ee0e1/comparison_1year_AC.csv")
df = pd.read_csv(comp_path, index_col='date', parse_dates=True)

print(f"Loaded comparison data: {len(df)} rows")
print(f"Columns: {df.columns.tolist()}")

# 2. Load KOSPI Data for Benchmark
kospi_path = PATHS.HISTORY_DIR / "labeled_KR_KOSPI_daily_20y.csv"

if kospi_path.exists():
    df_kospi = pd.read_csv(kospi_path)
    col_map = {c: c.lower() for c in df_kospi.columns}
    df_kospi.rename(columns=col_map, inplace=True)
    date_col = 'timestamp' if 'timestamp' in df_kospi.columns else 'date'
    df_kospi[date_col] = pd.to_datetime(df_kospi[date_col])
    df_kospi.set_index(date_col, inplace=True)
    df_kospi.sort_index(inplace=True)
    
    # Align KOSPI to same date range
    df_kospi = df_kospi.loc[df.index[0]:df.index[-1]]
    
    # Calculate KOSPI equity curve (starting at 100M)
    initial_cap = 100_000_000
    kospi_ret = df_kospi['close'].pct_change().fillna(0.0)
    kospi_equity = (1 + kospi_ret).cumprod() * initial_cap
    
    print(f"KOSPI data loaded: {len(kospi_equity)} rows")
else:
    print("WARNING: KOSPI data not found, using mock data")
    initial_cap = 100_000_000
    kospi_equity = pd.Series(initial_cap, index=df.index)

# 3. Convert from Index (100) to KRW (100M)
# Current format: Eq_A, Eq_B are indices starting at 100
# Need format: engine1, engine2 in KRW starting at 100M

# Convert: (Index / 100) * 100M
initial_cap = 100_000_000

df['engine1'] = (df['Eq_A'] / 100.0) * initial_cap
df['engine2'] = (df['Eq_B'] / 100.0) * initial_cap

# Add KOSPI
if kospi_path.exists():
    df['kospi'] = kospi_equity.reindex(df.index, method='ffill').fillna(initial_cap)
else:
    df['kospi'] = initial_cap

# 4. Format for Dashboard
output_df = df[['engine1', 'engine2', 'kospi']].copy()

# **FIX: Replace NaN values with forward fill, then 0**
output_df = output_df.fillna(method='ffill').fillna(0)

# Round to integers
output_df = output_df.round(0).astype(int)

# 5. Save to Dashboard Location
output_path = PATHS.DATA_DIR / "reports" / "simulation_1year_turbo.csv"
output_path.parent.mkdir(parents=True, exist_ok=True)

output_df.to_csv(output_path)

print(f"\n✓ Dashboard data updated: {output_path}")
print("\nFinal Values:")
print(f"  Engine1 (Strategy A - Turbo 2.4x): {output_df['engine1'].iloc[-1]:,} KRW (+{((output_df['engine1'].iloc[-1]/initial_cap)-1)*100:.1f}%)")
print(f"  Engine2 (Strategy C - Filter): {output_df['engine2'].iloc[-1]:,} KRW (+{((output_df['engine2'].iloc[-1]/initial_cap)-1)*100:.1f}%)")
print(f"  KOSPI: {output_df['kospi'].iloc[-1]:,} KRW (+{((output_df['kospi'].iloc[-1]/initial_cap)-1)*100:.1f}%)")

print("\nSample (last 5 rows):")
print(output_df.tail())
