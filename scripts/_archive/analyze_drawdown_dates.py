import pandas as pd
import sys

csv_path = r"c:\garam\garam\GARAM_Data\reports\simulation_1year_turbo.csv"
try:
    df = pd.read_csv(csv_path)
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)
    
    # Calculate Drawdown for Engine 1 (Legacy) and Engine 2 (Advanced/Turbo)
    # User said "Graph", likely referring to the main result which is usually Engine 2 or the Combined?
    # The chart showed Engine 2 doing better but still dropping.
    # Let's analyze Engine 1 (since user asked "why didn't we choose other stocks", implies selecting bad ones).
    # Engine 1 is the stock picker. Engine 2 is the allocator.
    # BUT Engine 1 curve in the CSV is "Base Engine" performance?
    # Let's check both.
    
    def get_max_drawdown(series):
        peak = series.cummax()
        dd = (series - peak) / peak
        min_dd = dd.min()
        end_date = dd.idxmin()
        # Find start date (peak before end_date)
        peak_date = series[:end_date].idxmax()
        return min_dd, peak_date, end_date

    dd1, s1, e1 = get_max_drawdown(df['engine1'])
    dd2, s2, e2 = get_max_drawdown(df['engine2'])
    
    print(f"Engine 1 (Legacy) MDD: {dd1*100:.2f}% (From {s1.date()} to {e1.date()})")
    print(f"Engine 2 (Advanced) MDD: {dd2*100:.2f}% (From {s2.date()} to {e2.date()})")
    
    # Let's focus on the period with the worst performance for Engine 1 (Stock Selection)
    target_start = pd.Timestamp("2025-10-01") # Based on visual memory of Nov Drop
    target_end = pd.Timestamp("2025-12-01")
    
    subset = df.loc[target_start:target_end]
    if not subset.empty:
        dd_sub, ss, es = get_max_drawdown(subset['engine1'])
        print(f"Nov-Dec Focus (Engine 1): {dd_sub*100:.2f}% (From {ss.date()} to {es.date()})")

except Exception as e:
    print(e)
