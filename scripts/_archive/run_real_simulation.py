"""
Run Real Simulation (1-Year, Full Universe)
Uses Champion Rule Strategy on 50 stocks with 1-year real minute data.
"""

import sys
import subprocess
from pathlib import Path

# Add project root
# Force C: drive to ensure we use the edited files
project_root = Path("c:/garam/garam")
sys.path.insert(0, str(project_root))

from config import PATHS

def main():
    print("Starting Real Simulation (Champion Rule v3.0)...")
    
    script_path = project_root / "scripts" / "backtest" / "run_champion_rule_v3.py"
    
    # Arguments
    universe_file = PATHS.DATA_DIR / "real_universe.csv"
    scores_file = PATHS.DATA_DIR / "real_scores_2024.csv"
    
    # Use v3 Regime-Aware profile (Multi-Alpha Safe)
    profile = project_root / "config" / "profile_champion_v3_regime_multialpha.yaml"
    results_dir = "g:/내 드라이브/garamdata/experiments/real_sim_champion_v3_final"
    
    cmd = [
        sys.executable, str(script_path),
        "--universe-file", str(universe_file),
        "--scores-file", str(scores_file),
        "--profile", str(profile),
        "--results-dir", results_dir
    ]
    
    print(f"Command: {' '.join(cmd)}")
    
    try:
        subprocess.run(cmd, check=True)
        print("\nSimulation Completed Successfully.")
        print(f"Results saved to: {results_dir}")
    except subprocess.CalledProcessError as e:
        print(f"\nSimulation Failed with exit code {e.returncode}")
        sys.exit(e.returncode)

if __name__ == "__main__":
    main()
