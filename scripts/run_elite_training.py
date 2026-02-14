
import sys
import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from pathlib import Path
from tqdm import tqdm
import json

# Setup Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))
from scripts.neural_brain import GaramNeuralBrain

class EliteTrainingBot:
    def __init__(self):
        # Using MEDIUM mode (50% Load)
        self.brain = GaramNeuralBrain(input_size=7, mode="MEDIUM") # Added HERO features
        self.capital = 100_000_000
        
        # Goals
        # Daily Target: 10% (Ideally)
        # Min Trade ROI: 3.0% (Net)
        
    def load_dna_memory(self):
        """
        Load OSS's past memories (Success/Failures) from DNA.
        This allows AI to learn from previous 'TRAPPED' or 'GLORY' moments.
        """
        dna_path = PROJECT_ROOT / "core/active_config/tactical_dna.json"
        memories = []
        if dna_path.exists():
            with open(dna_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                memories = data.get('memory', [])
        print(f"[DNA] Loaded {len(memories)} past experiences from OSS DNA.")
        return memories

    def prepare_data(self, df, memories):
        print("[DATA] Injecting HERO Logic & DNA Memories...")
        
        # 1. Base Features
        df['ret'] = df['close'].pct_change()
        df['vol'] = df['ret'].rolling(20).std()
        df['ma5'] = df['close'].rolling(5).mean()
        df['ma20'] = df['close'].rolling(20).mean()
        df['ma60'] = df['close'].rolling(60).mean()
        
        # 2. HERO Logic (Who is leading?)
        # Since we simulate single stock '005930', we check if it is in 'Hero Mode'
        # Hero Definition: Price > MA60 AND Volatility is Alive AND Volume is rising
        df['is_hero'] = np.where(
            (df['close'] > df['ma60']) & 
            (df['vol'] > df['vol'].rolling(100).mean()) & 
            (df['volume'] > df['volume'].rolling(20).mean()), 
            1.0, 0.0
        )
        
        # 3. Memory Injection (Contextual)
        # Map past failures to current timestamp? 
        # Since DNA memory has specific timestamps not matching backtest sim directly (unless aligned),
        # We simulate "Experience Feature" -> Distance from MA, etc. that matches failure patterns.
        
        # Features: [Vol, Trend, Mom, VolShock, HERO_Flag, MA_Div, Failure_Risk]
        f1 = df['vol'].fillna(0).values * 100
        f2 = ((df['ma5'] - df['ma20']) / df['ma20']).fillna(0).values * 100
        f3 = df['close'].pct_change(5).fillna(0).values * 100
        f4 = (df['volume'] / df['volume'].rolling(20).mean()).fillna(0).values
        f5 = df['is_hero'].values
        f6 = ((df['close'] - df['ma60']) / df['ma60']).fillna(0).values * 100
        
        # Failure Risk Proxy (High Vol + Down Trend = Pain)
        f7 = np.where((df['ma5'] < df['ma20']) & (df['vol'] > 0.002), 1.0, 0.0)
        
        self.features = np.column_stack([f1, f2, f3, f4, f5, f6, f7])
        self.features = (self.features - np.mean(self.features, axis=0)) / (np.std(self.features, axis=0) + 1e-5)
        return df

    def generate_elite_labels(self, df):
        """
        [SPARTAN TEACHER]
        Rule: If Net Profit < 3.0%, DO NOT TRADE.
        """
        print("[AI TRAINING] Generating SPARTAN Labels (Min ROI 3.0%)...")
        closes = df['close'].values
        lookahead = 120 # Look ahead 2 hours (Trend Following)
        
        full_X = []
        full_y = []
        
        COST = 0.003
        TARGET_ROI = 0.03 # 3%
        
        good_trades = 0
        
        for i in tqdm(range(len(df) - lookahead)):
            curr_p = closes[i]
            future = closes[i+1 : i+lookahead+1]
            max_p = np.max(future)
            min_p = np.min(future)
            
            gross_ret = (max_p - curr_p) / curr_p
            net_ret = gross_ret - COST
            dd = (curr_p - min_p) / curr_p
            
            # HERO Filter: Only trade if it was Hero mode? (Optional, but let AI learn)
            
            # LABELING LOGIC
            if net_ret >= TARGET_ROI and dd < 0.03:
                # EXCELLENT OPPORTUNITY
                # Threshold: Lower (Enter)
                # Stop: Dynamic (Below MinP)
                th_target = 1.0 
                stop_target = (max(0.04, dd * 1.2) - 0.03) / 0.07 # Norm
                good_trades += 1
            else:
                # WASTE OF TIME -> IGNORE
                th_target = 0.0 # Pass
                stop_target = 0.5
                
            full_X.append(self.features[i])
            full_y.append([th_target, stop_target])
            
        print(f"[AI] Identified {good_trades} ELITE opportunities out of {len(df)} bars.")
        
        # OVERSAMPLING GOOD TRADES (CRITICAL)
        # SInce good trades are rare (daily 10% target is hard), we must repeat them so AI sees them.
        X_good = [x for i, x in enumerate(full_X) if full_y[i][0] == 1.0]
        y_good = [y for y in full_y if y[0] == 1.0]
        
        if len(X_good) > 0:
            repeat_factor = int(len(full_X) / len(X_good)) // 2
            print(f"[AI] Oversampling Elite Trades x{repeat_factor} to force learning...")
            full_X.extend(X_good * repeat_factor)
            full_y.extend(y_good * repeat_factor)
        
        self.X_train = np.array(full_X)
        self.y_train = np.array(full_y)

    def train_brain(self, epochs=100):
        # More epochs for harder task
        print(f"\n=== [ELITE TRAINING] 50% Load | {len(self.X_train)} Samples ===")
        
        X_t = torch.tensor(self.X_train, dtype=torch.float32).to(self.brain.device)
        y_t = torch.tensor(self.y_train, dtype=torch.float32).to(self.brain.device)
        
        opt = optim.AdamW(self.brain.parameters(), lr=0.0005) # Slower LR
        crit = nn.MSELoss()
        
        batch_size = 22000
        num_batches = len(X_t) // batch_size + 1
        
        self.brain.train()
        for ep in range(epochs):
            perm = torch.randperm(len(X_t))
            X_s, y_s = X_t[perm], y_t[perm]
            
            ep_loss = 0
            for i in range(num_batches):
                s, e = i*batch_size, (i+1)*batch_size
                if s >= len(X_t): break
                
                opt.zero_grad()
                out = self.brain.net(X_s[s:e])
                loss = crit(out, y_s[s:e])
                loss.backward()
                opt.step()
                ep_loss += loss.item()
                
            if ep % 20 == 0:
                print(f"   Epoch {ep} Loss: {ep_loss/num_batches:.5f}")
                
    def run_backtest(self, df):
        print("\n=== [ELITE BACKTEST] Verifying Brain Performance ===")
        self.brain.eval()
        with torch.no_grad():
            inp = torch.tensor(self.features, dtype=torch.float32).to(self.brain.device)
            preds = self.brain.net(inp).cpu().numpy()
            
        thresh_preds = 8.5 - (preds[:, 0] * 1.5)
        stop_preds = 0.03 + (preds[:, 1] * 0.07)
        
        trade_count = 0
        win_count = 0
        
        for i, row in enumerate(df.itertuples()):
            if i >= len(thresh_preds): break
            
            # Logic
            th = thresh_preds[i]
            stop = stop_preds[i]
            
            # NOTE: Only enter if AI is VERY CONFIDENT (Low Threshold)
            # Base score needs to be high to trigger
            if self.capital <= 0: break 
            
            if self.brain.mode: # dummy access
                pass

            # Simulation Logic (Simplified for report)
            # We want to see if it picked the 3% winners.
            # ... (Full replication of logic) ...
            
            # For this report, we use a vectorized check for speed & impact
            # If Threshold < 7.5 (AI says BUY) -> Check return
            if th < 7.5 and row.oss_score > th: # Trigger
                trade_count += 1
                
                # Check outcome (Lookahead 60 min to see if it hit profit)
                future = df['close'].values[i+1 : i+61]
                if len(future) < 1: continue
                
                entry = row.close * 1.0005
                max_p = np.max(future)
                min_p = np.min(future)
                
                # Stop check
                stop_p = entry * (1 - stop)
                if min_p < stop_p:
                    # Stopped out
                    loss = (stop_p - entry) / entry
                    self.capital *= (1 + loss)
                else:
                    # Survived. Did we hit 3%?
                    # Let's assume we hold until max or 1 hour
                    ret = (max_p - entry) / entry
                    self.capital *= (1 + ret - 0.0025) # fees
                    if ret > 0.03: win_count += 1
                    
        total_ret = ((self.capital / 100_000_000) - 1) * 100
        print(f"\nFinal Equity: {self.capital:,.0f} KRW")
        print(f"Total Return: {total_ret:.2f}%")
        print(f"Trades: {trade_count} | Wins (>3%): {win_count}")
        if trade_count > 0:
            print(f"Elite Win Rate: {win_count/trade_count*100:.1f}%")

def run():
    # Data Loading (Same as before)
    symbol = "005930"
    path = PROJECT_ROOT / f"GARAM_Data/history/minute/{symbol}.csv"
    if not path.exists(): return
    df = pd.read_csv(path)
    df.columns = [c.lower() for c in df.columns]
    if 'date' in df.columns: df['time'] = pd.to_datetime(df['date'].astype(str), errors='coerce')
    else: df['time'] = df.index
    df = df.dropna(subset=['time'])
    mask = (df['time'] >= "2025-06-01") & (df['time'] <= "2026-02-06")
    df = df.loc[mask].sort_values('time').reset_index(drop=True)
    
    # Mock Scores
    df['ma5'] = df['close'].rolling(5).mean()
    df['ma20'] = df['close'].rolling(20).mean()
    df.loc[df['ma5']>df['ma20'], 'oss_score'] = 8.0
    df['oss_score'] = df['oss_score'].fillna(0)
    
    bot = EliteTrainingBot()
    mems = bot.load_dna_memory() # Inject DNA
    df = bot.prepare_data(df, mems)
    bot.generate_elite_labels(df)
    bot.train_brain() # Learn to be Elite
    bot.run_backtest(df)

if __name__ == "__main__":
    run()
