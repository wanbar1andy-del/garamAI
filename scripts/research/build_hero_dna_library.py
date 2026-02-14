"""
[GARAM] Hero DNA Library Builder
Objective: Build a statistical library of "Signals" and their forward 120m outcomes.
Definition:
- Signal: Score >= 1.0 (Ret5 * VolSpike)
- Hero: Signal -> MFE_120m >= 10%
- Scanning: 60-day minute data (Top daily volume targets)

Outputs: logs/dna/hero_library.csv
"""
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, time, timedelta
import sys
import logging

# Setup
PROJECT_ROOT = Path("C:/garam/garam")
sys.path.append(str(PROJECT_ROOT))
DATA_DIR = PROJECT_ROOT / "GARAM_Data/60day_replay_kst"
OUT_DIR = PROJECT_ROOT / "logs/dna"
OUT_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')

def build_library():
    logging.info("Scanning Files to build Universe...")
    files = list(DATA_DIR.glob("*.csv"))
    
    # 1. Identify active tickers per day (Optimization)
    # We want "Candidates" - i.e. stocks that had volume/movement.
    # To save time, we'll scan all, but process only those with significant daily range or vol.
    # actually, minute processing is fast enough if we don't do complex networking.
    
    signals = []
    
    # Process file by file to save memory (Simulating "All Data" scan)
    # 400 files.
    cnt = 0
    for f in files:
        if '329180' in f.name: continue
        try:
            df = pd.read_csv(f)
            # Norm
            cols = df.columns
            if 'ts' in cols: df.rename(columns={'ts':'date'}, inplace=True)
            elif 'Date' in cols: df.rename(columns={'Date':'date'}, inplace=True)
            df['date'] = pd.to_datetime(df['date'])
            df.sort_values('date', inplace=True)
            df.set_index('date', inplace=True)
            
            # Filter Market Hours 09:00-15:20
            df = df.between_time('09:00', '15:20')
            if df.empty: continue
            
            tkr = f.stem
            
            # Intra-day Loop
            # We need Rolling features.
            # Convert to numpy for speed
            closes = df['close'].values.astype(float)
            vols = df['volume'].values.astype(float)
            times = df.index
            
            if len(closes) < 20: continue
            
            # Vectorized Score Calc?
            # Score = Ret5 * VolSpike
            # Ret5
            s_c = pd.Series(closes)
            s_v = pd.Series(vols)
            ret5 = s_c.pct_change(5).fillna(0).values
            
            # VolSpike
            v_avg = s_v.rolling(20).mean().fillna(1).values
            v_spike = vols / (v_avg + 1e-9)
            v_spike = np.clip(v_spike, 0, 3.0)
            
            scores = ret5 * v_spike * 100
            
            # Scan for Signals
            cooldown_until = pd.Timestamp.min
            
            for i in range(20, len(closes)):
                t = times[i]
                if t <= cooldown_until: continue
                
                sc = scores[i]
                if sc >= 1.0: # SIGNAL!
                    # Forward Analysis
                    entry_px = closes[i]
                    max_scan = min(len(closes), i + 120) # 120 mins forward
                    
                    forward_c = closes[i:max_scan]
                    forward_t = times[i:max_scan]
                    
                    if len(forward_c) < 5: continue
                    
                    # Metrics
                    peak_px = np.max(forward_c)
                    min_px = np.min(forward_c)
                    
                    mfe_val = (peak_px - entry_px) / entry_px
                    mae_val = (min_px - entry_px) / entry_px
                    
                    # Times to Thrust
                    t_1pct = next((k for k,px in enumerate(forward_c) if (px-entry_px)/entry_px >= 0.01), -1)
                    t_2pct = next((k for k,px in enumerate(forward_c) if (px-entry_px)/entry_px >= 0.02), -1)
                    t_3pct = next((k for k,px in enumerate(forward_c) if (px-entry_px)/entry_px >= 0.03), -1)
                    
                    # Shakeout Depth (Drop BEFORE Peak)
                    peak_idx = np.argmax(forward_c)
                    if peak_idx > 0:
                        pre_peak_min = np.min(forward_c[:peak_idx])
                        shakeout_depth = (pre_peak_min - entry_px) / entry_px
                    else:
                        shakeout_depth = 0.0
                        
                    is_hero = 1 if mfe_val >= 0.10 else 0
                    
                    signals.append({
                        'ticker': tkr,
                        'entry_time': t,
                        'entry_px': entry_px,
                        'score_init': sc,
                        'mfe_120': mfe_val,
                        'mae_120': mae_val,
                        'shakeout_depth': shakeout_depth,
                        't_1pct': t_1pct,
                        't_2pct': t_2pct,
                        't_3pct': t_3pct,
                        'is_hero': is_hero
                    })
                    
                    # Set Cooldown (e.g. 120 mins to capture full run)
                    # We want distinct runs.
                    cooldown_until = t + timedelta(minutes=120)

            cnt += 1
            if cnt % 50 == 0: logging.info(f"Processed {cnt} files...")
            
        except Exception as e:
            logging.error(f"Error {f}: {e}")
            
    # Save
    logging.info(f"Scanning Done. Total Signals: {len(signals)}")
    df_sig = pd.DataFrame(signals)
    out_path = OUT_DIR / "hero_library.csv"
    df_sig.to_csv(out_path, index=False)
    
    # Quick Summary
    heroes = df_sig[df_sig['is_hero'] == 1]
    logging.info(f"Total Heroes Found: {len(heroes)} ({len(heroes)/len(df_sig)*100:.1f}%)")
    
if __name__ == "__main__":
    build_library()
