import pandas as pd
import numpy as np
import glob

def analyze(file):
    try:
        df = pd.read_csv(file)
        if df.empty: return None
        
        # Calculate Stats
        df['ret'] = df['equity'].pct_change()
        df['cummax'] = df['equity'].cummax()
        df['dd'] = (df['equity'] - df['cummax']) / df['cummax']
        
        final_eq = df['equity'].iloc[-1]
        start_eq = df['equity'].iloc[0]
        total_ret = (final_eq / start_eq) - 1
        mdd = df['dd'].min()
        
        # Days
        days = len(df)
        years = days / 252.0 if days > 0 else 1.0
        cagr = (final_eq / start_eq) ** (1/years) - 1 if final_eq > 0 else 0
        
        calmar = abs(cagr / mdd) if mdd != 0 else 0
        
        return {
            "File": file,
            "Equity": f"{final_eq / 100_000_000:.2f}억",
            "Return": f"{total_ret*100:.1f}%",
            "MDD": f"{mdd*100:.1f}%",
            "Calmar": f"{calmar:.2f}",
            "CAGR": f"{cagr*100:.1f}%"
        }
    except Exception as e:
        return {"File": file, "Error": str(e)}

files = [
    "sim_base_check.csv",
    "sim_v2_baseline.csv", 
    "sim_v21_trailing08.csv", 
    "sim_v21_strict.csv", 
    "sim_v21_conc.csv"
]

results = []
for f in files:
    res = analyze(f)
    if res: results.append(res)

print(pd.DataFrame(results)[["File", "Equity", "Return", "MDD", "Calmar"]])
