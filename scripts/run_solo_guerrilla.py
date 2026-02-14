
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# Setup Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))
sys.path.append(str(PROJECT_ROOT / "scripts"))

# Imports
from core.active_config.tactical_genome import dna

# Import Sibling Script
# We use a try-block or direct import assuming path is set
try:
    from run_long_term_backtest import LongTermBacktestBot, load_real_data_gpu
except ImportError:
    from scripts.run_long_term_backtest import LongTermBacktestBot, load_real_data_gpu

class SoloGuerrillaBot(LongTermBacktestBot):
    def __init__(self):
        super().__init__()
        self.mode = "SOLO"
        self.solo_cap_limit = dna.get("solo_capital_limit") or 300_000_000
        self.oss_threshold = 8.0 
        self.stop_pct = 0.07     
        self._adjust_mode()

    def _adjust_mode(self):
        if self.capital < self.solo_cap_limit:
            self.mode = "SOLO_GUERRILLA"
            self.oss_threshold = dna.get("solo_oss_threshold") or 7.2
            self.stop_pct = dna.get("solo_trailing_stop") or 0.03
            dna.params["liquidity_guard_ratio"] = 0.99 
        else:
            self.mode = "LEGION_TYPHOON"
            self.oss_threshold = 8.0
            self.stop_pct = 0.07
            dna.params["liquidity_guard_ratio"] = 0.30
            
    def _process_tick(self, tick):
        if self.position == 0:
            self._adjust_mode()
        self.current_price = tick['price']
        
        # --- SOLO PHASE LOGIC ---
        if self.phase == "PHASE_0_IDLE":
            score = tick.get('oss_score', 0)
            # Solo Entry: Lower Threshold
            if score > self.oss_threshold and self.position == 0:
                self.phase = "PHASE_1_DISCOVERY"
                self._transition_to_trigger()

        elif self.phase == "PHASE_2_TRIGGER":
            # Quick Trigger (1%)
            if self.current_price > self.entry_price * 1.01: 
                self.phase = "PHASE_3_FORMATION"
            elif self.current_price < self.entry_price * 0.99: 
                self.execute_sell("CUT", self.current_price, tick['time'])
                self.phase = "PHASE_0_IDLE"

        elif self.phase == "PHASE_3_FORMATION":
            self.highest_price = max(self.highest_price, self.current_price)
            # Tight Trailing Stop
            stop_price = self.highest_price * (1 - self.stop_pct)
            
            if self.current_price < stop_price:
                self.phase = "PHASE_4_EXTRACTION"
                
        elif self.phase == "PHASE_4_EXTRACTION":
            self.execute_sell("PROFIT", self.current_price, tick['time'])
            self.phase = "PHASE_0_IDLE"
            
        # Equity Update
        floating_pnl = 0
        if self.position > 0:
            val = self.position * self.current_price
            cost = self.position * self.avg_price
            floating_pnl = val - cost
        self.current_equity = self.capital + floating_pnl
        self.equity_curve.append({'time': tick['time'], 'equity': self.current_equity})

def run_solo_test():
    bot = SoloGuerrillaBot()
    df = load_real_data_gpu("005930") 
    
    if df is None: return

    print(f"\n[SOLO] Running 'Guerrilla Mode' Test...")
    print(f"       Threshold: {bot.oss_threshold} (Legion was 8.0)")
    print(f"       Trailing Stop: {bot.stop_pct*100}% (Legion was 7%)")
    
    # Inject Breeze Signals (Score 7.5) to test Solo Sensitivity
    df['ma10'] = df['close'].rolling(10).mean()
    cond_breeze = (df['ma5'] > df['ma10']) & (df['oss_score'] < 8.0)
    df.loc[cond_breeze, 'oss_score'] = 7.5 
    
    # Run
    for row in df.itertuples():
        tick = {
            'time': row.time, 'price': row.close, 'volume': row.volume,
            'oss_score': row.oss_score
        }
        bot._process_tick(tick)
        
    final_equity = bot.current_equity
    total_ret = ((final_equity / 100_000_000) - 1) * 100
    
    print("\n" + "="*50)
    print(" [SOLO GUERRILLA REPORT]")
    print("="*50)
    print(f"Final Equity    : {final_equity:,.0f} KRW")
    print(f"Total Return    : {total_ret:+.2f}%")
    print(f"Total Trades    : {len([t for t in bot.trade_log if t['type']=='SELL'])}")
    print("-" * 50)

    # Plot
    if bot.equity_curve:
        rdf = pd.DataFrame(bot.equity_curve)
        plt.figure(figsize=(12, 6))
        plt.plot(rdf['time'], rdf['equity'], label='Solo Guerrilla', color='green')
        plt.title(f"Garam 2.1: Solo Guerrilla ({total_ret:.1f}%)")
        plt.xlabel("Date")
        plt.ylabel("Equity")
        plt.grid(True)
        plt.legend()
        plt.savefig(PROJECT_ROOT / "reports/solo_guerrilla_result.png")
        print(f"[GRAPH] Saved result.")

if __name__ == "__main__":
    run_solo_test()
