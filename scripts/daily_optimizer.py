
import pandas as pd
import subprocess
import sys
from pathlib import Path
import logging
from datetime import datetime

# Setup Logging
log_dir = Path("logs/optimizer")
log_dir.mkdir(parents=True, exist_ok=True)
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s', 
                    handlers=[logging.FileHandler(log_dir / "daily_evolve.log"), logging.StreamHandler(sys.stdout)])

def run_simulation():
    logging.info("Running Daily Simulation...")
    try:
        # Run simulate_daily_trend.py
        subprocess.run(["python", "scripts/strategies/simulate_daily_trend.py"], check=True)
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Simulation Failed: {e}")
        return False

def analyze_and_decide():
    # Load Equity Curve
    eq_file = Path("logs/y1_daily/equity.csv")
    if not eq_file.exists():
        logging.error("Equity file not found.")
        return None
        
    try:
        df = pd.read_csv(eq_file)
        if df.empty: return None
        
        # Calculate recent Volatility (of Equity)
        df['return'] = df['equity'].pct_change()
        recent_vol = df['return'].tail(5).std() * 100 # percentage
        
        logging.info(f"Recent Equity Volatility (5d): {recent_vol:.2f}%")
        
        # Decision Logic (Mock / Simple)
        # If Vol > 2.0%, tighten stops. Else, standard.
        command = ""
        if recent_vol > 2.0:
            logging.info("High Volatility Detected. Tightening Risk.")
            command = 'echo "[AUTO-EVOLVE] High Volatility! Tightening ATR Stop to 2.0x."'
        else:
            logging.info("Volatility Normal. Maintaining Standard.")
            command = 'echo "[AUTO-EVOLVE] Market Normal. Keeping ATR Stop at 3.0x."'
            
        return command
        
    except Exception as e:
        logging.error(f"Analysis Failed: {e}")
        return None

def packet_command(cmd_str):
    if not cmd_str: return
    
    cmd_dir = Path("commands")
    cmd_dir.mkdir(exist_ok=True)
    
    out_file = cmd_dir / "apply_tomorrow_strategy.txt"
    try:
        with open(out_file, 'w') as f:
            f.write(cmd_str)
        logging.info(f"Command Packet Generated: {out_file}")
    except Exception as e:
        logging.error(f"Failed to write command packet: {e}")

def main():
    logging.info("Starting Daily Auto-Evolution Cycle...")
    
    # 1. Run Simulation
    if not run_simulation():
        return
        
    # 2. Analyze
    cmd = analyze_and_decide()
    
    # 3. Packet
    packet_command(cmd)
    
    logging.info("Cycle Complete.")

if __name__ == "__main__":
    main()
