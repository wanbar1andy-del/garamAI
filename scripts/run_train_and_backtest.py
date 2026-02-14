
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

# Import Brain
from scripts.neural_brain import GaramNeuralBrain

class DeepEvolutionBot:
    def __init__(self):
        # 50% Load Approved
        self.brain = GaramNeuralBrain(input_size=5, mode="MEDIUM")
        self.capital = 100_000_000
        self.equity_curve = []
        
        # Training Data
        self.X_train = []
        self.y_train = []

    def prepare_data(self, df):
        print("[DATA] Preparing Enriched Features (Cost-Aware)...")
        df['ret'] = df['close'].pct_change()
        df['vol'] = df['ret'].rolling(20).std()
        df['ma5'] = df['close'].rolling(5).mean()
        df['ma20'] = df['close'].rolling(20).mean()
        df['trend'] = (df['ma5'] - df['ma20']) / df['ma20']
        
        # Enriched Feature Matrix
        f1 = df['vol'].fillna(0).values * 100
        f2 = df['trend'].fillna(0).values * 100
        f3 = df['close'].pct_change(5).fillna(0).values * 100
        # Volume Shock
        f4 = (df['volume'] / df['volume'].rolling(20).mean()).fillna(0).values
        # Volatility Regime
        f5 = (df['vol'] / df['vol'].rolling(60).mean()).fillna(0).values 
        
        self.features = np.column_stack([f1, f2, f3, f4, f5])
        
        # Normalize
        self.features = (self.features - np.mean(self.features, axis=0)) / (np.std(self.features, axis=0) + 1e-5)
        return df

    def generate_training_labels(self, df):
        """
        [COST-AWARE TEACHER]
        Only label as 'BUY' if:
        (Potential Gain) - (Transaction Cost 0.3%) > Minimum Margin (0.5%)
        Otherwise, teach AI to stay passsive (High Threshold).
        """
        print("[AI TRAINING] Generating Labels with Cost Reality (Fee 0.3% + Margin 0.5%)...")
        closes = df['close'].values
        
        lookahead = 60
        full_X = []
        full_y = []
        
        COST_RATE = 0.003 # 0.3% (Tax + Fee + Slippage)
        MIN_MARGIN = 0.005 # 0.5% Net Profit required
        
        for i in tqdm(range(len(df) - lookahead)):
            curr_price = closes[i]
            future_prices = closes[i+1 : i+lookahead+1]
            max_p = np.max(future_prices)
            min_p = np.min(future_prices)
            
            # Theoretical Gross Return
            gross_ret = (max_p - curr_price) / curr_price
            max_drawdown = (curr_price - min_p) / curr_price
            
            # Net Return logic
            net_ret = gross_ret - COST_RATE
            
            # DECISION LOGIC
            if net_ret > MIN_MARGIN and max_drawdown < 0.02:
                # GOOD TRADE: It covers cost and gives margin.
                # Teach: Low Threshold (Aggressive), Proper Stop
                target_th_adj = 1.0 # -> Will map to 7.0 (Buy)
                
                # Stop should be tight but survive the drawdown
                ideal_stop = max(0.04, max_drawdown * 1.5)
                # Map 0.03~0.10 -> 0~1
                target_stop_norm = (ideal_stop - 0.03) / 0.07
                
            else:
                # BAD TRADE: Fee eater or dangerous.
                # Teach: Max Threshold (Do NOT Buy)
                target_th_adj = 0.0 # -> Will map to 8.5+ (Pass)
                target_stop_norm = 0.5 # Irrelevant, but keep neutral
            
            full_X.append(self.features[i])
            full_y.append([target_th_adj, target_stop_norm])
            
        self.X_train = np.array(full_X)
        self.y_train = np.array(full_y)
        
        # Balance the dataset? 
        # No, let it learn that mostly it should NOT trade.
        print(f"[AI] Generated {len(self.X_train)} samples.")


    def train_brain(self, epochs=50):
        print("\n=== [AI LEARNING] Deep Training on RTX 3060 (50% Load) ===")
        
        # Convert to Tensors
        X_t = torch.tensor(self.X_train, dtype=torch.float32).to(self.brain.device)
        y_t = torch.tensor(self.y_train, dtype=torch.float32).to(self.brain.device)
        
        optimizer = optim.AdamW(self.brain.parameters(), lr=0.001)
        criterion = nn.MSELoss()
        
        # Custom "MEDIUM" Batch Size from neural_brain.py definition is 22000
        # We process in chunks
        batch_size = 22000 
        num_batches = len(X_t) // batch_size + 1
        
        self.brain.train()
        
        import time
        start_t = time.time()
        
        for epoch in range(epochs):
            total_loss = 0
            
            # Shuffle
            perm = torch.randperm(len(X_t))
            X_s = X_t[perm]
            y_s = y_t[perm]
            
            for i in range(num_batches):
                start = i * batch_size
                end = start + batch_size
                if start >= len(X_t): break
                
                runs_X = X_s[start:end]
                runs_y = y_s[start:end]
                
                optimizer.zero_grad()
                out = self.brain.net(runs_X)
                loss = criterion(out, runs_y)
                loss.backward()
                optimizer.step()
                total_loss += loss.item()
                
            if epoch % 10 == 0:
                print(f"   Epoch {epoch}/{epochs} | Loss: {total_loss/num_batches:.5f}")
                
        print(f"[AI] Training Complete ({time.time() - start_t:.1f}s). Brain is ready.")

    def run_backtest(self, df):
        print("\n=== [INTELLIGENT BACKTEST] Using Trained Brain ===")
        
        self.brain.eval()
        
        # Inference all at once for speed
        with torch.no_grad():
            feat_t = torch.tensor(self.features, dtype=torch.float32).to(self.brain.device)
            preds = self.brain.net(feat_t).cpu().numpy()
            
        # Denormalize Predictions
        # Pred[0] (0~1) -> Threshold (8.5 ~ 7.0) 
        #   1.0 (Mobile) -> 7.0
        #   0.0 (Safe)   -> 8.5
        thresh_preds = 8.5 - (preds[:, 0] * 1.5)
        
        # Pred[1] (0~1) -> Stop (3% ~ 10%)
        stop_preds = 0.03 + (preds[:, 1] * 0.07)
        
        # Execute
        pos = 0
        entry_p = 0
        highest_p = 0
        
        for i, row in enumerate(df.itertuples()):
            if i >= len(thresh_preds): break
            
            th = thresh_preds[i]
            stop = stop_preds[i]
            
            # Use raw 8.0 score as base, but Threshold dictates entry
            # In simulation, we need real score.
            # Let's assume OSS Score logic from previous signal injection
            score = row.oss_score
            
            if pos == 0:
                if score > th:
                    pos = int(self.capital / (row.close * 1.0005))
                    cost = pos * (row.close * 1.0005)
                    self.capital -= cost
                    entry_p = row.close
                    highest_p = row.close
            elif pos > 0:
                highest_p = max(highest_p, row.close)
                stop_p = highest_p * (1 - stop)
                
                if row.close < stop_p:
                    rev = pos * (row.close * 0.9995) * 0.9977
                    self.capital += rev
                    pos = 0
            
            eq = self.capital
            if pos > 0: eq += pos * row.close - (pos * entry_p)
            self.equity_curve.append(eq)
            
        # Report
        final_eq = self.equity_curve[-1]
        ret = ((final_eq / 100_000_000) - 1) * 100
        
        print("\n" + "="*50)
        print(" [DEEP EVOLUTION RESULT]")
        print("="*50)
        print(f"Final Equity : {final_eq:,.0f} KRW")
        print(f"Total Return : {ret:+.2f}%")
        print("-" * 50)


def run_process():
    # Load Data (June ~ Feb)
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
    
    # Inject Signal
    df['ma5'] = df['close'].rolling(5).mean()
    df['ma20'] = df['close'].rolling(20).mean()
    cond = (df['ma5'] > df['ma20'])
    df['oss_score'] = 0.0
    df.loc[cond, 'oss_score'] = 8.0 # Base
    
    bot = DeepEvolutionBot()
    
    # 1. Feature Engineering
    df = bot.prepare_data(df)
    
    # 2. Generate 'Answer Key' (Labels)
    bot.generate_training_labels(df)
    
    # 3. Train the Brain
    bot.train_brain(epochs=50) # Intense training
    
    # 4. Prove it
    bot.run_backtest(df)

if __name__ == "__main__":
    run_process()
