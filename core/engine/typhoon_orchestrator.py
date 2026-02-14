
import time
import random
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from core.tactics.formation_commander import FormationCommander
from core.liquidity.physics_engine import LiquidityArchitect # Alias for compatibility
from core.active_config.tactical_genome import dna

class TyphoonOrchestrator:
    """
    [GARAM 2.1 KERNEL]
    Typhoon Generation & Energy Harvesting Architecture.
    Orchestrates the 4-Phase Cycle: Discovery -> Trigger -> Formation -> Extraction.
    """
    def __init__(self):
        self.commander = FormationCommander()
        self.architect = LiquidityArchitect()
        self.phase = "PHASE_0_IDLE"
        self.hero_symbol = None
        
        # Simulation State
        self.current_price = 0
        self.entry_price = 0
        self.highest_price = 0
        self.total_volume = 0
        self.external_flow_ratio = 0.0

    def get_acc_threshold(self):
        return dna.get("typhoon_acc_threshold")

    def run_cycle(self, market_feed):
        print(f"\n===================================================")
        print(f"   🌊 GARAM TYPHOON ENGINE | STATUS: {self.phase}")
        print(f"===================================================")
        
        for tick in market_feed:
            self._process_tick(tick)
            time.sleep(0.5) # slow down for demo visibility

    def _process_tick(self, tick):
        self.current_price = tick['price']
        self.total_volume = tick.get('volume', 0)
        internal_vol = tick.get('internal_vol', 0)
        
        # [Typhoon Monitor] Acceleration Calculation
        # V_ext (External Volume) vs V_garam (Internal Volume)
        external_vol = self.total_volume - internal_vol
        
        # Calculate Acceleration (V_ext / V_garam)
        # If V_garam is 0, use 1 to avoid div zero (or infinite acc if external exists)
        base_internal = max(1, internal_vol)
        acc_ratio = external_vol / base_internal
        
        # --- PHASE LOGIC ---
        
        # Phase 1: Butterfly Discovery
        if self.phase == "PHASE_0_IDLE":
            score = tick['oss_score'] + tick['sentiment_score']
            print(f"   [SCAN] Score: {score:.2f} | Price: {self.current_price}")
            
            if score > 8.0:
                self.phase = "PHASE_1_DISCOVERY"
                self.hero_symbol = tick['symbol']
                print(f"   🦋 [PHASE 1] NA-BI (Butterfly) Found! Hero: {self.hero_symbol}")
                self._transition_to_trigger()

        # Phase 2: Wing Flap (Butterfly Module)
        elif self.phase == "PHASE_2_TRIGGER":
            # Staggered Order Check
            # Simulating time delay effect of staggered orders
            if self.current_price > self.entry_price * 1.02:
                print(f"   🚀 [PHASE 2] Lift-off! Signals captured by Market Scanners.")
                self.phase = "PHASE_3_FORMATION"
                
        # Phase 3: Typhoon Formation (Typhoon Monitor)
        elif self.phase == "PHASE_3_FORMATION":
            self.highest_price = max(self.highest_price, self.current_price)
            
            print(f"   🌀 [PHASE 3] Typhoon Status: V_ext/V_garam = {acc_ratio:.2f}x")
            
            if acc_ratio > 5.0:
                 print("      ✅ Typhoon Formed! (V_ext is 5x of V_garam)")
            elif acc_ratio < 0.5:
                 print("      ⚠️ Warning: Typhoon Stalling. (Mostly Internal Flow)")

            # Pulse Check (Logic from Commander)
            support_level = self.highest_price * 0.95 
            self.commander.run_pulse_logic(self.current_price, support_level)
            
            # Transition Check
            action = self.commander.run_anchor_logic(self.current_price, self.entry_price, self.highest_price)
            if action == "EXIT_ALL":
                print(f"   📉 [SIGNAL] Trend Broken. Initiating Energy Harvest.")
                self.phase = "PHASE_4_EXTRACTION"

        # Phase 4: Energy Extraction (Harvest)
        elif self.phase == "PHASE_4_EXTRACTION":
            print(f"   💰 [PHASE 4] Harvesting Energy.")
            # Calculate optimal exit path based on "peak momentum"
            print(f"      [PATH] Locking in profits at {self.current_price} (Peak was {self.highest_price})")
            self.commander.execute_tiered_exit()
            print(f"   ✅ [COMPLETE] Mission Accomplished.")
            sys.exit(0)

    def _transition_to_trigger(self):
        self.phase = "PHASE_2_TRIGGER"
        self.entry_price = self.current_price
        self.highest_price = self.current_price
        
        print(f"   👊 [ACTION] Executing Staggered Entry (Creating Attractive Signal)...")
        # Simulate staggered impact
        time.sleep(1) 
        print(f"      -> Commander T0 Entry Complete.")
        time.sleep(0.5)
        print(f"      -> Division Waterfall Entry Initiated...")
        
        self.architect.learn_from_execution(50000, self.current_price, self.current_price*1.005, 1000000, 0.02)

if __name__ == "__main__":
    orchestrator = TyphoonOrchestrator()
    
    # SIMULATED MARKET FEED
    # Scenario: Butterfly found -> We enter -> External Money joins (Typhoon) -> Peak -> Crash -> Exit
    market_scenario = [
        # 1. Scanning
        {'symbol': '005930', 'price': 70000, 'volume': 10000, 'depth': 50000, 'oss_score': 4.0, 'sentiment_score': 1.0, 'internal_vol': 0},
        {'symbol': '005930', 'price': 70000, 'volume': 10000, 'depth': 50000, 'oss_score': 7.5, 'sentiment_score': 2.0, 'internal_vol': 0},
        # 2. Hero Found (High Score)
        {'symbol': '005930', 'price': 70100, 'volume': 20000, 'depth': 50000, 'oss_score': 5.0, 'sentiment_score': 4.5, 'internal_vol': 0}, # Total 9.5
        # 3. Trigger (We enter) -> Price goes up
        {'symbol': '005930', 'price': 71000, 'volume': 100000, 'depth': 40000, 'oss_score': 0, 'sentiment_score': 0, 'internal_vol': 80000}, # Mostly us
        {'symbol': '005930', 'price': 72000, 'volume': 150000, 'depth': 40000, 'oss_score': 0, 'sentiment_score': 0, 'internal_vol': 20000}, # External starts joining
        # 4. Formation (Self-Sustaining)
        {'symbol': '005930', 'price': 75000, 'volume': 500000, 'depth': 30000, 'oss_score': 0, 'sentiment_score': 0, 'internal_vol': 50000}, # 10% us, 90% external
        {'symbol': '005930', 'price': 78000, 'volume': 800000, 'depth': 30000, 'oss_score': 0, 'sentiment_score': 0, 'internal_vol': 10000}, # Mooning
        # 5. Peak & Pullback (Pulse Logic should fire)
        {'symbol': '005930', 'price': 74000, 'volume': 200000, 'depth': 50000, 'oss_score': 0, 'sentiment_score': 0, 'internal_vol': 0}, # Support test
        # 6. Rebound then Crash
        {'symbol': '005930', 'price': 76000, 'volume': 300000, 'depth': 50000, 'oss_score': 0, 'sentiment_score': 0, 'internal_vol': 0},
        {'symbol': '005930', 'price': 70000, 'volume': 400000, 'depth': 50000, 'oss_score': 0, 'sentiment_score': 0, 'internal_vol': 0}, # Broken
    ]
    
    orchestrator.run_cycle(market_scenario)
