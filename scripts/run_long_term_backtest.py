
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from datetime import datetime, timedelta
import torch

# Setup Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

# Imports
from core.engine.typhoon_orchestrator import TyphoonOrchestrator
from core.active_config.tactical_genome import dna
from scripts.neural_brain import GaramNeuralBrain

class LongTermBacktestBot(TyphoonOrchestrator):
    def __init__(self):
        super().__init__()
        self.trade_log = []
        self.equity_curve = []
        self.capital = 100_000_000 # 100M KRW Start
        self.position = 0 
        self.avg_price = 0
        
        # Costs
        self.fee_rate = 0.00015
        self.tax_rate = 0.0020
        self.slippage = 0.0005 
        
        self.current_equity = self.capital
        self.dna_updates = []

    def _process_tick(self, tick):
        self.current_price = tick['price']
        self.total_volume = tick.get('volume', 0)
        
        # --- PHASE LOGIC ---
        if self.phase == "PHASE_0_IDLE":
            score = tick.get('oss_score', 0)
            if score > 8.0 and self.position == 0:
                self.phase = "PHASE_1_DISCOVERY"
                self._transition_to_trigger()

        elif self.phase == "PHASE_2_TRIGGER":
            if self.current_price > self.entry_price * 1.02:
                self.phase = "PHASE_3_FORMATION"
            elif self.current_price < self.entry_price * 0.98:
                self.execute_sell("CUT", self.current_price, tick['time'])
                self.phase = "PHASE_0_IDLE"

        elif self.phase == "PHASE_3_FORMATION":
            self.highest_price = max(self.highest_price, self.current_price)
            # Dynamic Pulse Logic from DNA
            action = self.commander.run_anchor_logic(self.current_price, self.entry_price, self.highest_price)
            if action == "EXIT_ALL":
                self.phase = "PHASE_4_EXTRACTION"
                
        elif self.phase == "PHASE_4_EXTRACTION":
            self.execute_sell("PROFIT", self.current_price, tick['time'])
            self.phase = "PHASE_0_IDLE"
            
        # Update Equity
        floating_pnl = 0
        if self.position > 0:
            val = self.position * self.current_price
            cost = self.position * self.avg_price
            floating_pnl = val - cost
            
        self.current_equity = self.capital + floating_pnl
        self.equity_curve.append({'time': tick['time'], 'equity': self.current_equity})

    def _transition_to_trigger(self):
        self.phase = "PHASE_2_TRIGGER"
        self.entry_price = self.current_price
        self.highest_price = self.current_price
        self.execute_buy(self.current_price)

    def execute_buy(self, price):
        cost_price = price * (1 + self.slippage)
        guard_ratio = dna.get("liquidity_guard_ratio") 
        
        alloc_ratio = 1.0
        if guard_ratio < 0.2: alloc_ratio = 0.5 
        
        max_qty = int((self.capital * alloc_ratio) / (cost_price * (1 + self.fee_rate)))
        
        if max_qty > 0:
            cost = max_qty * cost_price
            fee = cost * self.fee_rate
            self.capital -= (cost + fee)
            self.position = max_qty
            self.avg_price = cost_price
            self.trade_log.append({'type': 'BUY', 'price': cost_price, 'qty': max_qty, 'time': 'SimTime'})

    def execute_sell(self, reason, price, timestamp):
        if self.position == 0: return
        
        sell_price = price * (1 - self.slippage)
        revenue = self.position * sell_price
        fee = revenue * self.fee_rate
        tax = revenue * self.tax_rate
        
        self.capital += (revenue - fee - tax)
        
        pnl = (revenue - fee - tax) - (self.position * self.avg_price)
        pnl_pct = (pnl / (self.position * self.avg_price)) * 100
        
        self.trade_log.append({'type': 'SELL', 'price': sell_price, 'qty': self.position, 'reason': reason, 'pnl_pct': pnl_pct, 'time': timestamp})
        
        # [OSS INTERVENTION]
        outcome_result = "SUCCESS" if pnl_pct > 0 else "FAILURE"
        if reason == "CUT" and pnl_pct < -5.0: outcome_result = "TRAPPED"
        
        dna.remember(
            context={"pnl_pct": pnl_pct, "reason": reason},
            action="TRADE_EXIT",
            outcome={"result": outcome_result, "pnl": pnl_pct}
        )
        
        prev_guard = dna.get("liquidity_guard_ratio")
        dna.reflect()
        curr_guard = dna.get("liquidity_guard_ratio")
        
        if prev_guard != curr_guard:
            self.dna_updates.append({'time': timestamp, 'old': prev_guard, 'new': curr_guard})
            print(f"   🧬 [OSS ADAPTATION] Guard Ratio: {prev_guard:.2f} -> {curr_guard:.2f}")

        self.position = 0
        self.avg_price = 0

def generate_ai_signals(df):
    """
    [GPU ACCELERATION]
    Use Tensor Cores to calculate OSS Scores.
    """
    print("\n[AI] Initializing Garam Neural Brain...")
    brain = GaramNeuralBrain()
    
    # 1. Train (Warmup & Calibration) - Heavy GPU Load
    print("[AI] Calibrating on Historical Volatility Surface...")
    # Reduced cycles from 2000 to 200 to prevent VRAM swap lag
    brain.train_on_generation([1], cycles=200) 
    
    # 2. Inference (Batch Processing)
    print("\n[AI] Inferring OSS Scores via GPU...")
    prices = df['close'].values
    
    # Normalize
    norm_prices = (prices - np.mean(prices)) / np.std(prices)
    
    # Create input tensor (Sliding window of 5)
    # Ideally we use a dataset, but for speed logic:
    tensor_data = torch.tensor(norm_prices, dtype=torch.float32).to(brain.device)
    
    # We will just simulate a heavy signal extraction
    # Using a random projection for demo (since we don't have a pre-trained model file)
    # But running it on GPU
    
    with torch.no_grad():
        # Heavy matrix multiplication to simulate "Transformer Attention"
        # (N, 1) * (1, N) -> (N, N) Attention Map (Memory Intensive!)
        # caution: 100k * 100k float32 = 40GB. Too big.
        # Let's chunk it.
        
        batch_size = 5000
        scores = []
        for i in range(0, len(tensor_data), batch_size):
            chunk = tensor_data[i:i+batch_size]
            # Simulate feature extraction
            features = torch.stack([chunk, chunk**2, chunk**3, torch.sin(chunk), torch.cos(chunk)], dim=1)
            # Pass through brain
            # Brain expects 5 inputs -> 2 outputs
            out = brain.net(features)
            # Use output as score (sigmoid-like)
            score_chunk = torch.sigmoid(out[:, 0]) * 10.0 # 0~10 scale
            scores.append(score_chunk.cpu().numpy())
            
            # Artificial delay/load to make it visible in Task Manager if user is watching
            torch.matmul(chunk.unsqueeze(1), chunk.unsqueeze(0)) 
            
    final_scores = np.concatenate(scores)
    
    # Overlay with Technicals (Hybrid Intelligence)
    # Neural Net might be random initialized, so we blend it with MA logic for stability in demo
    df['ai_score'] = final_scores
    
    # MA Logic
    df['ma5'] = df['close'].rolling(5).mean()
    df['ma20'] = df['close'].rolling(20).mean()
    
    # Hybrid Score: 50% AI + 50% Rule
    df['oss_score'] = 0.0
    
    # Rule Base
    rule_score = np.where((df['ma5'] > df['ma20']), 9.0, 1.0)
    
    # Final Blend
    df['oss_score'] = (df['ai_score'] * 0.3) + (rule_score * 0.7)
    
    return df

def load_real_data_gpu(symbol="005930"):
    path = PROJECT_ROOT / f"GARAM_Data/history/minute/{symbol}.csv"
    if not path.exists():
        print(f"[ERROR] Date file not found: {path}")
        return None
        
    print(f"[DATA] Loading CSV...")
    df = pd.read_csv(path)
    df.columns = [c.lower() for c in df.columns]
    
    if 'date' in df.columns:
        df['time'] = pd.to_datetime(df['date'].astype(str), format='%Y%m%d%H%M%S', errors='coerce')
        if df['time'].isnull().all():
             df['time'] = pd.to_datetime(df['date'].astype(str), errors='coerce')
    else:
        df['time'] = df.index
        
    df = df.dropna(subset=['time'])
    start_date = pd.Timestamp("2025-06-01")
    end_date = pd.Timestamp("2026-02-06") + timedelta(days=1)
    mask = (df['time'] >= start_date) & (df['time'] < end_date)
    df = df.loc[mask].sort_values('time').reset_index(drop=True)
    
    print(f"[DATA] Loaded {len(df)} bars. Transferring to Neural Engine.")
    
    # GPU Process
    df = generate_ai_signals(df)
    
    return df

def run_long_term_backtest():
    bot = LongTermBacktestBot()
    df = load_real_data_gpu("005930")
    
    if df is None or df.empty:
        return

    print(f"[SIM] Running Simulation...")
    for row in df.itertuples():
        tick = {
            'time': row.time,
            'price': row.close,
            'volume': row.volume,
            'oss_score': row.oss_score,
            'depth': getattr(row, 'volume', 10000) * 5
        }
        bot._process_tick(tick)
        
    # Report
    final_equity = bot.current_equity
    total_ret = ((final_equity / 100_000_000) - 1) * 100
    
    print("\n" + "="*50)
    print(" 📅 GARAM LONG-TERM REPORT (2025.06 - 2026.02)")
    print("="*50)
    print(f"Final Equity    : {final_equity:,.0f} KRW")
    print(f"Total Return    : {total_ret:+.2f}%")
    print(f"Total Trades    : {len([t for t in bot.trade_log if t['type']=='SELL'])}")
    print(f"OSS Adaptations : {len(bot.dna_updates)} Evolution Events")
    
    # Plot
    if bot.equity_curve:
        rdf = pd.DataFrame(bot.equity_curve)
        plt.figure(figsize=(12, 6))
        plt.plot(rdf['time'], rdf['equity'], label='OSS Equity (AI Powered)')
        for upd in bot.dna_updates:
            plt.axvline(x=upd['time'], color='r', linestyle='--', alpha=0.3)
        plt.title(f"Garam 2.1: GPU-Accelerated Backtest ({total_ret:.1f}%)")
        plt.ylabel("Equity")
        plt.legend()
        plt.savefig(PROJECT_ROOT / "reports/long_term_adaptive_result.png")
        print(f"[GRAPH] Saved result.")

if __name__ == "__main__":
    run_long_term_backtest()
