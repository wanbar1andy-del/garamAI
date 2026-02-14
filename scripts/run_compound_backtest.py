
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from datetime import datetime

# Setup Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

# Imports
from core.engine.typhoon_orchestrator import TyphoonOrchestrator
from core.active_config.tactical_genome import dna

# Subclass to prevent sys.exit() and capture signals
class BacktestOrchestrator(TyphoonOrchestrator):
    def __init__(self):
        super().__init__()
        self.trade_log = []
        self.equity_curve = []
        self.capital = 100_000_000 # 100M KRW Start
        self.position = 0 # Shares
        self.avg_price = 0
        
        # Fee & Slippage
        self.fee_rate = 0.00015 # 0.015%
        self.tax_rate = 0.0020  # 0.20%
        self.slippage = 0.0005  # 0.05%
        
        self.current_equity = self.capital

    def _process_tick(self, tick):
        # Override to prevent sys.exit and track trades
        
        # Super logic call (We need to capture the side-effects of phase change)
        # But super()._process_tick calls sys.exit(). We need to intercept phase 4.
        
        # Copy-paste logic essentially, or wrap. 
        # Since logic is simple, I'll reimplement the 'Action' parts here based on Phase.
        
        self.current_price = tick['price']
        self.total_volume = tick.get('volume', 0)
        internal_vol = tick.get('internal_vol', 0)
        
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
                self.execute_sell("CUT", self.current_price)
                self.phase = "PHASE_0_IDLE"

        elif self.phase == "PHASE_3_FORMATION":
            self.highest_price = max(self.highest_price, self.current_price)
            # Pulse Logic (Simplified for backtest speed)
            action = self.commander.run_anchor_logic(self.current_price, self.entry_price, self.highest_price)
            if action == "EXIT_ALL":
                self.phase = "PHASE_4_EXTRACTION"
                
        elif self.phase == "PHASE_4_EXTRACTION":
            self.execute_sell("PROFIT", self.current_price)
            self.phase = "PHASE_0_IDLE"
            
        # Update Equity (Mark-to-Market)
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
        # All-in for Compound Growth Test
        cost_price = price * (1 + self.slippage)
        max_qty = int(self.capital / (cost_price * (1 + self.fee_rate)))
        
        if max_qty > 0:
            cost = max_qty * cost_price
            fee = cost * self.fee_rate
            self.capital -= (cost + fee)
            self.position = max_qty
            self.avg_price = cost_price
            self.trade_log.append({'type': 'BUY', 'price': cost_price, 'qty': max_qty, 'time': 'SimTime'})

    def execute_sell(self, reason, price):
        if self.position == 0: return
        
        sell_price = price * (1 - self.slippage)
        revenue = self.position * sell_price
        fee = revenue * self.fee_rate
        tax = revenue * self.tax_rate
        
        self.capital += (revenue - fee - tax)
        
        pnl = (revenue - fee - tax) - (self.position * self.avg_price)
        pnl_pct = (pnl / (self.position * self.avg_price)) * 100
        
        self.trade_log.append({'type': 'SELL', 'price': sell_price, 'qty': self.position, 'reason': reason, 'pnl_pct': pnl_pct})
        self.position = 0
        self.avg_price = 0

def load_data():
    # Attempt to load 005930 (Samsung Elec)
    # Trying valid path patterns
    candidates = [
        PROJECT_ROOT / "GARAM_Data/history/minute/005930.csv",
        PROJECT_ROOT / "data/history/minute/005930.csv",
        PROJECT_ROOT / "GARAM_Data/005930.csv"
    ]
    
    df = None
    for p in candidates:
        if p.exists():
            print(f"[DATA] Loading from {p}")
            df = pd.read_csv(p)
            break
            
    if df is None:
        print("[DATA] Real data not found. Generating Mock Data for Logic Verification.")
        # Generate Sine Wave Data
        dates = pd.date_range(start="2025-01-01", periods=10000, freq="1min")
        prices = 70000 + 5000 * np.sin(np.linspace(0, 50, 10000)) + np.random.normal(0, 100, 10000)
        df = pd.DataFrame({'date': dates, 'open': prices, 'high': prices+100, 'low': prices-100, 'close': prices, 'volume': 10000})
        
    df.columns = [c.lower() for c in df.columns]
    if 'date' in df.columns:
        df['time'] = df['date']
    elif 'time' not in df.columns:
        df['time'] = df.index
        
    # Generate Fake OSS Signals for testing
    df['oss_score'] = np.random.uniform(0, 10, len(df))
    # Make sure we have some trigger points
    # When price is low and turning up, give high score
    df['ma20'] = df['close'].rolling(20).mean()
    df.loc[(df['close'] > df['ma20']) & (df['close'].shift(1) < df['ma20'].shift(1)), 'oss_score'] = 9.0
    
    return df

def run_backtest():
    print("=== [GARAM OSS] Compound Growth Backtest ===")
    
    df = load_data()
    bot = BacktestOrchestrator()
    
    print(f"[SIM] Running simulation on {len(df)} bars...")
    
    for idx, row in df.iterrows():
        tick = {
            'time': row.get('time'),
            'price': row['close'],
            'volume': row['volume'],
            'oss_score': row.get('oss_score', 0),
            'depth': 100000 # Mock depth
        }
        bot._process_tick(tick)
        
    # Final Result
    final_equity = bot.current_equity
    cagr_pct = ((final_equity / 100_000_000) - 1) * 100
    
    print("\n" + "="*40)
    print("          BACKTEST REPORT          ")
    print("="*40)
    print(f"Initial Capital : 100,000,000 KRW")
    print(f"Final Equity    : {final_equity:,.0f} KRW")
    print(f"Total Return    : {cagr_pct:+.2f}%")
    print(f"Total Trades    : {len([t for t in bot.trade_log if t['type']=='SELL'])}")
    print("-" * 40)
    
    # Plotting
    equity_df = pd.DataFrame(bot.equity_curve)
    if not equity_df.empty:
        plt.figure(figsize=(10, 6))
        plt.plot(equity_df['equity'], label='OSS Equity')
        plt.title('Garam OSS: Compound Growth Curve')
        plt.xlabel('Ticks')
        plt.ylabel('Equity (KRW)')
        plt.grid(True)
        plt.legend()
        
        img_path = PROJECT_ROOT / "reports/backtest_compound_result.png"
        plt.savefig(img_path)
        print(f"[GRAPH] Saved to {img_path}")
    
if __name__ == "__main__":
    run_backtest()
