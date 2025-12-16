import pandas as pd
import json
import time
from pathlib import Path

# Mock Engine Class if not available
class RealTimeEngine:
    def __init__(self, cash=20000000, guard=None):
        self.cash = cash
        self.guard = guard
        self.equity = cash
        self.market_is_open = True
        print(f"[SIM] Initialized with Capital: {cash:,} KRW")
        if guard:
            print(f"[SIM] Guard Params Loaded: {guard}")

    def market_open(self):
        # Time check
        now = pd.Timestamp.now(tz="Asia/Seoul")
        if now.hour >= 15 and now.minute >= 30:
            return False
        return True

    def update_market(self, sym, bar):
        # Update logic
        pass

    def step(self):
        # Step logic
        pass

    def save_report(self, path):
        print(f"[SIM] Report saved to {path}")

def load_guard_params(path):
    p = Path(path)
    if p.exists():
        return json.loads(p.read_text(encoding='utf-8'))
    return {}

CAPITAL = 20_000_000

def main():
    print(">>> Starting Real-Time Simulator...")
    
    # Symbols
    u_path = Path("configs/universe_400.txt")
    if not u_path.exists():
         if Path("config/universe_400.txt").exists():
             u_path = Path("config/universe_400.txt")
         else:
             print("Universe not found")
             return
             
    symbols = u_path.read_text(encoding='utf-8').splitlines()
    
    # Guard
    guard = load_guard_params("guard_param_recommended.json")
    
    engine = RealTimeEngine(cash=CAPITAL, guard=guard)

    # Simulation Loop
    while engine.market_open():
        # In real scenario, we read latest parquet
        # For script demo, we iterate once or wait
        # print("Sim Step...")
        time.sleep(60)
        
    engine.save_report("reports/realtime_sim_report.json")

if __name__ == "__main__":
    main()
