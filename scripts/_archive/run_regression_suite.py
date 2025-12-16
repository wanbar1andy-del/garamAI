"""
Golden Test Suite (Regression Testing)
Runs a fixed scenario and compares the output against a 'Golden Master' to detect logic drift.
"""

import sys
import os
import hashlib
import json
import pandas as pd
from pathlib import Path
import logging

# Add project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root.parent))

from garam.config import PATHS
from garam.risk.portfolio_manager import PortfolioManager
from garam.risk.dge import RiskConfig

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("GoldenTest")

class GoldenTestSuite:
    def __init__(self):
        self.golden_dir = PATHS.LOGS_DIR / "golden"
        self.golden_dir.mkdir(parents=True, exist_ok=True)
        self.master_file = self.golden_dir / "master_results.json"
        
    def run_scenario_a(self):
        """
        Scenario A: Simple Breakout on Mock Data
        """
        # 1. Setup Mock Data (Fixed Seed)
        dates = pd.date_range(start="2024-01-01", periods=100)
        prices = [10000]
        for i in range(99):
            # Deterministic pattern: Up 1%, Down 0.5%
            change = 1.01 if i % 2 == 0 else 0.995
            prices.append(prices[-1] * change)
            
        df = pd.DataFrame({'close': prices}, index=dates)
        
        # 2. Run PM Logic
        pm = PortfolioManager(100_000_000)
        config = RiskConfig()
        pm.register_symbol("TEST_A", config)
        
        equity_curve = []
        
        for date in dates:
            pm.on_day_start()
            price = df.loc[date, 'close']
            
            # Simple Signal: Buy on even days
            signal = 1 if date.day % 2 == 0 else 0
            
            if signal == 1:
                size = pm.calculate_position_size("TEST_A", price, price*0.98, 'GREEN')
                # Mock Trade
                pnl = size * 0.01 # 1% profit
                pm.update_pnl(pnl)
                
            equity_curve.append(pm.current_capital)
            
            
        return {
            'final_equity': pm.current_capital,
            'equity_hash': hashlib.md5(str(equity_curve).encode()).hexdigest()
        }

    def run_api_check(self):
        """
        Scenario B: Dashboard API Health Check
        Verifies that key endpoints return 200 OK and valid JSON.
        """
        import urllib.request
        
        endpoints = [
            'http://localhost:5000/',
            'http://localhost:5000/api/ai/summary',
            'http://localhost:5000/api/strategy/daily-plan/today',
            'http://localhost:5000/api/strategy/signals/today',
            'http://localhost:5000/api/portfolio/universe',
            'http://localhost:5000/api/portfolio/performance'
        ]
        
        results = {}
        
        print("\n[API Check]")
        for url in endpoints:
            try:
                with urllib.request.urlopen(url, timeout=2) as response:
                    status = response.getcode()
                    results[url] = 'OK' if status == 200 else f'FAIL({status})'
                    print(f"  - {url}: {results[url]}")
            except Exception as e:
                results[url] = f'ERROR({str(e)})'
                print(f"  - {url}: {results[url]}")
                
        return results

    def run(self, update_master=False):
        logger.info("Running Golden Test Suite...")
        
        current_results = {
            'scenario_a': self.run_scenario_a(),
            'api_check': self.run_api_check()
        }
        
        if update_master or not self.master_file.exists():
            logger.info("Updating Golden Master...")
            with open(self.master_file, 'w') as f:
                json.dump(current_results, f, indent=4)
            print("✅ Golden Master Updated.")
            return True
            
        # Compare
        with open(self.master_file, 'r') as f:
            master_results = json.load(f)
            
        success = True
        for key, val in current_results.items():
            master_val = master_results.get(key)
            if val != master_val:
                print(f"❌ Mismatch in {key}!")
                print(f"   Expected: {master_val}")
                print(f"   Got:      {val}")
                success = False
            else:
                print(f"✅ {key} Passed.")
                
        return success

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--update', action='store_true', help='Update Golden Master')
    args = parser.parse_args()
    
    suite = GoldenTestSuite()
    success = suite.run(update_master=args.update)
    
    if not success:
        sys.exit(1)
