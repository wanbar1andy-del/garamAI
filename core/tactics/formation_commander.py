
import time
import random
from dataclasses import dataclass
from typing import List, Dict
from enum import Enum

class FormationMode(Enum):
    ANCHOR = "ANCHOR_C_MAX"
    PULSE = "PULSE_MOMENTUM"
    EXIT_TIERED = "EXIT_REVERSE_WATERFALL"

@dataclass
class GroupState:
    group_id: int
    accounts: List[str]
    mode: str = "HOLD"
    
from core.active_config.tactical_genome import dna

class FormationCommander:
    """
    [TACTICAL COMMANDER]
    Orchestrates the movement of the 'Commander' and the 'Division'.
    Implements: Anchor Mode, Pulse Mode, Inducement Tracking, Impact Absorption, Tiered Exit.
    """
    
    def __init__(self, commander_id="ACC_COMMANDER_001", total_followers=100):
        self.commander_id = commander_id
        self.followers = [f"ACC_DIV_{i:03d}" for i in range(total_followers)]
        # Split followers into 5 Pulse Groups
        self.groups = self._split_into_groups(self.followers, 5)
        
        # State
        self.external_vol_ratio = 0.0
        self.current_trend_support = True
        self.is_self_sustaining = False
        
        # Config (Dynamic DNA)
        # self.impact_limit_ratio = 0.20 # Deprecated
        # self.trailing_stop_pct = 0.07 # Deprecated

    @property
    def impact_limit_ratio(self):
        return dna.get("liquidity_guard_ratio") # Use Guard Ratio as Limit
        
    @property
    def trailing_stop_pct(self):
        return dna.get("trailing_stop_pct")
        
    def _split_into_groups(self, followers, n):
        groups = []
        chk = len(followers) // n
        for i in range(n):
            batch = followers[i*chk : (i+1)*chk]
            groups.append(GroupState(i, batch))
        return groups

    def update_market_context(self, internal_vol, total_vol, order_book_depth):
        """
        [Inducement Tracker & External Flow Detection]
        """
        if total_vol <= 0: return

        external_vol = total_vol - internal_vol
        self.external_vol_ratio = external_vol / total_vol
        
        print(f"   [FLOW] Internal: {internal_vol} | External: {external_vol} ({self.external_vol_ratio*100:.1f}%)")
        
        # Detect 'Self-Sustaining' Trend
        if self.external_vol_ratio > 0.6: # If >60% is external
            self.is_self_sustaining = True
            print("   ✅ [SIGNAL] Self-Sustaining Trend Confirmed. Division Mode: ADJUST.")
        elif internal_vol > 0 and self.external_vol_ratio < 0.3:
            self.is_self_sustaining = False
            print("   ⚠️ [WARNING] Price driven by Internal Flow only. Prepare Conservative Exit.")

        # Impact Absorption Check
        # Return max tradeable volume allowed right now
        return order_book_depth * self.impact_limit_ratio

    def run_anchor_logic(self, current_price, entry_price, highest_price):
        """
        [Anchor Mode] Commander Logic: C_Max
        """
        drop_from_high = (highest_price - current_price) / highest_price
        
        action = "HOLD"
        reason = "Trend Active"
        
        if drop_from_high >= self.trailing_stop_pct:
            action = "EXIT_ALL"
            reason = f"Trailing Stop Triggered (-{drop_from_high*100:.2f}%)"
            
        print(f"   [ANCHOR] Commander {self.commander_id}: {action} ({reason})")
        return action

    def run_pulse_logic(self, market_price, support_level):
        """
        [Pulse Mode] Division Logic
        5 Groups rotate: Profit Taking -> Re-entry at Support
        """
        print(f"   [PULSE] Division Operations (Price: {market_price}, Support: {support_level})")
        
        for group in self.groups:
            # Simulation of heterogeneous behavior
            # Group 0,1: Profit Taking (Sell)
            # Group 2,3: Wait
            # Group 4  : Re-entry (Buy at Support)
            
            # Logic: If Price nears Support (+- 1%), Group 4 Buys to suppress volatility
            if abs(market_price - support_level) / support_level < 0.01:
                if group.group_id == 4:
                    print(f"      Group {group.group_id}: 🔵 RE-ENTRY (Support Defense)")
            
            # Logic: If Price rallies hard, Group 0 Sells slightly to provide liquidity
            elif market_price > support_level * 1.05:
                if group.group_id == 0:
                     print(f"      Group {group.group_id}: 🔴 PROFIT PRESERVATION (Liquidity Supply)")

    def execute_tiered_exit(self):
        """
        [Tiered Exit] Reverse Waterfall
        Logic Only for now.
        """
        print("\n   🚨 [EXIT PROTOCOL] REVERSE WATERFALL INITIATED")
        print("   1. [T+00:00] Commander ACC_COMMANDER_001 -> IMMEDIATE EXIT (Priority: Highest)")
        print("   2. [T+01:00] Division Group 0 (20%) -> VWAP Exit")
        print("   3. [T+03:00] Division Group 1 (20%) -> VWAP Exit")
        print("   4. ... dispersing remaining flow over 10 minutes ...")
        print("   [STATUS] Protocol Logic Ready. Waiting for Trigger.\n")

if __name__ == "__main__":
    # Test Scenario
    cmd = FormationCommander()
    
    print("=== [SCENARIO] Strong Trend w/ Correction ===")
    
    # 1. Market Update (Inducement Check)
    # Total Vol: 1M, Internal: 200k -> 80% External (Good)
    limit = cmd.update_market_context(internal_vol=200000, total_vol=1000000, order_book_depth=50000)
    print(f"   [IMPACT] Allowed Trade Volume: {limit:.0f}")
    
    # 2. Anchor Check
    cmd.run_anchor_logic(current_price=75000, entry_price=70000, highest_price=76000)
    
    # 3. Pulse Check (Support at 74000)
    cmd.run_pulse_logic(market_price=74500, support_level=74000)
    
    print("\n=== [SCENARIO] Trend Collapse ===")
    # 1. External flow dries up
    cmd.update_market_context(internal_vol=10000, total_vol=12000, order_book_depth=50000)
    
    # 2. Anchor Breaks (High was 80000, Now 72000 -> -10% drop)
    choice = cmd.run_anchor_logic(current_price=72000, entry_price=70000, highest_price=80000)
    
    if choice == "EXIT_ALL":
        cmd.execute_tiered_exit()
