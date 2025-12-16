import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

DATA_DIR = r"c:\garam\garam\GARAM_Data\history\daily"
os.makedirs(DATA_DIR, exist_ok=True)

symbols = ["458870", "353200", "440110", "298040", "007660"]
base_prices = [122200, 46550, 25600, 1848000, 136500]

for sym, base in zip(symbols, base_prices):
    dates = [datetime.now() - timedelta(days=x) for x in range(30, 0, -1)]
    prices = []
    curr = base * 0.9 # Start lower
    for _ in dates:
        change = np.random.uniform(-0.03, 0.03)
        curr = curr * (1 + change)
        prices.append(int(curr))
    
    # Ensure last price matches/close to base
    prices[-1] = base 
    
    df = pd.DataFrame({
        'date': [d.strftime('%Y-%m-%d') for d in dates],
        'close': prices,
        'open': prices,
        'high': prices,
        'low': prices,
        'volume': [1000] * 30
    })
    
    file_path = os.path.join(DATA_DIR, f"{sym}_daily.csv")
    df.to_csv(file_path, index=False)
    print(f"Created {file_path}")
