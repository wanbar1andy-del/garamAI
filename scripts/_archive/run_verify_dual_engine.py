import sys
import pandas as pd
from pathlib import Path
from datetime import datetime
import logging

# Setup Path
# Adjust this depending on where the script is run relative to package
sys.path.append("C:\\garam")

from garam.scripts.run_live_trading import LiveTradingEngine

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VerifyDualEngine")

def main():
    print("=== Verifying Dual Engine Architecture (Short Test) ===")
    
    # 1. Initialize Engine
    config_path = "C:/garam/garam/config/profile_champion_v2_1_restored.yaml"
    state_path = "portfolio_state_verify.json"
    
    if Path(state_path).exists():
        Path(state_path).unlink()
        
    try:
        engine = LiveTradingEngine(config_path, state_path=state_path)
        print("Engine Initialized Successfully.")
    except Exception as e:
        print(f"Engine Initialization Failed: {e}")
        return

    # 2. Define Short Period (1 Week)
    start_date = datetime(2025, 1, 6).date()
    end_date = datetime(2025, 1, 10).date() # 5 days
    
    sim_dates = pd.date_range(start=start_date, end=end_date, freq="B")
    
    print(f"Running Simulation for {len(sim_dates)} days...")
    
    history = []
    
    for current_date in sim_dates:
        target_date = current_date.date()
        print(f"> Processing {target_date}...")
        
        try:
            # This calls the new HybridController logic
            engine.run_daily_cycle(target_date=target_date)
            
            # Check if Signals/Orders generated
            state = engine.state
            print(f"  Positions: {len(state.get('positions', {}))}")
            print(f"  Equity: {state.get('equity', 0):,.0f}")
            
            history.append(state)
            
        except Exception as e:
            logger.error(f"CRASH on {target_date}: {e}", exc_info=True)
            break
            
    print("=== Verification Completed ===")
    if history:
        final_eq = history[-1]['equity']
        print(f"Final Equity: {final_eq:,.0f}")
    else:
        print("No successful cycles.")

if __name__ == "__main__":
    main()
