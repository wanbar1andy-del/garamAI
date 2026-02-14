
import pandas as pd
from pathlib import Path

DIR = Path("C:/garam/garam/logs/phase4_sweep")

def calc(name, file):
    if not file.exists(): return
    df = pd.read_csv(file)
    init = df['equity'].iloc[0]
    final = df['equity'].iloc[-1]
    ret = (final/init - 1)*100
    
    # MDD
    roll_max = df['equity'].cummax()
    dd = (df['equity'] - roll_max) / roll_max
    mdd = dd.min() * 100
    
    print(f"[{name}] Return: {ret:.2f}% | MDD: {mdd:.2f}%")

calc("Baseline", DIR / "equity_PYRAMID_0.7.csv")
calc("Aesthetic", DIR / "equity_PYRAMID_0.7_AESTHETIC.csv")
