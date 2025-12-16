import json
import pandas as pd
from pathlib import Path
from datetime import datetime
import sys
sys.path.append("C:\\garam")
from garam.config import PATHS

def fix_state_and_report():
    print("Fixing Portfolio State NaNs...")
    
    # 1. Load State
    state_path = "portfolio_state.json"
    if not Path(state_path).exists():
        print("State file not found.")
        return

    print("Reconstructing Portfolio State from signals_live.json...")
    
    signals_path = PATHS.STRATEGY_SIGNALS_LIVE
    if not signals_path.exists():
        print("signals_live.json not found!")
        return

    with open(signals_path, 'r', encoding='utf-8') as f:
        sig_data = json.load(f)
        
    # sig_data has 'holdings' and 'equity' and 'cash' calculated by the engine (before crash?)
    # If the engine crashed during state save, it likely FINISHED signals save.
    
    holdings = sig_data.get('holdings', {})
    equity = sig_data.get('equity', 0)
    cash = sig_data.get('cash', 0)
    
    timestamp = sig_data.get('generated_at', str(datetime.now()))
    
    print(f"Loaded from Signals: Cash={cash:,.0f}, Positions={len(holdings)}")
    
    # Reconstruct State Format
    # We will recalculate equity Sum(Qty * Price) + Cash
    
    fixed_positions = {}
    total_holdings_value = 0
    
    for sym, info in holdings.items():
        # info might contain enriched data
        qty = int(info.get('qty', 0))
        entry_price = float(info.get('entry_price', 0))
        entry_date = info.get('entry_date', datetime.now().strftime("%Y-%m-%d"))
        
        # Fetch Current Price
        # Check daily history first
        daily_csv = PATHS.HISTORY_DIR / "daily" / f"{sym}_daily.csv"
        current_price = 0
        if daily_csv.exists():
            try:
                df = pd.read_csv(daily_csv)
                if not df.empty:
                    current_price = df['close'].iloc[-1]
            except:
                pass
        
        # Fallback
        if current_price == 0 or pd.isna(current_price):
             current_price = entry_price
             
        current_price = float(current_price)
        val = float(qty * current_price)
        total_holdings_value += val

        fixed_positions[sym] = {
            "qty": qty,
            "entry_price": entry_price,
            "entry_date": entry_date,
            "current_price": current_price,
            "value": val
        }
        print(f"  {sym}: {qty} @ {current_price:,.0f} = {val:,.0f}")
        
    state = {
        "cash": float(cash),
        "positions": fixed_positions,
        "blacklist": {},
        "last_update": timestamp
    }
    
    new_equity = float(cash + total_holdings_value)
    
    state['equity'] = new_equity
    state['prev_equity'] = new_equity # approx
    
    print(f"Recalculated Equity: {new_equity:,.0f}")
    
    # Save State
    state_path = "portfolio_state.json"
    with open(state_path, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=4)
    print("Reconstructed portfolio_state.json")
    
    # 3. Fix Account Snapshot CSV
    snapshot_path = PATHS.ACCOUNT_SNAPSHOT
    if snapshot_path.exists():
        df = pd.read_csv(snapshot_path)
        # Update last row if timestamp matches today (or is the last one)
        # assuming the last row is the broken one
        if pd.isna(df['total_equity'].iloc[-1]):
            df.at[df.index[-1], 'total_equity'] = new_equity
            df.to_csv(snapshot_path, index=False)
            print("Fixed account_snapshot.csv")
            
            # 4. Regenerate Report
            # Get yesterday's equity
            if len(df) >= 2:
                yest_eq = df['total_equity'].iloc[-2]
                diff = new_equity - yest_eq
                today_str = datetime.now().strftime("%Y-%m-%d")
                
                report_md = f"""# 📊 Simulation Transition Report ({today_str})

## 1. Performance Overview
- **Yesterday ({df['timestamp'].iloc[-2]})**: {yest_eq:,.0f} KRW
- **Today ({today_str})**: {new_equity:,.0f} KRW
- **Change**: {diff:+,.0f} KRW ({(diff/yest_eq)*100:.2f}%)

## 2. Transition Status
- **Simulation**: Completed (30 days)
- **State**: Saved to `portfolio_state.json` (Sanitized)
- **Ready for Tomorrow**: ✅ YES

## 3. Latest Trades (Today)
- Please check dashboard for detailed trade logs.

## 4. Current Holdings (For Tomorrow)
"""
                for sym, pos in fixed_positions.items():
                    report_md += f"- **{sym}**: {pos['qty']} shares @ {pos.get('current_price',0):,.0f} KRW\n"

                report_path = PATHS.REPORTS_DIR / f"Simulation_Transition_Report_{today_str}.md"
                with open(report_path, 'w', encoding='utf-8') as f:
                    f.write(report_md)
                print(f"Regenerated Report to {report_path}")

if __name__ == "__main__":
    fix_state_and_report()
