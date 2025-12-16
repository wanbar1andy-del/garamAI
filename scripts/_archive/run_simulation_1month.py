import sys
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import logging
import json
import matplotlib.pyplot as plt

# Setup Path
sys.path.append("C:\\garam")

from garam.scripts.run_live_trading import LiveTradingEngine

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Sim1Month")

def main():
    print("=== Running 1-Month Backtest (Nov 5 - Dec 5, 2025) ===")
    
    # 1. Initialize Engine with Simulation State
    config_path = "C:/garam/garam/config/profile_champion_v3_weighted_400.yaml"
    state_path = "portfolio_state_sim_1month.json"
    
    # Remove existing state if any
    if Path(state_path).exists():
        Path(state_path).unlink()
        
    engine = LiveTradingEngine(config_path, state_path=state_path)
    
    # 2. Define Period
    start_date = datetime(2025, 11, 5).date()
    end_date = datetime(2025, 12, 5).date()
    
    sim_dates = pd.date_range(start=start_date, end=end_date, freq="B") # Business days
    
    history = []
    
    # 3. Run Loop
    for current_date in sim_dates:
        target_date = current_date.date()
        print(f"\n>>> Simulating Date: {target_date}")
        
        # We want to run the cycle FOR this target date.
        # run_daily_cycle(target_date) means "Make decisions for target_date using data up to target_date-1"
        # So if we want to simulate trading ON Nov 5, we need data up to Nov 4.
        
        try:
            engine.run_daily_cycle(target_date=target_date)
            
            # Capture State
            state_snapshot = {
                "date": str(target_date),
                "equity": engine.state.get('equity'),
                "cash": engine.state.get('cash'),
                "positions_count": len(engine.state.get('positions', {}))
            }
            history.append(state_snapshot)
            print(f"Equity: {engine.state.get('equity'):,.0f}")
            
        except Exception as e:
            logger.error(f"Error on {target_date}: {e}")

    # 4. Generate Report
    if not history:
        print("No history generated.")
        return

    df_res = pd.DataFrame(history)
    df_res['date'] = pd.to_datetime(df_res['date'])
    df_res.set_index('date', inplace=True)
    
    initial_equity = 100_000_000 # Default
    final_equity = df_res['equity'].iloc[-1]
    pnl = final_equity - initial_equity
    pnl_pct = (pnl / initial_equity) * 100
    
    print("\n=== Simulation Results ===")
    print(f"Initial Equity: {initial_equity:,.0f}")
    print(f"Final Equity:   {final_equity:,.0f}")
    print(f"PnL:            {pnl:,.0f} KRW ({pnl_pct:.2f}%)")
    
    # Save CSV
    df_res.to_csv("reports/simulation_1month_equity.csv")
    
    # Plot
    plt.figure(figsize=(10, 6))
    plt.plot(df_res.index, df_res['equity'], label='Equity')
    plt.title(f"1-Month Backtest (PnL: {pnl_pct:.2f}%)")
    plt.xlabel("Date")
    plt.ylabel("Equity (KRW)")
    plt.grid(True)
    plt.legend()
    plt.savefig("reports/simulation_1month_active_risk.png")
    print("Saved graph to reports/simulation_1month_active_risk.png")

if __name__ == "__main__":
    main()
