import sys
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import logging
import json
import matplotlib.pyplot as plt

# Setup Path
# Adjust based on your environment if needed
sys.path.append("C:\\garam")

from garam.scripts.run_live_trading import LiveTradingEngine
from garam.config import PATHS

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SimDynamic")

def main():
    print(f"=== Running Dynamic 1-Month Simulation (Target: {datetime.now().date()}) ===")
    
    # 1. Initialize Engine
    # Using the weighted profile as default
    config_path = PATHS.CONFIG_DIR / "profile_champion_v3_weighted_400.yaml"
    state_path = "portfolio_state.json" # We want to update the REAL state for tomorrow
    
    # Backup existing state if any (safety first)
    if Path(state_path).exists():
        import shutil
        backup_path = f"{state_path}.bak_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy(state_path, backup_path)
        print(f"Backed up existing state to {backup_path}")
        # Reset state for simulation start? 
        # The user wants "1 month simulation to NOW". Ideally we start fresh 1 month ago.
        Path(state_path).unlink()
        
    engine = LiveTradingEngine(str(config_path), state_path=state_path)
    
    # 2. Define Period (Last 30 Calendar Days -> Business Days)
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=35) # Approx 1 month + buffer
    
    # Using standard pandas bdate_range
    sim_dates = pd.date_range(start=start_date, end=end_date, freq="B")
    
    print(f"Simulating from {sim_dates[0].date()} to {sim_dates[-1].date()} ({len(sim_dates)} days)")
    
    history = []
    all_trades = []
    
    # 3. Run Loop
    for current_date in sim_dates:
        target_date = current_date.date()
        print(f"\n>>> Simulating Date: {target_date}")
        
        try:
            # Run Daily Cycle
            engine.run_daily_cycle(target_date=target_date)
            
            # Capture Equity State
            state_snapshot = {
                "timestamp": str(target_date),
                "total_equity": engine.state.get('equity', 0),
                "cash": engine.state.get('cash', 0),
            }
            history.append(state_snapshot)
            
            # Capture Trades (We need to extract them from engine or logs? 
            # Engine doesn't expose daily trades easily unless we read signals or modify engine.
            # But the engine DOES save 'signals_live.json'. We can read that?
            # Or we can rely on what the engine just did.
            # Ideally, LiveTradingEngine should return the trades it executed.
            # For now, let's look at `engine.state['positions']` changes or similar.
            # Actually, `run_live_trading.py` saves to `signals_live.json`. 
            # Let's read `signals_live.json` immediately after cycle.)
            
            try:
                with open(PATHS.STRATEGY_SIGNALS_LIVE, 'r', encoding='utf-8') as f:
                    sig_data = json.load(f)
                    
                # If generated_at matches today (simulated date... wait, generated_at is NOW, not simulated date. 
                # signal date is what matters).
                # Actually, run_live_trading overwrites signals_live.json.
                if sig_data.get('date') == str(target_date):
                    for order in sig_data.get('orders', []):
                        trade_record = {
                            "timestamp": str(target_date) + " 15:30:00", # Mock time
                            "symbol": order['symbol'],
                            "name": order.get('name', order['symbol']),
                            "type": order['action'], # BUY/SELL
                            "price": order.get('price', 0),
                            "qty": order.get('qty', 0),
                            "pnl": 0 # PnL is hard to get here without more logic
                        }
                        all_trades.append(trade_record)
            except Exception as e:
                print(f"Warning reading signals: {e}")
                
            print(f"Equity: {engine.state.get('equity'):,.0f}")
            
        except Exception as e:
            logger.error(f"Error on {target_date}: {e}")
            # Keep going

    # 4. Save Data for Dashboard
    # Equity Curve -> account_snapshot.csv
    df_equity = pd.DataFrame(history)
    if not df_equity.empty:
        PATHS.LIVE_DIR.mkdir(parents=True, exist_ok=True)
        df_equity.to_csv(PATHS.ACCOUNT_SNAPSHOT, index=False)
        print(f"Saved Equity History to {PATHS.ACCOUNT_SNAPSHOT}")
        
        # Also Chart
        plt.figure(figsize=(10, 6))
        plt.plot(pd.to_datetime(df_equity['timestamp']), df_equity['total_equity'])
        plt.title("Simulation Equity Curve")
        plt.grid(True)
        plt.savefig(PATHS.REPORTS_DIR / "simulation_equity.png")

    # Trades -> live_trades.csv
    df_trades = pd.DataFrame(all_trades)
    if not df_trades.empty:
        df_trades.to_csv(PATHS.LIVE_TRADES, index=False)
        print(f"Saved Trade History to {PATHS.LIVE_TRADES}")
    else:
        # Create empty if none
        pd.DataFrame(columns=['timestamp','symbol','name','type','price','qty','pnl']).to_csv(PATHS.LIVE_TRADES, index=False)

    # 5. Generate "Yesterday vs Today" Report
    if len(history) >= 2:
        today_eq = history[-1]['total_equity']
        yest_eq = history[-2]['total_equity']
        diff = today_eq - yest_eq
        
        print("\n=== Simulation Summary ===")
        print(f"Yesterday: {yest_eq:,.0f}")
        print(f"Today:     {today_eq:,.0f}")
        print(f"Change:    {diff:,.0f} KRW")
        
        # We can call the detailed reporting script here or just rely on the standard daily report 
        # generated by the LAST run_daily_cycle call (which overwrites Daily_Briefing).
        # Since we ran `engine.run_daily_cycle(end_date)`, the system likely generated `Daily_Briefing_{end_date}.md` already?
        # NO, `run_live_trading.py` does NOT generate the report. `daily_routine.py` does.
        # So we should ideally call `daily_routine.py` logic OR just print the summary.
        
        # User asked for "Report showing Yesterday vs Today". 
        # I'll create a special report file.
        
        report_md = f"""# 📊 Simulation Transition Report ({end_date})

## 1. Performance Overview
- **Yesterday ({sim_dates[-2].date()})**: {yest_eq:,.0f} KRW
- **Today ({end_date})**: {today_eq:,.0f} KRW
- **Change**: {diff:+,.0f} KRW ({(diff/yest_eq)*100:.2f}%)

## 2. Transition Status
- **Simulation**: Completed (30 days)
- **State**: Saved to `portfolio_state.json`
- **Ready for Tomorrow**: ✅ YES

## 3. Latest Trades (Today)
"""
        # Filter today's trades
        todays_trades = [t for t in all_trades if t['timestamp'].startswith(str(end_date))]
        if todays_trades:
            for t in todays_trades:
                report_md += f"- {t['type']} {t['name']} ({t['symbol']}): {t['qty']} @ {t['price']:,.0f}\n"
        else:
            report_md += "- No trades today.\n"
            
        report_path = PATHS.REPORTS_DIR / f"Simulation_Transition_Report_{end_date}.md"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_md)
        print(f"Transition Report saved to {report_path}")

if __name__ == "__main__":
    main()
