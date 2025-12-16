import sys
import pandas as pd
from pathlib import Path
from datetime import datetime
import logging
import matplotlib.pyplot as plt

# Setup Path
sys.path.append("C:\\garam")
from garam.scripts.run_live_trading import LiveTradingEngine

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Sim5Days")

def main():
    print("=== Running 5-Day Analysis (Dec 1 - Dec 5, 2025) ===")
    
    # 1. Initialize Engine
    # Uses current 'risk/account_limits.yaml' (Loose Risk)
    config_path = "C:/garam/garam/config/profile_champion_v3_weighted_400.yaml"
    state_path = "portfolio_state_sim_5days.json"
    
    if Path(state_path).exists():
        Path(state_path).unlink()
        
    engine = LiveTradingEngine(config_path, state_path=state_path)
    
    # 2. Define Period
    start_date = datetime(2025, 12, 1).date()
    end_date = datetime(2025, 12, 5).date()
    sim_dates = pd.date_range(start=start_date, end=end_date, freq="B")
    
    history = []
    
    # 3. Run Loop
    for current_date in sim_dates:
        target_date = current_date.date()
        print(f"\n>>> Simulating Date: {target_date}")
        
        try:
            engine.run_daily_cycle(target_date=target_date)
            
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
    
    initial_equity = 100_000_000
    final_equity = df_res['equity'].iloc[-1]
    pnl = final_equity - initial_equity
    pnl_pct = (pnl / initial_equity) * 100
    
    print("\n=== 5-Day Analysis Results ===")
    print(f"Initial Equity: {initial_equity:,.0f}")
    print(f"Final Equity:   {final_equity:,.0f}")
    print(f"PnL:            {pnl:,.0f} KRW ({pnl_pct:.2f}%)")
    
    # Save CSV
    df_res.to_csv("reports/simulation_5days_equity.csv")
    
    # Generate Markdown Report
    report = f"""# Recent 5-Day Profit Analysis (Dec 1 - Dec 5)

## 1. Summary
- **Period**: 2025-12-01 ~ 2025-12-05
- **Configuration**: Loose Risk (Daily -10%, Pos 50%)
- **Result**:
    - **Initial**: {initial_equity:,.0f} KRW
    - **Final**: {final_equity:,.0f} KRW
    - **PnL**: **{pnl:+,.0f} KRW ({pnl_pct:+.2f}%)**

## 2. Daily Breakdown
| Date | Equity | Daily PnL |
| :--- | :--- | :--- |
"""
    prev_eq = initial_equity
    for date, row in df_res.iterrows():
        curr_eq = row['equity']
        daily_pnl = curr_eq - prev_eq
        daily_pct = (daily_pnl / prev_eq) * 100
        report += f"| {date.date()} | {curr_eq:,.0f} | {daily_pnl:+,.0f} ({daily_pct:+.2f}%) |\n"
        prev_eq = curr_eq
        
    with open("reports/analysis_5days.md", "w", encoding="utf-8") as f:
        f.write(report)
    print("Saved report to reports/analysis_5days.md")

if __name__ == "__main__":
    main()
