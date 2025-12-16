import pickle
import pandas as pd
import numpy as np
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def analyze_coordination_logs(path):
    print(f"Loading results from {path}...")
    with open(path, 'rb') as f:
        data = pickle.load(f)
    
    signal_logs = data.get('signal_logs', [])
    
    if not signal_logs:
        print("No signal logs found.")
        return
    
    df = pd.DataFrame(signal_logs)
    print(f"\nTotal Signal Events: {len(df)}")
    print(f"Available columns: {df.columns.tolist()}")
    print(f"\nSample data (first 3 rows):")
    print(df.head(3))
    
    if len(df) == 0:
        print("Empty signal logs.")
        return
    
    # 1. Action Distribution
    print("\n=== Action Distribution ===")
    print(df['action'].value_counts())
    print(f"\nWAIT Frequency: {(df['action'] == 'WAIT').sum() / len(df):.2%}")
    
    # 2. Signal Statistics
    print("\n=== Signal Statistics ===")
    print("fs (Short Horizon):")
    print(df['fs'].describe())
    print("\nfm (Mid Horizon):")
    print(df['fm'].describe())
    
    # 3. Condition Analysis for FLAT state with WAIT
    flat_wait = df[(df['state'] == 'FLAT') & (df['action'] == 'WAIT')]
    print(f"\n=== FLAT -> WAIT Cases ({len(flat_wait)} events) ===")
    if len(flat_wait) > 0:
        print("fs range:")
        print(flat_wait['fs'].describe())
        print("\nfm range:")
        print(flat_wait['fm'].describe())
        
        # Check how many would satisfy relaxed conditions
        relaxed_entry = flat_wait[(flat_wait['fs'] > 0.3) & (flat_wait['fm'] >= -0.5)]
        print(f"\nIf we relax to fs > 0.3 & fm >= -0.5: {len(relaxed_entry)} would trigger")
    
    # 4. Rule Trigger Analysis (if logged)
    if 'rule_name' in df.columns:
        print("\n=== Rule Trigger Count ===")
        rule_counts = df[df['rule_name'].notna()]['rule_name'].value_counts()
        print(rule_counts)
    
    # 5. Execution vs. Signal
    print("\n=== Execution Analysis ===")
    if 'executed' in df.columns:
        print(f"Signals with action != WAIT: {(df['action'] != 'WAIT').sum()}")
        print(f"Actually executed: {df['executed'].sum()}")
        
        not_executed = df[(df['action'] != 'WAIT') & (~df['executed'])]
        if len(not_executed) > 0:
            print(f"\nBlocked signals ({len(not_executed)}):")
            if 'block_source' in df.columns:
                print(not_executed['block_source'].value_counts())

if __name__ == "__main__":
    analyze_coordination_logs("c:/garam/garam/data/swing_best_results.pkl")
