"""
Research A: HeatScore Filter vs. Leverage
Tests 3 scenarios to validate HeatScore efficacy:
1. Filter Only: Enter only if HeatScore >= Threshold
2. Size Only: Always enter, but adjust size based on HeatScore
3. Combined: Filter + Dynamic Size
"""

import logging
import argparse
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import sys

# Add project root
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from garam.config import PATHS
from garam.risk.portfolio_manager import PortfolioManager
from garam.risk.dge import RiskConfig
from garam.scripts.select_top10_universe import UniverseSelector

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("ResearchHeatScore")

class HeatScoreResearcher:
    def __init__(self, days=250, initial_capital=100_000_000):
        self.days = days
        self.initial_capital = initial_capital
        self.universe = []
        self.data_cache = {}
        
    def setup(self):
        """Load universe and data"""
        selector = UniverseSelector()
        self.universe = selector.select_top10()
        self._load_data()
        
    def _load_data(self):
        """Load real data (resampled to daily)"""
        data_dir = PATHS.DATA_DIR / "kr" / "intraday" / "1m"
        
        for symbol in self.universe:
            file_path = data_dir / f"{symbol}_1m.csv"
            if not file_path.exists(): continue
            
            try:
                df_1m = pd.read_csv(file_path)
                df_1m['timestamp'] = pd.to_datetime(df_1m['timestamp'])
                df_1m.set_index('timestamp', inplace=True)
                
                df_daily = df_1m.resample('1D').agg({
                    'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'
                }).dropna()
                
                if len(df_daily) < 20: continue
                
                # Generate Signals (20-day Breakout)
                df_daily['high_20'] = df_daily['high'].rolling(20).max().shift(1)
                df_daily['low_20'] = df_daily['low'].rolling(20).min().shift(1)
                
                df_daily['signal'] = 0
                # Buy Entry
                condition_buy = (df_daily['close'] > df_daily['high_20']) & (df_daily['close'].shift(1) <= df_daily['high_20'].shift(1))
                df_daily.loc[condition_buy, 'signal'] = 1
                # Sell Entry
                condition_sell = (df_daily['close'] < df_daily['low_20']) & (df_daily['close'].shift(1) >= df_daily['low_20'].shift(1))
                df_daily.loc[condition_sell, 'signal'] = -1
                
                self.data_cache[symbol] = df_daily
                
            except Exception as e:
                logger.error(f"Error loading {symbol}: {e}")

    def run_scenario(self, mode='control'):
        """
        Run backtest for a specific scenario
        mode: 'control', 'filter', 'size', 'combined'
        """
        logger.info(f"Running Scenario: {mode.upper()}")
        
        # Config based on mode
        pm_config = {'aggressive_mode': True} # Base config
        
        # Initialize PM
        pm = PortfolioManager(self.initial_capital, risk_config=pm_config)
        
        # Register symbols
        risk_config = RiskConfig(max_risk_per_trade_pct=0.015, use_kelly=False)
        for symbol in self.universe:
            pm.register_symbol(symbol, risk_config)
            
        all_dates = sorted(list(set().union(*[df.index for df in self.data_cache.values()])))
        portfolio_history = []
        
        # Mock HeatScore Generator (Replace with Real later)
        np.random.seed(42) # Fixed seed for comparison
        heat_scores = np.random.normal(0, 1.0, len(all_dates))
        
        for i, date in enumerate(all_dates):
            pm.on_day_start()
            
            # HeatScore Logic
            raw_heat_score = heat_scores[i]
            
            # Mode Logic
            effective_heat_score = raw_heat_score
            filter_pass = True
            
            if mode == 'control':
                effective_heat_score = 0.0 # No sizing impact
            elif mode == 'filter':
                effective_heat_score = 0.0 # No sizing impact
                if raw_heat_score < 0.5: filter_pass = False
            elif mode == 'size':
                effective_heat_score = raw_heat_score # Sizing impact active
            elif mode == 'combined':
                effective_heat_score = raw_heat_score
                if raw_heat_score < 0.5: filter_pass = False
            
            pm.update_heat_score(effective_heat_score)
            
            daily_trades = 0
            daily_pnl = 0
            
            for symbol in self.universe:
                if symbol not in self.data_cache: continue
                df = self.data_cache[symbol]
                if date not in df.index: continue
                
                row = df.loc[date]
                
                if row['signal'] != 0 and filter_pass:
                    price = row['close']
                    sl_price = price * 0.98 if row['signal'] == 1 else price * 1.02
                    
                    # Calculate Size
                    size_krw = pm.calculate_position_size(
                        symbol, price, sl_price, regime='GREEN'
                    )
                    
                    if size_krw > 0:
                        qty = int(size_krw / price)
                        if qty > 0:
                            # Execute
                            outcome = np.random.normal(0.002, 0.015) # Mock outcome
                            pnl = size_krw * outcome
                            pm.update_pnl(pnl)
                            daily_pnl += pnl
                            daily_trades += 1
            
            portfolio_history.append({
                'date': date,
                'equity': pm.current_capital,
                'trades': daily_trades
            })
            
        return pd.DataFrame(portfolio_history)

    def compare_results(self):
        modes = ['control', 'filter', 'size', 'combined']
        results = {}
        
        print("\n" + "="*70)
        print(" Research A: HeatScore Filter vs. Leverage Results")
        print("="*70)
        print(f"{'Mode':<10} | {'Return':<8} | {'CAGR':<8} | {'MDD':<8} | {'Sharpe':<6} | {'Eff':<5}")
        print("-" * 70)
        
        for mode in modes:
            history = self.run_scenario(mode)
            if history.empty: 
                results[mode] = None
                continue
            
            initial = self.initial_capital
            final = history['equity'].iloc[-1]
            ret = (final - initial) / initial
            days = len(history)
            cagr = (1 + ret) ** (250/days) - 1 if days > 0 else 0
            
            peak = history['equity'].cummax()
            dd = (history['equity'] - peak) / peak
            max_dd = dd.min()
            
            # Sharpe (Simplified daily)
            daily_ret = history['equity'].pct_change().dropna()
            sharpe = (daily_ret.mean() / daily_ret.std() * np.sqrt(250)) if daily_ret.std() > 0 else 0
            
            # Efficiency (CAGR / Avg Exposure) - Simplified proxy
            # In real script, track exposure. Here assume 100% for control/filter, dynamic for size
            avg_exp = 1.0
            if mode in ['size', 'combined']: avg_exp = 0.8 # Mock avg exposure
            eff = cagr / avg_exp
            
            print(f"{mode:<10} | {ret:.2%}   | {cagr:.2%}   | {max_dd:.2%}   | {sharpe:.2f}   | {eff:.2f}")
            results[mode] = {'cagr': cagr, 'mdd': max_dd, 'sharpe': sharpe, 'eff': eff}
            
        print("="*70 + "\n")
        
        # Criteria Check
        if not results.get('control'): return

        ctrl = results['control']
        
        print("🛑 Cut-off Criteria Check:")
        
        # 1. Filter Check
        if results.get('filter'):
            filt = results['filter']
            cond_sharpe = filt['sharpe'] >= ctrl['sharpe'] + 0.2
            cond_cagr = filt['cagr'] >= ctrl['cagr'] * 0.95
            cond_mdd = filt['mdd'] >= ctrl['mdd'] * 0.9 # MDD is negative, so >= is smaller magnitude? No.
            # MDD is e.g. -0.10. Improvement means -0.09 (larger value).
            # So filt['mdd'] > ctrl['mdd'] is improvement.
            # Requirement: >= 10% improvement. i.e. filt > ctrl * 0.9 (if ctrl is -0.20, target > -0.18)
            cond_mdd_imp = filt['mdd'] > ctrl['mdd'] * 0.9 
            
            pass_count = sum([cond_sharpe, cond_cagr, cond_mdd_imp])
            status = "PASS" if pass_count >= 2 else "FAIL"
            print(f"1. Filter Effect: {status} (Sharpe +{filt['sharpe']-ctrl['sharpe']:.2f}, MDD {filt['mdd']:.2%} vs {ctrl['mdd']:.2%})")

        # 2. Size Check
        if results.get('size'):
            size = results['size']
            cond_eff = size['eff'] >= ctrl['eff'] * 1.2
            cond_risk = size['mdd'] >= ctrl['mdd'] * 1.2 # MDD shouldn't be worse than 1.2x
            # e.g. Ctrl -10%. Limit -12%. Size -15% -> Fail.
            # Size (-0.15) < Ctrl (-0.10) * 1.2 (-0.12) -> True (Worse)
            # We want Size >= Ctrl * 1.2
            
            status = "PASS" if cond_eff and cond_risk else "FAIL"
            print(f"2. Size Effect:   {status} (Efficiency {size['eff']:.2f} vs {ctrl['eff']:.2f}, MDD {size['mdd']:.2%})")

        print("\n")

def main():
    researcher = HeatScoreResearcher()
    researcher.setup()
    researcher.compare_results()

if __name__ == "__main__":
    main()
