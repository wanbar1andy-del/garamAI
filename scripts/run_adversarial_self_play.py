
import sys
import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from pathlib import Path
from tqdm import tqdm
import time
import random

# Setup Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))
from scripts.neural_brain import GaramNeuralBrain

class AdversarialGym:
    def __init__(self):
        # 50% Load
        self.brain = GaramNeuralBrain(input_size=10, mode="MEDIUM")
        self.param_memory = []
        
        # Load Data once
        self.df = self.load_data()
        self.prepare_features()
        
    def load_data(self):
        symbol = "005930"
        path = PROJECT_ROOT / f"GARAM_Data/history/minute/{symbol}.csv"
        if not path.exists(): return pd.DataFrame() 
        df = pd.read_csv(path)
        df.columns = [c.lower() for c in df.columns]
        if 'date' in df.columns: df['time'] = pd.to_datetime(df['date'].astype(str), errors='coerce')
        else: df['time'] = df.index
        df = df.dropna(subset=['time'])
        mask = (df['time'] >= "2025-06-01") & (df['time'] <= "2026-02-06")
        df = df.loc[mask].sort_values('time').reset_index(drop=True)
        return df

    def prepare_features(self):
        df = self.df
        df['ret'] = df['close'].pct_change()
        df['vol'] = df['ret'].rolling(20).std()
        
        # 10 Features (Context)
        f1 = (df['vol'] / df['vol'].rolling(100).mean()).fillna(0).values 
        f2 = ((df['close'].rolling(5).mean() - df['close'].rolling(60).mean())/df['close'].rolling(60).mean()).fillna(0).values * 100
        f3 = (df['volume'] / df['volume'].rolling(20).mean()).fillna(0).values
        f4 = ((df['close'] - df['close'].rolling(20).mean()) / df['close'].rolling(20).mean()).fillna(0).values * 100
        f5 = df['close'].pct_change(5).fillna(0).values * 100
        
        # Random noise features to test AI robustness initially
        f_dummy = np.random.randn(len(df), 5)
        
        self.features = np.column_stack([f1, f2, f3, f4, f5, f_dummy])
        self.features = (self.features - np.mean(self.features, axis=0)) / (np.std(self.features, axis=0) + 1e-5)

    def agent_pose_question(self, current_stats):
        """
        AGENT (Me) analyzes the gap and asks OSS to try a new strategy.
        """
        acc = current_stats.get('accuracy', 0)
        trades = current_stats.get('trades', 0)
        
        # Strategy Logic
        if trades < 10:
            query = "TRADES_TOO_LOW"
            suggestion = {"threshold_bias": -0.1, "epochs": 20} # Lower bar
        elif acc < 0.5:
            query = "ACCURACY_LOW"
            suggestion = {"threshold_bias": 0.1, "epochs": 30} # Raise bar, train more
        else:
            query = "OPTIMIZE_YIELD"
            suggestion = {"threshold_bias": 0.0, "epochs": 15} # Fine tune
            
        print(f"\n[AGENT] Question: Trade count is {trades} and Accuracy is {acc*100:.1f}%.")
        print(f"        Action: I suspect we are too rigid. Adjusting Threshold Bias by {suggestion['threshold_bias']}.")
        
        return suggestion

    def oss_predict_and_train(self, suggestion):
        """
        OSS (Brain) inputs the suggestion, trains to close the gap.
        """
        print(f"[OSS]   Answer: Accepted. Re-training with bias {suggestion['threshold_bias']} for {suggestion['epochs']} epochs...")
        
        # Generate new Labels based on bias
        # Bias < 0 means we label MORE marginal trades as 'Good' (Lowering standard)
        # Bias > 0 means we label ONLY super-elite trades (Raising standard)
        
        bias = suggestion['threshold_bias']
        closes = self.df['close'].values
        lookahead = 60
        full_X, full_y = [], []
        
        # Dynamic Target for this round
        TARGET = 0.03 + bias # e.g., 2% if bias is -0.01 (Wait... Bias should reduce threshold, not ROI target? Let's say ROI target)
        
        # If we want more trades, we lower the ROI requirement for labeling
        current_target_roi = max(0.01, 0.03 + bias/5) 
        
        print(f"[OSS]   Self-Reflection: Redefining 'Success' as ROI > {current_target_roi*100:.1f}% to learn new patterns.")
        
        # Fast Labeling
        # We perform labeling on subset or full
        # For speed in loop, we use full but simple logic
        
        for i in range(0, len(self.df)-lookahead, 5): # Stride 5 for speed
            curr = closes[i]
            future = closes[i+1:i+lookahead]
            mx = np.max(future)
            mn = np.min(future)
            ret = (mx - curr)/curr
            dd = (curr - mn)/curr
            
            if ret > current_target_roi and dd < 0.03:
                full_X.append(self.features[i])
                full_y.append([1.0, 0.0]) # Hero
            else:
                full_X.append(self.features[i])
                full_y.append([0.0, 0.0]) # Dud
                
        # Oversample
        tx = [x for i,x in enumerate(full_X) if full_y[i][0] == 1.0]
        ty = [y for y in full_y if y[0] == 1.0]
        if len(tx) > 0:
            rep = int(len(full_X)/len(tx)) // 2
            full_X.extend(tx * rep)
            full_y.extend(ty * rep)
            
        # Train
        X_t = torch.tensor(np.array(full_X), dtype=torch.float32).to(self.brain.device)
        y_t = torch.tensor(np.array(full_y), dtype=torch.float32).to(self.brain.device)
        
        self.brain.train()
        opt = optim.Adam(self.brain.parameters(), lr=0.0005)
        crit = nn.MSELoss()
        
        for ep in range(suggestion['epochs']):
            # Batch Training
            opt.zero_grad()
            # Random subset for stochasticity
            idx = torch.randperm(len(X_t))[:20000]
            out = self.brain.net(X_t[idx])
            loss = crit(out, y_t[idx])
            loss.backward()
            opt.step()
            
        print(f"[OSS]   Training Done. Loss: {loss.item():.4f}")

    def execution_test(self):
        """
        Run validaton
        """
        print("[TEST]  Running Verification Backtest...")
        self.brain.eval()
        with torch.no_grad():
            inp = torch.tensor(self.features, dtype=torch.float32).to(self.brain.device)
            preds = self.brain.net(inp).cpu().numpy()
            
        capital = 100_000_000
        trades = 0
        wins = 0
        
        for i, row in enumerate(self.df.itertuples()):
            if i >= len(preds): break
            prob = preds[i][0]
            
            if prob > 0.85: # Confidence
                 # Trade Sim
                 entry = row.close * 1.0005
                 if i + 60 >= len(self.df): break
                 future = self.df['close'].values[i+1:i+61]
                 mx = np.max(future)
                 mn = np.min(future)
                 
                 trades += 1
                 if mn < entry * 0.94: # Stop
                     capital *= 0.94
                 else:
                     ret = (mx - entry)/entry
                     if ret > 0.03: wins += 1
                     capital *= (1 + max(-0.05, ret - 0.003)) # PnL
                     
        acc = wins/trades if trades > 0 else 0
        stats = {
            'trades': trades,
            'accuracy': acc,
            'equity': capital,
            'return': (capital/100_000_000 - 1)*100
        }
        print(f"[RESULT] Trades: {trades} | Accuracy: {acc*100:.1f}% | Return: {stats['return']:.2f}%")
        return stats

    def run_loop(self, duration_sec=1800):
        print(f"=== [ADVERSARIAL SELF-PLAY] Start ({duration_sec}s) ===")
        start_time = time.time()
        
        history_stats = {'trades': 0, 'accuracy': 0}
        
        round_n = 1
        while time.time() - start_time < duration_sec:
            print(f"\n--- Round {round_n} ---")
            
            # 1. Agent asks
            sugg = self.agent_pose_question(history_stats)
            
            # 2. OSS answers & trains
            self.oss_predict_and_train(sugg)
            
            # 3. Test
            history_stats = self.execution_test()
            
            # 4. Feedback
            gap = 5.31 - history_stats['return'] # Base baseline +5.31
            print(f"[FEEDBACK] Gap from baseline: {gap:.2f}%")
            
            round_n += 1
            if history_stats['return'] > 10.0 and history_stats['trades'] > 50:
                print("!!! BREAKTHROUGH ACHIEVED !!!")
                # Don't stop, optimize further
                
            time.sleep(1) # Breath

if __name__ == "__main__":
    gym = AdversarialGym()
    gym.run_loop(duration_sec=300) # Run for 5 minutes (demo) then can extend
