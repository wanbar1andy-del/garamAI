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
logger = logging.getLogger("Sim1Year")

def main():
    print("=== Running 1-Year Backtest (Dec 2024 - Dec 2025) ===")
    
    # 1. Initialize Engine with Simulation State
    # Config: Champion V3 Weighted (Finalized Live Profile)
    config_path = "C:/garam/garam/config/profile_champion_v3_weighted_400.yaml"
    state_path = "portfolio_state_sim_1year.json"
    
    # Remove existing state if any
    if Path(state_path).exists():
        Path(state_path).unlink()
        
    engine = LiveTradingEngine(config_path, state_path=state_path)
    
    # 2. Define Period
    start_date = datetime(2024, 12, 5).date()
    end_date = datetime(2025, 12, 5).date()
    
    sim_dates = pd.date_range(start=start_date, end=end_date, freq="B") # Business days
    
    history = []
    daily_log = []  # NEW: For adaptive turbo research
    prev_equity = 100_000_000  # Track previous equity for daily returns
    
    # 3. Run Loop
    for current_date in sim_dates:
        target_date = current_date.date()
        # print(f"\n>>> Simulating Date: {target_date}") # Reduce spam
        if current_date.day == 1:
            print(f">>> Simulating Month: {current_date.strftime('%Y-%m')}")
        
        try:
            engine.run_daily_cycle(target_date=target_date)
            
            # Capture State
            current_equity = engine.state.get('equity', prev_equity)
            state_snapshot = {
                "date": str(target_date),
                "equity": current_equity,
                "cash": engine.state.get('cash'),
                "positions_count": len(engine.state.get('positions', {}))
            }
            history.append(state_snapshot)
            
            # NEW: Detailed daily log for research
            daily_return = (current_equity - prev_equity) / prev_equity if prev_equity > 0 else 0.0
            
            # Extract controller metadata (if available)
            try:
                # Try to get regime from engine's last detection
                regime = getattr(engine, 'current_regime', 'UNKNOWN')
                
                # Try to get controller mode
                controller_meta = getattr(engine.controller, 'last_mode', 'UNKNOWN')
                
                # Try to get final_score (may need to access engine2's last analysis)
                final_score = None
                if hasattr(engine.controller, 'last_directives'):
                    final_score = engine.controller.last_directives.get('score', None)
                
            except Exception:
                regime = 'UNKNOWN'
                controller_meta = 'UNKNOWN'
                final_score = None
            
            daily_log.append({
                'date': str(target_date),
                'equity': float(current_equity),
                'daily_return': float(daily_return),
                'regime': regime,
                'mode': controller_meta,
                'final_score': float(final_score) if final_score is not None else None,
                'positions_count': len(engine.state.get('positions', {}))
            })
            
            prev_equity = current_equity
            
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
    
    # Calculate MDD
    rolling_max = df_res['equity'].cummax()
    drawdown = (df_res['equity'] - rolling_max) / rolling_max
    mdd = drawdown.min() * 100
    
    print("\n=== Simulation Results ===")
    print(f"Initial Equity: {initial_equity:,.0f}")
    print(f"Final Equity:   {final_equity:,.0f}")
    print(f"PnL:            {pnl:,.0f} KRW ({pnl_pct:.2f}%)")
    print(f"MDD:            {mdd:.2f}%")
    
    # Save CSV
    df_res.to_csv("reports/simulation_1year_equity.csv")
    
    # NEW: Save daily log for research
    if daily_log:
        Path("logs").mkdir(exist_ok=True)
        df_daily = pd.DataFrame(daily_log)
        df_daily.to_csv("logs/daily_backtest_log.csv", index=False)
        print(f"Saved daily log to logs/daily_backtest_log.csv ({len(daily_log)} days)")
    
    # Plot
    try:
        plt.figure(figsize=(12, 6))
        plt.plot(df_res.index, df_res['equity'], label='Equity')
        plt.title(f"1-Year Backtest (PnL: {pnl_pct:.2f}%, MDD: {mdd:.2f}%)")
        plt.xlabel("Date")
        plt.ylabel("Equity (KRW)")
        plt.grid(True)
        plt.legend()
        plt.savefig("reports/simulation_1year_result.png")
        print("Saved graph to reports/simulation_1year_result.png")
    except Exception as plotting_error:
        print(f"Plotting failed: {plotting_error}")

if __name__ == "__main__":
    main()
