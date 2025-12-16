"""
DGE Final Live Trading Runner
- Executes 'DGE Hybrid Swing' Strategy
- Uses RealBrokerSim (Paper Trading with Real Data)
- Supports Overnight Holding based on Suitability Score
"""

import sys
import os
from pathlib import Path
import pandas as pd
import time
from datetime import datetime, timedelta
import yaml
import json
import logging
import csv

# ... (existing imports)



# Add project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from broker.real_broker_sim import RealBrokerSim
from strategies.kr_intraday.dge_final import DGEFinalStrategy
from scripts.analysis.score_universe_for_dgefinal import calculate_suitability
from regime.micro_regime import calculate_latest_micro_regime
from config import PATHS

# Configuration
PROFILE_PATH = "config/profile_champion.yaml"
UNIVERSE_FILE = "configs/universe_top100.csv"
LOG_FILE = "logs/paper_trading_results.log"

# Setup Logging
# Ensure logs dir exists
Path("logs").mkdir(exist_ok=True)

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
logging.getLogger('').addHandler(console)

class LiveRunner:
    def __init__(self):
        self.broker = RealBrokerSim() # Connects to Kiwoom (Data)
        self.strategies = {} # symbol -> strategy instance
        self.universe = []
        self.allocations = {}
        self.config = self.load_config()
        self.market_regime = "R7_UNKNOWN" # Default
        self.micro_regime = "MR_UNKNOWN" # Default
        
    def load_config(self):
        try:
            with open(PROFILE_PATH, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            logging.info(f"Loaded Profile: {PROFILE_PATH}")
            return config
        except Exception as e:
            logging.error(f"Failed to load profile: {e}")
            sys.exit(1)

    def save_dashboard_status(self):
        status = {
            "profile": "Champion v2.1 Optimized",
            "market_regime": self.market_regime,
            "micro_regime": self.micro_regime,
            "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "allocations": self.allocations,
            "active_strategies": list(self.strategies.keys())
        }
        try:
            status_file = PATHS.LOGS_DIR / "dashboard_status.json"
            with open(status_file, "w", encoding="utf-8") as f:
                json.dump(status, f, indent=2)
        except Exception as e:
            logging.error(f"Failed to save dashboard status: {e}")
        except Exception as e:
            logging.error(f"Failed to save dashboard status: {e}")

    def save_daily_intent(self):
        """Generates and saves daily_plan.json with natural language summary"""
        intent_summary = f"Market is {self.market_regime} ({self.micro_regime}). "
        
        # Simple Logic to Text
        if "R4" in self.market_regime or "R5" in self.market_regime:
            mode = "DEFENSIVE"
            intent_summary += "System is in Defensive Mode. New entries are disabled. Monitoring existing positions for exit signals only."
        elif "R1" in self.market_regime or "R2" in self.market_regime:
            mode = "ATTACK"
            intent_summary += "System is in Attack Mode. Aggressively scanning for breakout setups in top 100 symbols."
        else:
            mode = "NEUTRAL"
            intent_summary += "System is in Neutral Mode. Selective entries allowed with reduced position size."

        plan = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "market_regime": self.market_regime,
            "micro_regime": self.micro_regime,
            "operator_mode": mode,
            "intent_summary": intent_summary,
            "target_universe_count": len(self.universe),
            "active_strategies": list(self.strategies.keys()),
            "risk_settings": self.config.get("risk", {})
        }
        
        try:
            with open(PATHS.DAILY_INTENT, "w", encoding="utf-8") as f:
                json.dump(plan, f, indent=2, ensure_ascii=False)
            logging.info(f"Saved Daily Intent: {mode}")
        except Exception as e:
            logging.error(f"Failed to save daily intent: {e}")

    def log_account_snapshot(self):
        """Logs daily account snapshot to CSV"""
        # In simulation, we might not have real account data, so we mock it or get from broker
        # For now, using mock/initial values if broker doesn't support it
        total_equity = self.broker.balance + self.broker.get_holdings_value() if hasattr(self.broker, 'get_holdings_value') else 100_000_000
        cash = self.broker.balance
        
        snapshot = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_equity": total_equity,
            "cash_balance": cash,
            "invested_amount": total_equity - cash,
            "unrealized_pnl": 0, # Placeholder
            "realized_pnl_cumulative": 0, # Placeholder
            "daily_return_pct": 0.0 # Placeholder
        }
        
        file_exists = PATHS.ACCOUNT_SNAPSHOT.exists()
        try:
            with open(PATHS.ACCOUNT_SNAPSHOT, "a", newline='', encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=snapshot.keys())
                if not file_exists:
                    writer.writeheader()
                writer.writerow(snapshot)
            logging.info("Logged Account Snapshot")
        except Exception as e:
            logging.error(f"Failed to log snapshot: {e}")

    def log_trade_execution(self, trade_dict):
        """Logs trade execution to CSV"""
        # trade_dict should match schema
        file_exists = PATHS.LIVE_TRADES.exists()
        fieldnames = ["timestamp", "symbol", "name", "side", "quantity", "price", "fee", "reason", "strategy_id", "regime"]
        
        try:
            with open(PATHS.LIVE_TRADES, "a", newline='', encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                if not file_exists:
                    writer.writeheader()
                writer.writerow(trade_dict)
            logging.info(f"Logged Trade: {trade_dict['symbol']} {trade_dict['side']}")
        except Exception as e:
            logging.error(f"Failed to log trade: {e}")
            
    def update_market_regime(self):
        # 1. Fetch Market Data (Proxy: 005930)
        # In real live trading, we should use KOSPI Index (001) or KODEX 200 (069500).
        # For now, using 005930 as proxy as per analysis.
        proxy_sym = "005930"
        daily_df = self.broker.get_price_history(proxy_sym)
        
        if daily_df is None or daily_df.empty:
            logging.warning("Failed to fetch Market Proxy data. Defaulting to R7/MR_UNKNOWN.")
            return

        # 2. Calculate Main Regime (Simplified Logic from EdgeMeter)
        # Ideally, import EdgeMeter. For now, using simple logic to match analysis.
        # R1: Close > MA20 & Strong, R2: Close > MA20, R3: Close < MA20 & > MA60, R4: Close < MA60
        last_row = daily_df.iloc[-1]
        ma20 = daily_df['close'].rolling(20).mean().iloc[-1]
        ma60 = daily_df['close'].rolling(60).mean().iloc[-1]
        mom = last_row['close'] / daily_df['close'].shift(20).iloc[-1]
        
        if last_row['close'] > ma20:
            if mom > 1.05:
                self.market_regime = "R1_STRONG_UP"
            else:
                self.market_regime = "R2_GRIND_UP"
        else:
            if last_row['close'] > ma60:
                self.market_regime = "R3_CHOP"
            else:
                self.market_regime = "R4_DOWN"
                
        # 3. Calculate Micro Regime
        self.micro_regime = calculate_latest_micro_regime(daily_df)
        
        logging.info(f"Market Regime: {self.market_regime} | Micro: {self.micro_regime}")

    def is_entry_allowed(self, regime, micro, profile):
        rp = profile["regime_policy"].get(regime)
        if not rp:
            return False # Default Block if undefined
            
        # Check Mode
        if rp.get("mode") == "CASH_ONLY":
            logging.info(f"Blocked by Regime Mode: {regime} -> CASH_ONLY")
            return False
            
        # Check Guardrails
        guard = rp.get("guardrail", {})
        if guard.get("trading_enabled") is False:
            logging.info(f"Blocked by Trading Disabled: {regime}")
            return False
            
        banned_micros = guard.get("micro_ban", [])
        if micro in banned_micros:
            logging.info(f"Blocked by Micro Ban: {micro} in {regime}")
            return False
            
        return True

    def run_daily_prep(self):
        logging.info(f"\n[Daily Prep] {datetime.now()}")
        self.save_dashboard_status() # Early Status Update
        
        # 0. Update Market Regime
        self.update_market_regime()
        
        # [Operator View] Save Daily Intent
        self.save_daily_intent()
        
        # Check Global Entry Permission
        if not self.is_entry_allowed(self.market_regime, self.micro_regime, self.config):
            logging.warning(f"Entry BLOCKED by Policy ({self.market_regime}/{self.micro_regime}). Cash Only.")
            self.allocations = {} # Force Empty
            return

        # 1. Load Universe
        try:
            self.universe = pd.read_csv(UNIVERSE_FILE)['symbol'].astype(str).str.zfill(6).tolist()
        except FileNotFoundError:
            logging.warning(f"Universe file not found: {UNIVERSE_FILE}. Using default watchlist.")
            self.universe = ['005930', '000660', '373220', '207940', '105560'] # Fallback

        # 2. Calculate Scores (Live)
        logging.info(f"Calculating Scores for {len(self.universe)} symbols...")
        scores = {}
        for sym in self.universe:
            try:
                # Fetch Daily Data (Cached or Live)
                daily_df = self.broker.get_price_history(sym)
                if daily_df is None or daily_df.empty:
                    continue
                
                # Calculate Score
                score_df = calculate_suitability(daily_df)
                if not score_df.empty:
                    scores[sym] = score_df['final_score'].iloc[-1]
            except Exception as e:
                # logging.error(f"Error scoring {sym}: {e}") # Reduce noise
                continue

        # 3. Portfolio Allocation (Champion Rule Layer 2)
        # Sort by Score Descending
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        self.allocations = {}
        remaining_cap = 1.0
        
        # Load Gate from Config
        t_gate = self.config['core'].get('gate', 0.15)
        max_pos = self.config['core'].get('max_positions', 3)
        logging.info(f"Using T_GATE: {t_gate}, MaxPos: {max_pos}")
        
        logging.info("\n[Portfolio Allocation]")
        allocated_count = 0
        
        for sym, score in sorted_scores:
            if score < t_gate:
                logging.info(f"  {sym}: Score {score:.2f} < Gate {t_gate} (Skipped)")
                continue
                
            if remaining_cap <= 0:
                break
            
            if allocated_count >= max_pos:
                logging.info(f"  Max Positions ({max_pos}) Reached. Stopping allocation.")
                break
                
            # Concentration Logic: w = min(score, remaining)
            weight = min(score, remaining_cap)
            self.allocations[sym] = weight
            remaining_cap -= weight
            allocated_count += 1
            
            logging.info(f"  {sym}: Score {score:.2f} -> Alloc {weight*100:.1f}%")
            
        if not self.allocations:
            logging.info("  No symbols met the criteria. 100% Cash.")
            
        # 4. Initialize Strategies for Allocated Symbols
        self.strategies = {}
        risk_per_trade = 0.02 # Default
        
        for sym, weight in self.allocations.items():
            daily_df = self.broker.get_price_history(sym)
            
            # Note: Layer 3 Smart Swing is not explicitly in profile yaml yet, 
            # assuming it's part of strategy logic or defaults.
            # v2.1 spec says "Champion v2 core", so we assume same smart swing logic.
            
            strat_config = {
                'risk_per_trade': risk_per_trade,
                'mode': 'ATTACK',
                'smart_swing': True # Default for Champion
            }
            strategy = DGEFinalStrategy(self.broker, strat_config, daily_df, sym)
            self.strategies[sym] = strategy
            self.strategies[sym] = strategy
            logging.info(f"Initialized Strategy for {sym} (Alloc: {weight*100:.1f}%)")
            
        self.save_dashboard_status() # Save Status
                
    def run_market_loop(self):
        logging.info(f"\n[Market Loop] Started at {datetime.now()}")
        logging.info("Waiting for Market Open (09:00)...")
        
        while True:
            now = datetime.now()
            
            # 0. Pre-Market Wait (Wait until 09:00)
            if now.hour < 9:
                self.save_dashboard_status()
                time.sleep(60)
                continue
                
            # 1. Market Close Check (15:30)
            if now.hour == 15 and now.minute >= 30:
                logging.info("Market Closed.")
                self.handle_eod_logic() # Final Check
                self.save_dashboard_status()
                self.log_account_snapshot() # [Operator View] EOD Snapshot
                break
                
            # 2. EOD Check (15:20) - Overnight Decision
            if now.hour == 15 and now.minute == 20:
                self.handle_eod_logic()
                time.sleep(60) # Run once
                continue
                
            # 3. Intraday Loop (Monitor Stop Loss & Entry)
            for sym, strategy in self.strategies.items():
                # Placeholder for real-time monitoring
                # In real implementation, we would fetch current price and update strategy
                pass
                
            time.sleep(1) # Loop

    def handle_eod_logic(self):
        logging.info(f"[EOD Logic {datetime.now().strftime('%H:%M')}] Checking Overnight Conditions...")
        for sym, strategy in self.strategies.items():
            pos = self.broker.get_position(sym)
            if pos:
                # Check Suitability using Smart Swing Logic from Config
                should_hold = strategy.should_hold_overnight(datetime.now())
                if should_hold:
                    logging.info(f"[{sym}] Strategy Hold Signal -> Holding Overnight.")
                else:
                    logging.info(f"[{sym}] Intraday Mode -> Closing Position.")
                    self.broker.send_order(sym, "SELL", pos['qty'], 0, "MARKET")

def main():
    # Ensure logs dir exists
    Path("logs").mkdir(exist_ok=True)
    
    logging.info("=== DGE Final Live Runner (Champion v2.1 Optimized) ===")
    logging.info("Profile: Champion v2.1 (Guardrails + Cash Only R5)")
    
    runner = LiveRunner()
    
    # Run Prep immediately
    runner.run_daily_prep()
    
    logging.info("Ready. Starting Market Loop...")
    try:
        runner.run_market_loop()
    except KeyboardInterrupt:
        logging.info("Stopped by User.")

if __name__ == "__main__":
    main()
