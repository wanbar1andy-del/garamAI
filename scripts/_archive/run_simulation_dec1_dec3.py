import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import logging

# Add project root to path
project_root = Path("c:/garam/garam")
sys.path.append(str(project_root.parent))

from garam.scripts.run_live_trading import LiveTradingEngine

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SimulationRunner")

def run_simulation():
    # Dates to simulate
    # We want to simulate the "Action" for Dec 2, Dec 3, Dec 4.
    # This corresponds to running the engine on the evening of Dec 1, Dec 2, Dec 3.
    # Dec 1 (Sun) -> Action for Dec 2 (Mon)
    # Dec 2 (Mon) -> Action for Dec 3 (Tue)
    # Dec 3 (Tue) -> Action for Dec 4 (Wed)
    
    dates = [
        "2025-12-02", # Monday
        "2025-12-03", # Tuesday
        "2025-12-04"  # Wednesday
    ]
    
    # Initialize Engine
    # We use a separate state file for this simulation to avoid messing up the "real" state
    sim_state_path = "portfolio_state_sim_dec1_3.json"
    # Delete if exists to start fresh
    if Path(sim_state_path).exists():
        Path(sim_state_path).unlink()
        
    engine = LiveTradingEngine(
        config_path="config/profile_champion_v3_weighted_400.yaml",
        state_path=sim_state_path
    )
    
    # Override Data Loading to ensure we have fresh data
    # (Already done by fetcher, engine loads from disk)
    
    print("=== Starting Simulation for Dec 1-3 ===")
    
    for date_str in dates:
        target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        print(f"\n>>> Running Cycle for Target Date: {target_date}")
        
        # Run Cycle
        # Note: We need to ensure the engine uses data ONLY up to target_date - 1
        # The current engine loads ALL data.
        # We need to monkey-patch or modify the engine to slice data?
        # Or just trust that the engine uses `target_date` to slice?
        # Wait, I didn't implement slicing in `run_live_trading.py` yet!
        # I need to fix `run_live_trading.py` first to slice data based on `target_date`.
        
        # Let's assume I will fix `run_live_trading.py` in the next step.
        engine.run_daily_cycle(target_date=target_date)
        
    print("\n=== Simulation Completed ===")
    
    # Print Final State
    import json
    with open(sim_state_path, 'r') as f:
        state = json.load(f)
        print(json.dumps(state, indent=4))

if __name__ == "__main__":
    run_simulation()
