
import random
from dataclasses import dataclass
from typing import List, Dict

@dataclass
class WhaleSig:
    detected: bool
    type: str # 'BUYER' or 'SELLER'
    volume_ratio: float # Whale Vol / Mkt Vol
    action_suggestion: str

from core.active_config.tactical_genome import dna

class SharkRadar:
    """
    [ANTIGRAVITY MODULE: SHARK RADAR]
    Powered by Active Tactical DNA.
    """
    
    def __init__(self):
        self.tick_history = []
        
    def analyze_ticks(self, ticks: List[dict], current_volume: int):
        whale_threshold = dna.get("whale_min_val")
        
        whale_buy_vol = 0
        whale_sell_vol = 0
        
        for t in ticks:
            val = t['price'] * t['vol']
            if val >= whale_threshold:
                if t['side'] == 'buy':
                    whale_buy_vol += t['vol']
                    print(f"   🐋 [WHALE] BIG BUY: {val/1000000:.0f}M (Thres: {whale_threshold/10e5:.0f}M)")
                else:
                    whale_sell_vol += t['vol']
                    print(f"   🦈 [SHARK] BIG SELL: {val/1000000:.0f}M")
                    
        # ... (rest of logic) ...
        return WhaleSig(False, 'NONE', 0.0, "MONITOR")

    def check_shakeout(self, price_drop_pct, volume_drop_pct):
        trap_threshold = dna.get("shakeout_vol_drop")
        
        if price_drop_pct > 0.02:
            if volume_drop_pct > trap_threshold:
                print(f"   🛡️ [ANTI-TRAP] Fake Drop (Vol -{volume_drop_pct*100:.0f}% > -{trap_threshold*100:.0f}%)")
                return "TRAP_IGNORE"
            else:
                return "REAL_DUMP"
        return "NORMAL"

class LiquidityGuard:
    def check_exposure(self, my_holding_vol, avg_5min_vol):
        limit_ratio = dna.get("liquidity_guard_ratio")
        ratio = my_holding_vol / (avg_5min_vol + 1e-9)
        
        print(f"   [GUARD] Exposure: {ratio*100:.1f}% (Limit: {limit_ratio*100:.1f}%)")
        
        if ratio > limit_ratio:
            return "REDUCE_SIZE"
        return "SAFE"

if __name__ == "__main__":
    radar = SharkRadar()
    guard = LiquidityGuard()
    
    print("=== [TEST] Shark & Guard Protocol ===")
    
    # 1. Whale Buying
    ticks = [
        {'price': 50000, 'vol': 5000, 'side': 'buy'}, # 250M
        {'price': 50100, 'vol': 100, 'side': 'sell'},
        {'price': 50000, 'vol': 3000, 'side': 'buy'}, # 150M
    ]
    sig = radar.analyze_ticks(ticks, 10000)
    print(f"   -> Suggestion: {sig.action_suggestion} (Ratio: {sig.volume_ratio:.2f})")
    
    # 2. Fake Drop
    radar.check_shakeout(0.03, 0.6)
    
    # 3. Guard Check
    guard.check_exposure(35000, 100000) # 35%
