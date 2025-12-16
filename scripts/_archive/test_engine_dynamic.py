import sys
import os
import logging

# Setup Path
sys.path.append(os.path.abspath("C:/garam/garam"))

from garam.engine.controller import HybridController
from garam.engine.base import BaseEngine

# Mock Engines
class MockEngine(BaseEngine):
    def generate_signals(self, market_data):
        # Always return score 1.0 for test
        return {"TEST": 1.0}
    def get_risk_factor(self):
        return 0.5

def test_dynamic_logic():
    logging.basicConfig(level=logging.INFO)
    
    # Config: 50:50 base, Turbo=2.0 (Boost E2), ABS=0.0 (Kill E1)
    config = {
        "mode": "DYNAMIC",
        "weights": {"engine1": 1.0, "engine2": 1.0}, # equal base
        "dynamic_rules": {
            "turbo_multiplier": 2.0,
            "abs_multiplier": 0.0
        }
    }
    
    controller = HybridController(config)
    
    e1 = MockEngine("engine1", {})
    e2 = MockEngine("engine2", {})
    
    controller.register_engine(e1)
    controller.register_engine(e2)
    
    market_data = ["TEST"]
    
    print("\n--- TEST 1: UNKNOWN Regime (Neutral) ---")
    controller.set_regime("UNKNOWN")
    res = controller.get_combined_signals(market_data)
    print(f"Result: {res['TEST']} (Expected ~1.0 if weights are equal)")
    
    print("\n--- TEST 2: BULL Regime (Turbo Mode) ---")
    # Turbo: Engine 2 * 2.0 -> E1=1, E2=2. Total=3.
    # Score = (1*1 + 1*2) / 3 = 1.0 (Wait, weighted average of identical scores is same)
    # Let's change scores to see effect.
    e1.generate_signals = lambda x: {"TEST": 0.0} # E1 says Neutral
    e2.generate_signals = lambda x: {"TEST": 1.0} # E2 says Buy
    
    controller.set_regime("BULL")
    res = controller.get_combined_signals(market_data)
    # E1(0)*1 + E2(1)*2 = 2. Total Weight 3. Result = 2/3 = 0.66
    print(f"Result: {res['TEST']} (Expected ~0.666)")
    if 0.66 < res['TEST'] < 0.67:
        print("PASS: Turbo applied correctly.")
    else:
        print("FAIL: Turbo logic incorrect.")
        
    print("\n--- TEST 3: BEAR Regime (ABS Mode) ---")
    # ABS: Engine 1 * 0.0 -> E1=0, E2=1. Total=1.
    # Score = (0*0 + 1*1) / 1 = 1.0
    controller.set_regime("BEAR")
    res = controller.get_combined_signals(market_data)
    print(f"Result: {res['TEST']} (Expected 1.0)")
    if res['TEST'] == 1.0:
        print("PASS: ABS applied correctly.")
    else:
        print("FAIL: ABS logic incorrect.")

if __name__ == "__main__":
    test_dynamic_logic()
