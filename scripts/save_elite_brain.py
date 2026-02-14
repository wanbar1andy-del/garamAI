
import sys
import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from pathlib import Path
from tqdm import tqdm
import random

# Setup Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))
from scripts.neural_brain import GaramNeuralBrain

def save_brain():
    print("=== [BAKING ELITE BRAIN] Re-creating the Winner State ===")
    
    # 1. Init Brain
    brain = GaramNeuralBrain(input_size=10, mode="MEDIUM")
    
    # 2. Load & Prep Data
    symbol = "005930"
    path = PROJECT_ROOT / f"GARAM_Data/history/minute/{symbol}.csv"
    if not path.exists():
        print("Data missing.")
        return
        
    df = pd.read_csv(path)
    df.columns = [c.lower() for c in df.columns]
    if 'date' in df.columns: df['time'] = pd.to_datetime(df['date'].astype(str), errors='coerce')
    else: df['time'] = df.index
    df = df.dropna(subset=['time'])
    mask = (df['time'] >= "2025-06-01") & (df['time'] <= "2026-02-06")
    df = df.loc[mask].sort_values('time').reset_index(drop=True)
    
    # Feature Engineering (The 10-Feature Set from Self-Play)
    df['ret'] = df['close'].pct_change()
    df['vol'] = df['ret'].rolling(20).std()
    
    f1 = (df['vol'] / df['vol'].rolling(100).mean()).fillna(0).values 
    f2 = ((df['close'].rolling(5).mean() - df['close'].rolling(60).mean())/df['close'].rolling(60).mean()).fillna(0).values * 100
    f3 = (df['volume'] / df['volume'].rolling(20).mean()).fillna(0).values
    f4 = ((df['close'] - df['close'].rolling(20).mean()) / df['close'].rolling(20).mean()).fillna(0).values * 100
    f5 = df['close'].pct_change(5).fillna(0).values * 100
    f_dummy = np.zeros((len(df), 5)) # Placeholders used in self-play
    
    features = np.column_stack([f1, f2, f3, f4, f5, f_dummy])
    features = (features - np.mean(features, axis=0)) / (np.std(features, axis=0) + 1e-5)
    
    # 3. Labeling (The Winning Formula: 3% ROI + Safety)
    print("[LABELING] Applying 'Sniper' Criteria (>3% ROI, <3% DD)...")
    closes = df['close'].values
    lookahead = 60
    full_X = []
    full_y = []
    
    for i in range(len(df) - lookahead):
        curr = closes[i]
        future = closes[i+1 : i+lookahead]
        mx = np.max(future)
        mn = np.min(future)
        
        ret = (mx - curr) / curr
        dd = (curr - mn) / curr
        
        if ret > 0.03 and dd < 0.03:
            full_X.append(features[i])
            full_y.append([1.0, 0.0]) # Hero
        else:
            full_X.append(features[i])
            full_y.append([0.0, 0.0])
            
    # Oversampling
    X_pos = [x for i, x in enumerate(full_X) if full_y[i][0] == 1.0]
    y_pos = [y for y in full_y if y[0] == 1.0]
    
    if len(X_pos) > 0:
        rep = int(len(full_X) / len(X_pos)) // 2
        print(f"[SAMPLING] Boosting Elite Samples x{rep}")
        full_X.extend(X_pos * rep)
        full_y.extend(y_pos * rep)
        
    X_t = torch.tensor(np.array(full_X), dtype=torch.float32).to(brain.device)
    y_t = torch.tensor(np.array(full_y), dtype=torch.float32).to(brain.device)
    
    # 4. Train
    print("[TRAINING] Final Bake (20 Epochs)...")
    brain.train()
    opt = optim.Adam(brain.parameters(), lr=0.0005)
    crit = nn.MSELoss()
    
    batch_size = 20000
    
    for ep in tqdm(range(20)):
        perm = torch.randperm(len(X_t))
        X_s = X_t[perm]
        y_s = y_t[perm]
        
        for i in range(0, len(X_t), batch_size):
            end = i + batch_size
            opt.zero_grad()
            out = brain.net(X_s[i:end])
            loss = crit(out, y_s[i:end])
            loss.backward()
            opt.step()
            
    # 5. Save
    save_dir = PROJECT_ROOT / "models"
    save_dir.mkdir(exist_ok=True)
    save_path = save_dir / "garam_brain_elite.pth"
    torch.save(brain.state_dict(), save_path)
    
    print(f"\n[SUCCESS] Elite Brain saved to: {save_path}")
    print(f"           Size: {save_path.stat().st_size / 1024:.1f} KB")

if __name__ == "__main__":
    save_brain()
