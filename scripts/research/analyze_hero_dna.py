import pandas as pd
import numpy as np

FILE = "logs/dna/hero_library.csv"

def analyze():
    df = pd.read_csv(FILE)
    heroes = df[df['is_hero'] == 1]
    candidates = df[df['is_hero'] == 0]
    
    # 1. Time-to-Thrust
    print("## 1. Time-to-Thrust Distribution (Heroes only)")
    tt = heroes[['t_1pct', 't_2pct', 't_3pct']].describe(percentiles=[0.25, 0.5, 0.75])
    print(tt.to_markdown())
    print("\n*Note: -1 means did not reach target.*")
    
    # 2. Shakeout Depth (Drop before Peak)
    print("\n## 2. Shakeout Depth Distribution (Heroes)")
    sd = heroes['shakeout_depth'].describe(percentiles=[0.1, 0.25, 0.5])
    print(sd.to_markdown())
    
    # 3. Mid-Cycle Shakeout (Proxy: MAE vs MFE)
    # If Hero reached > 10%, what was the max drop? (MAE)
    print("\n## 3. Max Adversity (MAE) during Hero Run")
    ma = heroes['mae_120'].describe(percentiles=[0.1, 0.25, 0.5])
    print(ma.to_markdown())
    
    # 4. Remaining Upside (EU) vs Initial Score
    # Binning by Score categories
    df['score_bin'] = pd.cut(df['score_init'], bins=[1, 2, 5, 10, 100], labels=['1-2', '2-5', '5-10', '10+'])
    print("\n## 4. Remaining Upside (MFE 120) by Initial Score")
    eu = df.groupby('score_bin')['mfe_120'].describe()[['count', 'mean', '50%', 'max']]
    print(eu.to_markdown())
    
    # 5. Failure Signature (Candidates)
    print("\n## 5. Failure Signature (Non-Heroes)")
    fail_stats = candidates[['mfe_120', 'mae_120']].describe()
    print(fail_stats.to_markdown())
    
    # 6. Stage Transition (Candidate -> Confirmed)
    # Probability of reaching +1.2% (Confirmed) from Signal
    # And Probability of reaching Hero (10%) from Confirmed
    
    total = len(df)
    confirmed = len(df[df['mfe_120'] >= 0.012])
    real_hero = len(heroes)
    
    p_cand_conf = confirmed / total
    p_conf_hero = real_hero / confirmed if confirmed > 0 else 0
    
    print("\n## 6. Stage Transition Probabilities")
    print(f"* Candidate -> Confirmed (+1.2%): {p_cand_conf*100:.1f}%")
    print(f"* Confirmed -> Hero (+10%): {p_conf_hero*100:.1f}%")
    print(f"* Base Rate (Cand -> Hero): {real_hero/total*100:.1f}%")

if __name__ == "__main__":
    analyze()
