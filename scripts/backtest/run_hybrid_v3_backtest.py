import sys
from pathlib import Path
import pandas as pd
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from config import PATHS
from scripts.backtest.run_generic_backtest import run_backtest
from strategies.kr_intraday.dge_hybrid_v3 import DGEHybridStrategyV3

def run():
    print(">>> Running Backtest: Hybrid_v3 (Trend-First)")
    
    # Ensure playbook exists
    playbook_path = PATHS.CONFIG_DIR / "playbook_hybrid_v3.yaml"
    if not playbook_path.exists():
        print(f"Error: Playbook {playbook_path} not found.")
        print("Please run scripts/analysis/build_playbook_hybrid_v3_from_pnl.py first.")
        return
        
    config = {
        "strategy_name": "Hybrid_v3",
        "playbook_path": playbook_path,
        "orb_minutes": 30,
        "use_kelly": False, # Fixed risk for verification
        "base_risk": 0.015,
        "start_date": "2025-09-26",
        "end_date": "2025-11-28",
        "symbols": [
            "005930", "000660", "005380", "005490", "035420", 
            "000270", "051910", "068270", "105560", "006400"
        ]
    }
    
    # Run Generic Backtest with Hybrid v3 Class
    run_backtest(
        strategy_class=DGEHybridStrategyV3,
        config_dict=config,
        strategy_name="Hybrid_v3"
    )

if __name__ == "__main__":
    run()
