import json
import pandas as pd
from pathlib import Path
from datetime import datetime
import sys
sys.path.append("C:\\garam")
from garam.config import PATHS

def sync_state_to_signals():
    print("Syncing Fixed State to signals_live.json...")
    
    # 1. Load Fixed State
    state_path = "portfolio_state.json"
    if not Path(state_path).exists():
        print("State file not found!")
        return
        
    with open(state_path, 'r', encoding='utf-8') as f:
        state = json.load(f)
        
    equity = state.get('equity')
    cash = state.get('cash')
    positions = state.get('positions', {})
    
    print(f"Loaded Fixed State: Equity={equity:,.0f}")
    
    # 2. Load Signals File
    signals_path = PATHS.STRATEGY_SIGNALS_LIVE
    if not signals_path.exists():
        print("Signals file not found!")
        return
        
    # Read as text first to avoid JSON error if it still has NaNs (though we want to overwrite it)
    try:
        with open(signals_path, 'r', encoding='utf-8') as f:
            # We try to load to preserve 'orders' and 'regime'
            import re
            content = f.read()
            content = re.sub(r':\s*NaN', ': null', content, flags=re.IGNORECASE)
            signals = json.loads(content)
    except Exception as e:
        print(f"Error reading signals: {e}. Creating new structure.")
        signals = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "generated_at": str(datetime.now()),
            "regime": "UNKNOWN",
            "orders": []
        }
        
    # 3. Update Signals with State Data
    signals['equity'] = equity
    signals['cash'] = cash
    
    # Update Holdings structure
    holdings = {}
    for sym, pos in positions.items():
        qty = pos['qty']
        entry_price = pos['entry_price']
        current_price = pos.get('current_price', entry_price)
        val = pos.get('value', qty * current_price)
        
        pnl = val - (qty * entry_price)
        pnl_pct = (pnl / (qty * entry_price)) * 100 if qty > 0 else 0
        
        holdings[sym] = {
            "name": sym, # Should lookup name if possible, but sym is fallback
            "qty": qty,
            "entry_price": entry_price,
            "current_price": current_price,
            "entry_date": pos.get('entry_date', ''),
            "value": val,
            "pnl": pnl,
            "pnl_pct": pnl_pct
        }
        
    signals['holdings'] = holdings
    
    # 4. Save
    with open(signals_path, 'w', encoding='utf-8') as f:
        json.dump(signals, f, indent=4)
        
    print(f"Updated signals_live.json with valid Equity={equity:,.0f}")

if __name__ == "__main__":
    sync_state_to_signals()
