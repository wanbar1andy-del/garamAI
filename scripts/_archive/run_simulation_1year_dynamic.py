import sys
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import logging
import json
import matplotlib.pyplot as plt

# Setup Path
sys.path.append("C:\\garam")

from garam.scripts.run_live_trading import LiveTradingEngine
from garam.config import PATHS

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Sim1Year")

def main():
    print(f"=== Running Dynamic 1-Year Simulation (Target: {datetime.now().date()}) ===")
    
    # 1. Initialize Engine
    config_path = PATHS.CONFIG_DIR / "profile_champion_v3_weighted_400.yaml"
    state_path = "portfolio_state.json" 
    
    # Backup existing state
    if Path(state_path).exists():
        import shutil
        backup_path = f"{state_path}.bak_pre_1year"
        shutil.copy(state_path, backup_path)
        print(f"Backed up existing state to {backup_path}")
        Path(state_path).unlink()
        
    engine = LiveTradingEngine(str(config_path), state_path=state_path)
    
    # 2. Define Period (Last 365 Days)
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=365)
    
    sim_dates = pd.date_range(start=start_date, end=end_date, freq="B")
    print(f"Simulating from {sim_dates[0].date()} to {sim_dates[-1].date()} ({len(sim_dates)} business days)")
    
    history = []
    all_trades = []
    
    # 3. Run Loop
    for i, current_date in enumerate(sim_dates):
        target_date = current_date.date()
        print(f"\n>>> [{i+1}/{len(sim_dates)}] Simulating Date: {target_date}")
        
        try:
            # Run Daily Cycle
            engine.run_daily_cycle(target_date=target_date)
            
            # --- FIX: Ensure Equity is not NaN ---
            # If engine produces NaN equity, recalculate it manually
            equity = engine.state.get('equity')
            cash = engine.state.get('cash', 0)
            
            if pd.isna(equity) or equity is None:
                # Recalculate based on positions
                positions = engine.state.get('positions', {})
                holdings_val = 0
                for sym, pos in positions.items():
                    qty = pos.get('qty', 0)
                    # Use current price from engine if available (it might be in 'current_price' enriched by run_live_trading)
                    # Or check engine's internal price dict if we could access it.
                    # run_live_trading *should* have enriched 'positions' with 'current_price'.
                    
                    price = pos.get('current_price', pos.get('entry_price', 0))
                    holdings_val += qty * price
                
                equity = cash + holdings_val
                engine.state['equity'] = equity # Patch engine state
            
            # Capture Equity State
            history.append({
                "timestamp": str(target_date),
                "total_equity": float(equity),
                "cash": float(cash),
            })
            
            # Capture Trades from signals file (since engine overwrites it daily)
            try:
                if PATHS.STRATEGY_SIGNALS_LIVE.exists():
                    with open(PATHS.STRATEGY_SIGNALS_LIVE, 'r', encoding='utf-8') as f:
                        sig_data = json.load(f)
                    
                    # Check signal date matches target_date
                    if sig_data.get('date') == str(target_date):
                        for order in sig_data.get('orders', []):
                            all_trades.append({
                                "timestamp": str(target_date) + " 15:30:00",
                                "symbol": order['symbol'],
                                "name": order.get('name', order['symbol']),
                                "type": order['action'],
                                "price": order.get('price', 0),
                                "qty": order.get('qty', 0),
                                "pnl": 0
                            })
            except Exception as e:
                pass # Squelch read errors
                
            print(f"Equity: {equity:,.0f}")
            
        except Exception as e:
            logger.error(f"Error on {target_date}: {e}")

    # 4. Save Data for Dashboard
    # Equity Curve
    df_equity = pd.DataFrame(history)
    if not df_equity.empty:
        PATHS.LIVE_DIR.mkdir(parents=True, exist_ok=True)
        df_equity.to_csv(PATHS.ACCOUNT_SNAPSHOT, index=False)
        print(f"Saved Equity History to {PATHS.ACCOUNT_SNAPSHOT}")
        
        # Chart
        plt.figure(figsize=(10, 6))
        plt.plot(pd.to_datetime(df_equity['timestamp']), df_equity['total_equity'])
        plt.title("1-Year Simulation Equity Curve")
        plt.grid(True)
        plt.savefig(PATHS.REPORTS_DIR / "simulation_1year_equity.png")

    # Trades
    df_trades = pd.DataFrame(all_trades)
    if not df_trades.empty:
        df_trades.to_csv(PATHS.LIVE_TRADES, index=False)
        print(f"Saved Trade History to {PATHS.LIVE_TRADES}")

    # 5. Final State Sync
    # Ensure final state file is valid
    final_state_path = "portfolio_state.json"
    if Path(final_state_path).exists():
        # Re-read and ensure no NaNs
        try:
            with open(final_state_path, 'r', encoding='utf-8') as f:
                state = json.load(f)
        except:
             # If simple load fails, use regex fix manually or just rely on what we have in 'engine.state'
             state = engine.state
        
        # Force equity to be valid float
        if pd.isna(state.get('equity')):
             state['equity'] = history[-1]['total_equity'] if history else 100000000
             
        with open(final_state_path, 'w', encoding='utf-8') as f:
             # Ensure native types
             def convert(o):
                 if isinstance(o, np.int64): return int(o)
                 if isinstance(o, np.float64): return float(o)
                 return o
             json.dump(state, f, indent=4, default=convert)
        print("Final portfolio_state.json saved.")

    # 6. Run Analysis Automatically
    import subprocess
    print("\n>>> Triggering Performance Analysis...")
    subprocess.run(["python", "scripts/analyze_simulation_performance.py"], check=True)

if __name__ == "__main__":
    main()
