"""
[PHASE 4] OSS EVENT-DRIVEN MEMORY (EDM) TRAINER
- Purpose: Train the Brain to recognize specific Market Events (Explosion, Squeeze, Reversal).
- Logic:
  1. Detect Event (Volume Spike, Range Expansion, etc.)
  2. Snapshot Context (Low/High Base, RSI, Volatility).
  3. Wait for Outcome (Forward Return).
  4. Store [Event + Context -> Outcome] into Episodic Memory.
"""

import sys
import os
import pandas as pd
import numpy as np
import torch
import json
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path("C:/garam/garam")
sys.path.append(str(PROJECT_ROOT))

# Load Core
from scripts.neural_brain import GaramNeuralBrain
from pipeline.backtest.run_alpha_robust import AlphaGenius_V2

def log(msg):
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {msg}")

# [EDM] Event Definitions
def detect_market_events(row, vol_ratio, daily_volatility):
    """
    Returns a list of events detected at this timestamp.
    """
    events = []
    
    # 1. Energy Explosion (The "Pulse")
    # Volume > 3.0x avg AND Range > 1.05 (5% body)
    # Refined: Use relative checks
    body_size = abs(row['close'] - row['open']) / row['open']
    if vol_ratio > 3.0 and body_size > 0.05:
        events.append("ENERGY_EXPLOSION")
        
    # 2. Energy Squeeze (The "Coil")
    # Volume < 0.5x avg AND Range < 0.015 (1.5% range)
    high_low_range = (row['high'] - row['low']) / row['close']
    if vol_ratio < 0.5 and high_low_range < 0.015:
        events.append("ENERGY_SQUEEZE")
        
    return events

def run_edm_training(start_date="20250701", end_date="20250715"):
    log(f"🔥 Starting EDM Training (Curriculum: {start_date}-{end_date})")
    
    # 1. Load Data (Full OHLCV for EDM)
    # Define Loading Logic locally to ensure OHLCV
    data_dir = PROJECT_ROOT / "GARAM_Data/minute/kr"
    
    log(f"📚 Loading OHLCV Data from {data_dir} ({start_date}-{end_date})...")
    
    # Custom Loader for Matrix Construction
    all_files = list(data_dir.glob("*.csv"))
    # Filter by user request (July 2025) usually implies a subset
    # for speed, we'll try to load all and slice, or filter file names if possible?
    # Filenames are symbols. We have to read content to check date.
    
    opens, highs, lows, closes, volumes = {}, {}, {}, {}, {}
    
    # Parallel Load
    from concurrent.futures import ThreadPoolExecutor
    
    def _load_ohlcv(fpath):
        try:
            df = pd.read_csv(fpath)
            cols = [c.lower() for c in df.columns]
            df.columns = cols
            if "datetime" in df.columns: df = df.rename(columns={"datetime": "date"})
            
            # Date Parsing
            if "date" in df.columns:
                 df["dt"] = pd.to_datetime(df["date"].astype(str), format="%Y%m%d%H%M%S", errors='coerce')
                 if df["dt"].isnull().all():
                     df["dt"] = pd.to_datetime(df["date"].astype(str), format="%Y%m%d%H%M", errors='coerce')
            
            df = df.dropna(subset=["dt"]).set_index("dt").sort_index()
            
            # Date Filter
            mask = (df.index >= pd.to_datetime(start_date)) & (df.index <= pd.to_datetime(end_date))
            df = df.loc[mask]
            
            if df.empty: return None
            return (fpath.stem, df)
        except:
            return None

    with ThreadPoolExecutor(max_workers=8) as executor:
        results = executor.map(_load_ohlcv, all_files[:400]) # Limit to 400 for memory safety
        
    for res in results:
        if res:
            sym, df = res
            opens[sym] = df['open']
            highs[sym] = df['high']
            lows[sym] = df['low']
            closes[sym] = df['close']
            volumes[sym] = df['volume']

    # Build DataFrames
    df_o = pd.DataFrame(opens).fillna(method='ffill')
    df_h = pd.DataFrame(highs).fillna(method='ffill')
    df_l = pd.DataFrame(lows).fillna(method='ffill')
    df_c = pd.DataFrame(closes).fillna(method='ffill')
    df_v = pd.DataFrame(volumes).fillna(0)
    
    if df_c.empty:
        log("❌ No data found in range.")
        return

    log(f"✅ Loaded {len(df_c.columns)} symbols. Building Features...")

    # 2. Features (Context) via AlphaGenius
    alpha = AlphaGenius_V2(mode="ULTRA_AGGRESSIVE")
    # This populates alpha.last_state_map
    # We pass C/V as usual
    _ = alpha.calculate_signals(df_c, df_v) 
    
    # Extract Context Maps
    ctx_rsi = alpha.last_state_map['rsi']
    ctx_vol = alpha.last_state_map['vol_ratio']
    ctx_trend = alpha.last_state_map['trend_15m']
    ctx_squeeze = alpha.last_state_map.get('width_z', pd.DataFrame(0, index=df_c.index, columns=df_c.columns))
    
    # 3. Brain & Memory
    brain = GaramNeuralBrain(mode="MAX")
    BRAIN_PATH = PROJECT_ROOT / "results/oss_archive/neuro_brain_state.pth"
    if BRAIN_PATH.exists():
        try:
            brain.load_state_dict(torch.load(BRAIN_PATH))
            log("🧠 Brain State Loaded.")
        except:
            log("⚠️ Brain State Corrupted. Starting Fresh.")
    
    MEMORY_FILE = PROJECT_ROOT / "core/active_config/oss_episodic_memory.json"
    if MEMORY_FILE.exists():
         with open(MEMORY_FILE, 'r') as f:
            brain.memory_bank = json.load(f)

    # 4. EDM Scanning Loop
    log("⚡ Scanning for Events (Explosions & Squeezes)...")
    
    # Vectorized Event Detection
    # Energy Explosion: Vol > 3.0x avg AND Body > 2% (Relaxed from 5% for 1m bars)
    body_pct = (df_c - df_o).abs() / df_o
    is_explosion = (ctx_vol > 3.0) & (body_pct > 0.02)
    
    # Energy Squeeze: Vol < 0.3x avg AND Range < 0.5% (Tightened)
    range_pct = (df_h - df_l) / df_c
    is_squeeze = (ctx_vol < 0.3) & (range_pct < 0.005)
    
    # Future Outcome (Forward 120m Max Return)
    indexer = pd.api.indexers.FixedForwardWindowIndexer(window_size=120)
    future_max = df_c.rolling(window=indexer).max()
    future_ret = (future_max / df_c) - 1.0
    
    # Iterate and Visualize/Store
    
    # Explosion
    expl_indices = is_explosion.stack()
    expl_indices = expl_indices[expl_indices].index.tolist() 
    
    log(f"   -> Found {len(expl_indices)} ENERGY EXPLOSIONS (Target: >3x Vol, >2% Body)")
    
    count = 0
    for ts, sym in expl_indices:
        try:
            c_rsi = ctx_rsi.loc[ts, sym]
            c_vol = ctx_vol.loc[ts, sym]
            # ... (Context extraction same)
            c_trd = ctx_trend.loc[ts, sym]
            c_sqz = ctx_squeeze.loc[ts, sym]
            outcome = future_ret.loc[ts, sym]
            
            if np.isnan(outcome): continue
            
            context_vector = [c_vol, c_rsi, float(c_trd), c_sqz]
            brain.learn_context("ENERGY_EXPLOSION", context_vector, outcome)
            count += 1
        except KeyError: continue
        
    # Squeeze (Sampled to avoid 400k events)
    sqz_indices = is_squeeze.stack()
    sqz_indices = sqz_indices[sqz_indices].index.tolist()
    
    # Sampling: Cap at 5000 random squeezes
    import random
    if len(sqz_indices) > 5000:
        log(f"   -> Found {len(sqz_indices)} ENERGY SQUEEZES (Sampling 5000...)")
        sqz_indices = random.sample(sqz_indices, 5000)
    else:
        log(f"   -> Found {len(sqz_indices)} ENERGY SQUEEZES")
    
    for ts, sym in sqz_indices:
        try:
            c_rsi = ctx_rsi.loc[ts, sym]
            c_vol = ctx_vol.loc[ts, sym]
            c_trd = ctx_trend.loc[ts, sym]
            c_sqz = ctx_squeeze.loc[ts, sym]
            outcome = future_ret.loc[ts, sym]
            
            if np.isnan(outcome): continue
            
            context_vector = [c_vol, c_rsi, float(c_trd), c_sqz]
            brain.learn_context("ENERGY_SQUEEZE", context_vector, outcome)
            count += 1
        except KeyError: continue

    log(f"🧠 Total New Memories Formed: {count}")
    
    # Save Memory
    with open(MEMORY_FILE, 'w') as f:
        json.dump(brain.memory_bank, f)
    log("💾 Episodic Memory Saved.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--start_date", type=str, default="20250701")
    parser.add_argument("--end_date", type=str, default="20250715")
    args = parser.parse_args()
    
    run_edm_training(args.start_date, args.end_date)
