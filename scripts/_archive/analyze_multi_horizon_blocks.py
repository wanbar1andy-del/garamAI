import pickle
import pandas as pd
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from garam.research.regime.miracle_engine import Trade

def analyze_blocks(path):
    print(f"Loading results from {path}...")
    with open(path, 'rb') as f:
        data = pickle.load(f)
        
    logs = data.get('signal_logs', [])
    if not logs:
        print("No logs found.")
        return

    df = pd.DataFrame(logs)
    
    # Filter for intended entries
    entries = df[df['action'].isin(['ENTER_LONG', 'ENTER_SHORT'])]
    print(f"Total Intended Entries: {len(entries)}")
    
    executed = entries[entries['executed'] == True]
    blocked = entries[entries['executed'] == False]
    
    print(f"Executed: {len(executed)}")
    print(f"Blocked: {len(blocked)}")
    
    if len(blocked) > 0:
        print("\nBlocking Sources:")
        print(blocked['block_source'].value_counts())
        
        print("\nFilter Reasons:")
        print(blocked['filter_reason'].value_counts())
        
        print("\nRisk Reasons:")
        print(blocked['risk_reason'].value_counts())
        
        # Detailed look at blocked entries
        print("\nSample Blocked Entries:")
        print(blocked[['timestamp', 'action', 'block_source', 'filter_reason', 'risk_reason']].head(10))

if __name__ == "__main__":
    analyze_blocks("c:/garam/garam/data/backtest_multi_horizon.pkl")
