import sys
import os

# Ensure GARAM root is in path
sys.path.append(os.path.abspath("C:/garam/garam"))

from garam.engine.advanced import AdvancedEngine
from garam.config import PATHS # Ensure this works or mock it if needed

def test_initialization():
    print("Testing Advanced Engine Initialization...")
    
    config = {"mode": "FIXED"}
    engine = AdvancedEngine(config)
    
    print(f"Engine Name: {engine.name}")
    print(f"HMM Model: {engine.hmm}")
    print(f"Initial Regime: {engine.regime}")
    print(f"Risk Factor: {engine.get_risk_factor()}")
    
    if engine.regime != "UNKNOWN":
        print("SUCCESS: HMM Trained and Regime Detected.")
    else:
        print("WARNING: Regime is UNKNOWN (Likely valid if no history file found).")

if __name__ == "__main__":
    try:
        test_initialization()
    except Exception as e:
        print(f"FAILED: {e}")
        import traceback
        traceback.print_exc()
