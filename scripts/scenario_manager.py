
import pandas as pd
import numpy as np
import time
import sys
import logging
from pathlib import Path
from datetime import datetime

# Logging Setup
log_dir = Path("logs/autopilot")
log_dir.mkdir(parents=True, exist_ok=True)
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s', 
                    handlers=[logging.FileHandler(log_dir / "scenario_manager.log"), logging.StreamHandler(sys.stdout)])

# Config (Paths)
# Assuming standard live/paper paths
DATA_DIR = Path("GARAM_Data")
LOGS_DIR = Path("logs/phase30/paper")
SNAPSHOT_FILE = LOGS_DIR / "account_snapshot.csv"
TRADES_FILE = LOGS_DIR / "live_trades.csv"
COMMAND_DIR = Path("commands")
COMMAND_FILE = COMMAND_DIR / "live_update.txt"

class ScenarioManager:
    def __init__(self):
        self.current_scenario = "D_NORMAL"
        self.last_check = None
        
    def calculate_metrics(self):
        """Analyze account health and simulated market volatility"""
        if not SNAPSHOT_FILE.exists():
            logging.warning("Snapshot file not found.")
            return None
            
        try:
            df = pd.read_csv(SNAPSHOT_FILE)
            if df.empty: return None
            
            # Simulated Volatility Acceleration (Vol_Accel)
            # In real system, this would use Market Index data.
            # Here we use Equity Volatility as proxy.
            df['equity'] = pd.to_numeric(df['total_equity'], errors='coerce')
            df['ret'] = df['equity'].pct_change()
            
            # Short vs Long Volatility
            vol_short = df['ret'].tail(5).std() * 100
            vol_long = df['ret'].tail(20).std() * 100
            
            vol_accel = 0.0
            if vol_long > 0:
                vol_accel = vol_short / vol_long
                
            # Recent Returns (1 week ~ 5 days)
            recent_ret = df['ret'].tail(5).sum() * 100
            
            return {
                "vol_accel": vol_accel,
                "recent_ret": recent_ret,
                "equity": df['equity'].iloc[-1]
            }
            
        except Exception as e:
            logging.error(f"Metric Calc Error: {e}")
            return None

    def decide_scenario(self, metrics):
        if metrics is None: return "D_NORMAL"
        
        va = metrics['vol_accel']
        ret = metrics['recent_ret']
        
        # A. PANIC (High Vol Accel)
        if va > 2.0:
            return "A_PANIC"
            
        # B. CLIMAX (Simplified: High Return + High Vol)
        # Note: True Climax requires Stock-level volume checks. 
        # Here we use Portfolio Climax as proxy.
        if ret > 10.0 and va > 1.5:
             return "B_CLIMAX"
             
        # C. DRIFT (Negative Return for a week)
        if ret < -2.0:
             return "C_DRIFT"
             
        # D. NORMAL
        return "D_NORMAL"

    def execute_switch(self, new_scenario):
        if new_scenario == self.current_scenario:
            return
            
        logging.info(f"SWITCHING SCENARIO: {self.current_scenario} -> {new_scenario}")
        
        cmd_content = ""
        
        if new_scenario == "A_PANIC":
            cmd_content = ('echo "[AUTOPILOT] PANIC Detected! (Vol_Accel > 2.0). '
                           'Action: Tighten Stops to 50% (1.5 ATR). Suspend Buying."')
            # Real command: set_risk_params --stop-mult 1.5
            
        elif new_scenario == "B_CLIMAX":
            cmd_content = ('echo "[AUTOPILOT] CLIMAX Detected! (Return > 10%). '
                           'Action: Scale Out 50%. Set Break-Even Stops."')
            
        elif new_scenario == "C_DRIFT":
            cmd_content = ('echo "[AUTOPILOT] DRIFT Detected. '
                           'Action: Request Optimization (Backtest)."')
            
        elif new_scenario == "D_NORMAL":
            cmd_content = ('echo "[AUTOPILOT] Market NORMAL. '
                           'Action: Restore Standard Params (3.0 ATR). Full Aggression."')
            
        # Write Command
        if cmd_content:
            try:
                COMMAND_DIR.mkdir(exist_ok=True)
                with open(COMMAND_FILE, 'w', encoding='utf-8') as f:
                    f.write(cmd_content)
                logging.info(f"Command Packet Sent: {COMMAND_FILE}")
            except Exception as e:
                logging.error(f"Command Write Failed: {e}")
                
        self.current_scenario = new_scenario

    def run_loop(self):
        logging.info("Garam Auto-Pilot (Scenario Manager) Started.")
        
        while True:
            try:
                metrics = self.calculate_metrics()
                if metrics:
                    logging.info(f"Metrics: VA={metrics['vol_accel']:.2f}, Ret={metrics['recent_ret']:.2f}%")
                    
                    # Decide
                    new_scen = self.decide_scenario(metrics)
                    
                    # Switch if needed
                    self.execute_switch(new_scen)
                    
                else:
                    logging.warning("Insufficient Data for Metrics.")
                
            except Exception as e:
                logging.error(f"Loop Error: {e}")
                
            time.sleep(60) # 1 Minute Cycle

if __name__ == "__main__":
    manager = ScenarioManager()
    manager.run_loop()
