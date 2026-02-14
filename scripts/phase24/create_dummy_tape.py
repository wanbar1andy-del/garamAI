# scripts/phase24/create_dummy_tape.py
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def main():
    # Target dates from flow metrics (Dec 1 is Sunday, data starts Dec 5, 8...)
    # Let's use Dec 22-26 which has data in the snippet provided before
    dates = pd.date_range("2025-12-01", "2025-12-29", freq="B")
    
    rows = []
    # 005930 (Hero) vs 999999 (Competitor)
    np.random.seed(42)
    
    for d in dates:
        # Market hours 09:00 - 15:30, 5 min anchors
        ts_range = pd.date_range(f"{d.strftime('%Y-%m-%d')} 09:05", f"{d.strftime('%Y-%m-%d')} 15:30", freq="5min")
        
        for ts in ts_range:
            # Random score
            s_hero = np.random.uniform(50, 70)
            s_comp = np.random.uniform(50, 75)
            
            # Rank 1 and 2
            if s_hero > s_comp:
                rows.append({"ts": ts, "rank": 1, "symbol": "005930", "score": s_hero})
                rows.append({"ts": ts, "rank": 2, "symbol": "999999", "score": s_comp})
            else:
                rows.append({"ts": ts, "rank": 1, "symbol": "999999", "score": s_comp})
                rows.append({"ts": ts, "rank": 2, "symbol": "005930", "score": s_hero})
                
    df = pd.DataFrame(rows)
    out_path = "results/phase24/tape/decision_tape.csv"
    import os
    os.makedirs("results/phase24/tape", exist_ok=True)
    df.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"Created dummy tape at {out_path} with {len(df)} rows")

if __name__ == "__main__":
    main()
