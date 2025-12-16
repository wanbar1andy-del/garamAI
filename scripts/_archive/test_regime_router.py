"""
Test Regime Router
Verifies that RegimeRouter correctly loads the matrix and returns strategies.
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root.parent))

from garam.live.regime_router import RegimeRouter

def test_router():
    router = RegimeRouter()
    print(f"Loaded config from: {router.config_path}")
    print(f"Config keys: {list(router.config.keys())}")
    
    # Test GREEN
    router.current_regime = "GREEN"
    strategy = router.get_active_strategy()
    print(f"\n[GREEN] Strategy: {strategy['strategy_id']}, Params: {strategy['params']}")
    
    # Test RED
    router.current_regime = "RED"
    strategy = router.get_active_strategy()
    print(f"\n[RED] Strategy: {strategy['strategy_id']}, Params: {strategy['params']}")
    
    # Test YELLOW
    router.current_regime = "YELLOW"
    strategy = router.get_active_strategy()
    print(f"\n[YELLOW] Strategy: {strategy['strategy_id']}, Params: {strategy['params']}")

if __name__ == "__main__":
    test_router()
