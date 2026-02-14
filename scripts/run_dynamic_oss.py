
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import torch

# Setup Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

# Imports
from core.active_config.tactical_genome import dna
from scripts.neural_brain import GaramNeuralBrain

class DynamicOSSSimulator:
    def __init__(self):
        self.capital = 100_000_000
        self.position = 0
        self.avg_price = 0
        self.equity_curve = []
        self.param_history = [] # Log of dynamic params
        
        # Initialize AI Brain
        self.brain = GaramNeuralBrain(input_size=5, mode="CUSTOM_45")
        
        # Base DNA (Starting Point)
        self.base_threshold = 8.0
        self.base_stop = 0.05

    def get_ai_dynamic_params(self, features):
        """
        [CORE LOGIC]
        OSS Intervenes HERE.
        Input: Market Features (Volatility, Trend, etc.)
        Output: Optimal Threshold & Stop for THIS MOMENT.
        """
        # Convert to tensor
        inp = torch.tensor(features, dtype=torch.float32).unsqueeze(0).to(self.brain.device)
        
        # Inference
        self.brain.eval()
        with torch.no_grad():
            out = self.brain.net(inp).cpu().numpy()[0]
            
        # Interpret Output (-1 ~ 1 usually, assuming standardized weights or using sigmoid)
        # We simulate scaling since model is untrained random weights
        # Map: Out[0] -> Threshold Adjustment (-1.0 ~ +1.0)
        # Map: Out[1] -> Stop Adjustment (-0.02 ~ +0.02)
        
        # Sigmoid to bound 0~1
        adj_1 = 1 / (1 + np.exp(-out[0])) # 0~1
        adj_2 = 1 / (1 + np.exp(-out[1])) # 0~1
        
        # Dynamic Calculation
        # Threshold: 7.0 ~ 8.5
        dyn_threshold = 7.0 + (adj_1 * 1.5)
        
        # Stop: 3% ~ 10%
        # If High Volatility (Feature[2]), maybe wider stop? AI learns this.
        dyn_stop = 0.03 + (adj_2 * 0.07)
        
        return dyn_threshold, dyn_stop

    def run_simulation(self, df):
        print("\n=== [OSS DYNAMIC INTERVENTION] Real-time Golden Ratio Hunt ===")
        print(f"Target: June 2025 ~ Feb 2026 ({len(df)} bars)")
        
        # Pre-calc features for speed
        df['ret'] = df['close'].pct_change()
        df['vol'] = df['ret'].rolling(20).std()
        df['ma5'] = df['close'].rolling(5).mean()
        df['ma20'] = df['close'].rolling(20).mean()
        df['trend'] = (df['ma5'] - df['ma20']) / df['ma20']
        
        # Feature Vectors (Normalized roughly)
        # [Close, Vol, Trend, Volume, RSI-proxy]
        feature_matrix = np.column_stack([
            df['close'].values, 
            df['vol'].fillna(0).values * 100, 
            df['trend'].fillna(0).values * 100,
            np.log(df['volume'].replace(0, 1)).values,
            np.zeros(len(df)) # placeholder
        ])
        
        # Normalize
        feature_matrix = (feature_matrix - np.mean(feature_matrix, axis=0)) / (np.std(feature_matrix, axis=0) + 1e-5)
        
        print("[AI] Engine Running... (Adapting to each minute)")
        
        entry_price = 0
        highest_price = 0
        
        for i, row in enumerate(df.itertuples()):
            if i < 20: continue # Warmup
            
            # 1. OSS INTERVENTION (Every Minute)
            # Ask Brain: "What is the Golden Ratio for NOW?"
            current_feats = feature_matrix[i]
            opt_th, opt_stop = self.get_ai_dynamic_params(current_feats)
            
            self.param_history.append({'time': row.time, 'th': opt_th, 'stop': opt_stop})
            
            price = row.close
            score = row.oss_score
            
            # 2. Execution Logic using DYNAMIC Params
            
            # ENTRY?
            if self.position == 0:
                # Use the AI-determined threshold for this specific moment
                if score > opt_th:
                    self.position = int(self.capital / (price * 1.0005))
                    self.capital -= self.position * (price * 1.0005)
                    entry_price = price
                    highest_price = price
                    # print(f"  [BUY] {row.time} | Score {score:.1f} > AI_Th {opt_th:.1f}")

            # EXIT?
            elif self.position > 0:
                highest_price = max(highest_price, price)
                # Use the AI-determined Stop width for this specific moment
                stop_price = highest_price * (1 - opt_stop)
                
                if price < stop_price:
                    rev = self.position * (price * 0.9995) * 0.9977 # Tax/Fee
                    self.capital += rev
                    self.position = 0
                    # print(f"  [SELL] {row.time} | AI_Stop {opt_stop*100:.1f}% Triggered")

            # Equity
            eq = self.capital
            if self.position > 0:
                eq += self.position * price - (self.position * entry_price) # simple floating
            self.equity_curve.append({'time': row.time, 'equity': eq})

        # Report
        final_eq = self.equity_curve[-1]['equity']
        ret = ((final_eq / 100_000_000) - 1) * 100
        
        print("\n" + "="*50)
        print(" [DYNAMIC OSS REPORT]")
        print("="*50)
        print(f"Final Equity : {final_eq:,.0f} KRW")
        print(f"Total Return : {ret:+.2f}%")
        
        # Analyze Adaptation
        ths = [p['th'] for p in self.param_history]
        stops = [p['stop'] for p in self.param_history]
        
        print("\n[OSS ADAPTATION STATS]")
        print(f"Threshold : Avg {np.mean(ths):.2f} (Min {np.min(ths):.2f} ~ Max {np.max(ths):.2f})")
        print(f"Stop Loss : Avg {np.mean(stops)*100:.1f}% (Min {np.min(stops)*100:.1f}% ~ Max {np.max(stops)*100:.1f}%)")
        print("-" * 50)
        
        # Plot
        param_df = pd.DataFrame(self.param_history)
        fig, ax1 = plt.subplots(figsize=(12, 8))
        
        ax1.plot(df['time'].iloc[20:], [e['equity'] for e in self.equity_curve], 'g-', label='Equity')
        ax1.set_ylabel('Equity (KRW)', color='g')
        
        ax2 = ax1.twinx()
        ax2.plot(param_df['time'], param_df['th'], 'b--', alpha=0.3, label='AI Threshold')
        ax2.set_ylabel('Threshold', color='b')
        
        plt.title('Dynamic OSS Adaptation: Equity vs AI Threshold')
        plt.savefig(PROJECT_ROOT / "reports/dynamic_oss_result.png")
        print("[GRAPH] Saved dynamic visualization.")

def load_data_long_term(symbol="005930"):
    # Re-use loading logic
    path = PROJECT_ROOT / f"GARAM_Data/history/minute/{symbol}.csv"
    if not path.exists(): return pd.DataFrame() 
    df = pd.read_csv(path)
    df.columns = [c.lower() for c in df.columns]
    if 'date' in df.columns: df['time'] = pd.to_datetime(df['date'].astype(str), errors='coerce')
    else: df['time'] = df.index
    df = df.dropna(subset=['time'])
    mask = (df['time'] >= "2025-06-01") & (df['time'] <= "2026-02-06")
    df = df.loc[mask].sort_values('time').reset_index(drop=True)
    
    # Simple Signals
    df['ma5'] = df['close'].rolling(5).mean()
    df['ma20'] = df['close'].rolling(20).mean()
    df['oss_score'] = np.where(df['ma5']>df['ma20'], 8.0, 2.0) # Base signal to be filtered by AI Threshold
    
    return df

if __name__ == "__main__":
    df = load_data_long_term()
    if not df.empty:
        sim = DynamicOSSSimulator()
        sim.run_simulation(df)
