import pandas as pd
import yaml
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from config import PATHS

def build_playbook():
    print("Building Hybrid v3 Playbook...")
    
    # 1. Load PnL Analysis
    pnl_file = PATHS.BASE_DIR / "results" / "pnl_by_regime_strategy.csv"
    if not pnl_file.exists():
        print(f"Error: {pnl_file} not found.")
        return
        
    df = pd.read_csv(pnl_file)
    
    # 2. Define Regime Mapping Logic
    # We want to select the best strategy for each regime.
    # Criteria: Max Total PnL (or Win Rate / Avg R)
    # For now, simple Max Total PnL.
    
    # Filter out UNKNOWN
    df = df[df['regime_id'] != 'UNKNOWN']
    
    best_strategies = {}
    
    # Group by regime and find max pnl
    # We need to pivot or iterate
    regimes = df['regime_id'].unique()
    
    for regime in regimes:
        regime_data = df[df['regime_id'] == regime]
        best_row = regime_data.loc[regime_data['total_pnl'].idxmax()]
        best_strategies[regime] = best_row['strategy']
        print(f"Regime {regime}: Best = {best_row['strategy']} (PnL: {best_row['total_pnl']:,.0f})")
        
    # 3. Construct Playbook YAML
    # We need to map Strategy Name (Pure_v2/v3) to Module Config
    # Pure_v2 -> M_RANGE_V2 (assuming)
    # Pure_v3 -> M_ATTACK_V3 (assuming)
    
    strategy_to_module = {
        "Pure_v2": {
            "module": "M_RANGE_V2",
            "intensity": 0.5, # Default
            "params": {
                "mode": "Range",
                "target_R": 2.0,
                "stop_R": 1.0,
                "time_stop_min": 30
            }
        },
        "Pure_v3": {
            "module": "M_ATTACK_V3",
            "intensity": 0.8, # Aggressive
            "params": {
                "mode": "Attack",
                "target_R": 3.0,
                "stop_R": 1.0,
                "time_stop_min": 60
            }
        }
    }
    
    playbook = {
        "version": "3.0",
        "description": "DGE Hybrid v3.0 (Trend-First) - Generated from PnL Analysis",
        "regimes": {}
    }
    
    # Fill Regimes
    # We need to cover all 7 regimes. If missing in data, use default (Pure_v3 for Trend, v2 for Range)
    all_regimes = [
        "R1_STRONG_UP_BREAKOUT", "R2_STRONG_UP_GRIND", 
        "R3_SIDEWAYS_RANGE_LOWVOL", "R4_SIDEWAYS_RANGE_HIGHVOL",
        "R5_WEAK_DOWN_DRIFT", "R6_STRONG_DOWN_CRASH", "R7_STRONG_DOWN_REVERSAL"
    ]
    
    for r in all_regimes:
        strategy = best_strategies.get(r)
        
        # Default Logic if no data
        if not strategy:
            if "UP" in r or "DOWN" in r:
                strategy = "Pure_v3" # Trend default
            else:
                strategy = "Pure_v2" # Range default
            print(f"Regime {r}: No data, using default {strategy}")
            
        module_config = strategy_to_module[strategy]
        
        playbook["regimes"][r] = {
            "module": module_config["module"],
            "intensity": module_config["intensity"],
            "params": module_config["params"]
        }
        
    # 4. Save to YAML
    output_path = PATHS.CONFIG_DIR / "playbook_hybrid_v3.yaml"
    with open(output_path, 'w') as f:
        yaml.dump(playbook, f, sort_keys=False)
        
    print(f"Playbook saved to {output_path}")

if __name__ == "__main__":
    build_playbook()
