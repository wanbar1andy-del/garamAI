
from typing import List, Dict
from dataclasses import dataclass
import time

@dataclass
class FollowerStats:
    count: int
    total_aum: float
    avg_return: float

class AUMControlTower:
    """
    [CONTROL TOWER]
    Real-time monitoring of the 100-person Division vs Commander.
    """
    def __init__(self, commander_id="ACC_COMMANDER_001"):
        self.commander_id = commander_id
        self.commander_pnl = 0.0
        self.followers: Dict[str, float] = {} # id -> pnl
        self.follower_capitals: Dict[str, float] = {}

    def update_pnl(self, account_id, pnl_pct):
        if account_id == self.commander_id:
            self.commander_pnl = pnl_pct
        else:
            self.followers[account_id] = pnl_pct

    def register_capital(self, account_id, capital):
        self.follower_capitals[account_id] = capital

    def generate_dashboard(self):
        # Aggregate Follower Stats
        follower_pnls = list(self.followers.values())
        if not follower_pnls:
            avg_fol_ret = 0.0
        else:
            avg_fol_ret = sum(follower_pnls) / len(follower_pnls)
            
        total_aum = sum(self.follower_capitals.values())
        
        # Gap Analysis
        gap = self.commander_pnl - avg_fol_ret
        
        print("\n" + "█" * 60)
        print("          GARAM DIVISION CONTROL TOWER (AUM MONITOR)          ")
        print("█" * 60)
        print(f"📊 TOTAL AUM (100 Div): ₩{total_aum:,.0f}")
        print("-" * 60)
        print(f"👑 COMMANDER Return   : {self.commander_pnl:+.2f}%")
        print(f"🛡️ DIVISION Avg Return: {avg_fol_ret:+.2f}%")
        print(f"⚡ Execution Gap      : {gap:+.2f}%")
        
        if abs(gap) > 0.5:
             print("⚠️ ALERT: Slippage Disparity Detected! Check Priority Engine.")
        else:
             print("✅ STATUS: Sync Optimized.")
        print("█" * 60 + "\n")

if __name__ == "__main__":
    # Test Scenario
    tower = AUMControlTower()
    
    # Register 100 soldiers (Simulation)
    import random
    total_soldiers = 100
    for i in range(total_soldiers):
        uid = f"SOLDIER_{i:03d}"
        cap = random.uniform(10_000_000, 50_000_000) # 10m ~ 50m won
        tower.register_capital(uid, cap)
        
        # Simulate slight slippage for followers
        pnl = 12.5 + random.uniform(-0.3, 0.1) 
        tower.update_pnl(uid, pnl)
        
    # Commander result
    tower.update_pnl("ACC_COMMANDER_001", 12.8) # Commander got best price
    
    tower.generate_dashboard()
