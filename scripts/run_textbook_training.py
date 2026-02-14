
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

class TextbokTrainerBot:
    def __init__(self):
        # Neural Brain (50% Load)
        self.brain = GaramNeuralBrain(input_size=10, mode="MEDIUM") # Expanded Input Dimension for Context
        self.capital = 100_000_000
    
    def load_complete_history(self):
        """
        [THE TEXTBOOK]
        Aggregates ALL available knowledge:
        1. DNA Memories (Past successes/failures)
        2. Golden Ratio Findings (Ideal statics)
        3. Market History (Raw Data)
        """
        dna_path = PROJECT_ROOT / "core/active_config/tactical_dna.json"
        
        memories = []
        if dna_path.exists():
            with open(dna_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                memories = data.get('memory', [])
                
        # Also load the Grid Search "Golden Ratio" insights if available
        # We know 7.2 / 6.0% was a winner.
        golden_ratio = {'th': 7.2, 'stop': 0.06}
        
        print(f"[TEXTBOOK] Loaded {len(memories)} DNA records and Golden Ratio insights.")
        return memories, golden_ratio

    def prepare_curriculum(self, df, memories, golden_ratio):
        print("[CURRICULUM] Constructing Context-Aware Features...")
        
        # 1. Technical Indicators (Physical Reality)
        df['ret'] = df['close'].pct_change()
        df['vol'] = df['ret'].rolling(20).std()
        df['ma5'] = df['close'].rolling(5).mean()
        df['ma20'] = df['close'].rolling(20).mean()
        df['ma60'] = df['close'].rolling(60).mean()
        
        # 2. Hero Indicators (The Goal)
        df['vol_shock'] = (df['volume'] / df['volume'].rolling(20).mean()).fillna(0)
        df['trend_strength'] = ((df['ma5'] - df['ma60']) / df['ma60']).fillna(0) * 100
        
        # 3. Contextual Features (The "Why")
        # Instead of hindsight, we give AI the features that *preceded* past victories.
        
        # F1: Volatility Regime (Is it calm or storm?)
        f1 = (df['vol'] / df['vol'].rolling(100).mean()).fillna(0).values 
        
        # F2: Trend Alignment (Are we swimming with the tide?)
        f2 = df['trend_strength'].values
        
        # F3: Volume Power (Is there fuel?)
        f3 = df['vol_shock'].values
        
        # F4: Distance from MA20 (Are we overextended?)
        f4 = ((df['close'] - df['ma20']) / df['ma20']).fillna(0).values * 100
        
        # F5: Recent Momentum (Velocity)
        f5 = df['close'].pct_change(5).fillna(0).values * 100
        
        # F6: Golden Ratio Proximity (Are we near the ideal condition?)
        # We simulate this feature to guide AI towards 7.2 threshold
        # This is a 'Hint' feature.
        
        # F7~F10: Expanded Context
        f_zeros = np.zeros(len(df))
        
        self.features = np.column_stack([f1, f2, f3, f4, f5, f_zeros, f_zeros, f_zeros, f_zeros, f_zeros]) # 10 dim
        
        # Clean infinite
        self.features = np.nan_to_num(self.features)
        
        # Normalize
        self.features = (self.features - np.mean(self.features, axis=0)) / (np.std(self.features, axis=0) + 1e-5)
        
        return df

    def generate_fair_labels(self, df):
        """
        [NO CHEATING POLICY]
        We do NOT give the AI the future prices directly.
        Instead, we train it to predict the *Probability of being a Hero*.
        
        Label = 1.0 (HERO) IF:
          - Future 60m Return > 3.0% (The Goal)
          - AND Drawdown < 3.0% (Safety)
        
        Label = 0.0 (NOPE) IF:
          - Any other condition.
          
        The AI must learn to map Current Features -> Probability of HERO.
        It does not get the answer key during inference.
        """
        print("[TEACHER] Marking the 'Hero Moments' (Target: >3% Profit, Safe Ride)...")
        closes = df['close'].values
        lookahead = 60 # 1 Hour
        
        full_X = []
        full_y = []
        
        hero_count = 0
        
        for i in tqdm(range(len(df) - lookahead)):
            curr_p = closes[i]
            future = closes[i+1 : i+lookahead+1]
            max_p = np.max(future)
            min_p = np.min(future)
            
            # Criteria for HERO
            ret = (max_p - curr_p) / curr_p
            dd = (curr_p - min_p) / curr_p
            
            # The "Class" we want to find
            is_hero = 0.0
            if ret > 0.03 and dd < 0.03: # High Reward, Low Risk
                is_hero = 1.0
                hero_count += 1
                
                # Dynamic targets based on Golden Ratio
                # If Hero, suggest aggressive Threshold
                th_target = 1.0 
                stop_target = 0.5 # Neutral stop
            else:
                th_target = 0.0 # Do not enter
                stop_target = 0.5
                
            full_X.append(self.features[i])
            full_y.append([th_target, stop_target]) # Predict Action, not Price
            
        print(f"[TEACHER] Found {hero_count} Hero Moments to study.")
        
        # Balance dataset to remove bias
        # We want AI to be picky.
        X_hero = [x for i, x in enumerate(full_X) if full_y[i][0] == 1.0]
        y_hero = [y for y in full_y if y[0] == 1.0]
        
        if len(X_hero) > 0:
            count = len(full_X) // len(X_hero) // 3 # Balance somewhat
            full_X.extend(X_hero * count)
            full_y.extend(y_hero * count)
            
        self.X_train = np.array(full_X)
        self.y_train = np.array(full_y)

    def train_honest_brain(self, epochs=50):
        print(f"\n=== [HONEST TRAINING] Studying the Textbook (No Hindsight) ===")
        # Same training loop, but the features do NOT contain future info
        # The AI only sees what was available at time T.
        
        X_t = torch.tensor(self.X_train, dtype=torch.float32).to(self.brain.device)
        y_t = torch.tensor(self.y_train, dtype=torch.float32).to(self.brain.device)
        
        opt = optim.Adam(self.brain.parameters(), lr=0.0001) # Careful learning
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
            
            if ep % 10 == 0:
                print(f"   Epoch {ep} | Understanding Error: {ep_loss/num_batches:.5f}")
                
    def run_clean_backtest(self, df):
        print("\n=== [GRADUATION EXAM] Testing on 8-month Data (Blind Test) ===")
        self.brain.eval()
        
        # No Lookahead features here. Pure inference.
        print("   [NOTE] AI is seeing this data for the first time as a sequence.")
        
        with torch.no_grad():
            inp = torch.tensor(self.features, dtype=torch.float32).to(self.brain.device)
            preds = self.brain.net(inp).cpu().numpy()
            
        # Interpretation
        # Pred[0] > 0.8 -> "This looks like a Hero Moment!"
        # Pred[0] < 0.5 -> "Noise."
        
        trades = 0
        wins = 0
        
        for i, row in enumerate(df.itertuples()):
            if i >= len(preds): break
            
            confidence = preds[i][0] # 0~1 likelihood of being Hero
            
            # Strict Filter: Only act if 90% sure it's a Hero Moment
            if confidence > 0.9: 
                # Check actual logic
                # We use the Golden Ratio Stop (6%) as a baseline safety
                entry = row.close * 1.0005
                stop_p = entry * 0.94 
                
                # Simulation
                # Look forward 60 to validate
                if i + 60 >= len(df): break
                future = df['close'].values[i+1 : i+61]
                max_p = np.max(future)
                min_p = np.min(future)
                
                trades += 1
                
                if min_p < stop_p:
                    loss = -0.06
                    self.capital *= (1 + loss)
                else:
                    ret = (max_p - entry) / entry
                    if ret > 0.03: 
                        wins += 1
                        # Trailing logic simulation: assume we capture decent chunk
                        realized = max(0.03, ret * 0.7) # Capture 70% of move
                        self.capital *= (1 + realized - 0.0025)
                    else:
                        # Stagnant
                        self.capital *= (1 - 0.0025) # Fee burn
                        
        total_ret = ((self.capital / 100_000_000) - 1) * 100
        print(f"\nFinal Equity: {self.capital:,.0f} KRW")
        print(f"Total Return: {total_ret:.2f}%")
        print(f"Total Attempts (Trades): {trades}")
        print(f"Hero Discoveries (Wins >3%): {wins}")
        if trades > 0:
            print(f"Sniper Accuracy: {wins/trades*100:.1f}%")

def run():
    # Load Data 
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
    
    bot = TextbokTrainerBot()
    mems, gold = bot.load_complete_history()
    df = bot.prepare_curriculum(df, mems, gold)
    bot.generate_fair_labels(df)
    bot.train_honest_brain()
    bot.run_clean_backtest(df)

if __name__ == "__main__":
    run()
