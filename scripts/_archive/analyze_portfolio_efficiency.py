"""
Portfolio Capital Efficiency Analyzer

Analyzes portfolio performance from a capital utilization perspective:
- Capital Efficiency = CAGR / Avg Gross Exposure
- Average daily gross exposure
- Maximum exposure
- Risk utilization

This is the KEY metric to determine whether to:
- SCALE UP (Efficiency > 4.0): Add more symbols/strategies
- MAINTAIN (Efficiency 2.0-4.0): Current allocation is optimal
- OPTIMIZE/REPLACE (Efficiency < 2.0): Strategy needs improvement

Usage:
    python analyze_portfolio_efficiency.py --trades trades.csv --start 2025-01-01 --end 2025-12-31
    python analyze_portfolio_efficiency.py --paper-trading --date-range 20251120-20251126
"""

import pandas as pd
import numpy as np
import argparse
from pathlib import Path
from datetime import datetime, timedelta
import json
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from garam.config import PATHS


class PortfolioEfficiencyAnalyzer:
    """Analyzes capital efficiency of portfolio"""
    
    def __init__(self, initial_capital=100_000_000):
        self.initial_capital = initial_capital
        self.trades = []
        self.daily_exposures = []
        
    def load_trades_from_csv(self, trades_file):
        """Load trades from CSV"""
        df = pd.read_csv(trades_file, parse_dates=['timestamp'])
        self.trades = df.to_dict('records')
        return len(self.trades)
    
    def load_paper_trading_logs(self, start_date, end_date):
        """Load paper trading logs for date range"""
        logs_dir = PATHS.DATA_ROOT / "kr" / "paper_trading"
        
        all_trades = []
        current = start_date
        
        while current <= end_date:
            date_str = current.strftime('%Y%m%d')
            trades_file = logs_dir / f"trades_{date_str}.json"
            
            if trades_file.exists():
                with open(trades_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    trades = data.get('trades', [])
                    all_trades.extend(trades)
            
            current += timedelta(days=1)
        
        self.trades = all_trades
        return len(all_trades)
    
    def calculate_daily_exposure(self):
        """
        Calculate daily gross exposure from trades
        
        Gross Exposure = Sum of absolute position values / Portfolio value
        """
        if not self.trades:
            return []
        
        # Convert trades to DataFrame
        df = pd.DataFrame(self.trades)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['date'] = df['timestamp'].dt.date
        
        # Calculate daily positions
        daily_data = []
        
        for date in df['date'].unique():
            day_trades = df[df['date'] == date]
            
            # Calculate positions (simplified: assume each trade opens/closes position)
            # In real implementation, track actual positions over time
            total_value = sum(abs(t.get('price', 0) * t.get('quantity', 0)) for t in day_trades.to_dict('records'))
            
            # Assume portfolio value grows/shrinks with PnL
            portfolio_value = self.initial_capital  # Simplified
            
            # Add exposure info if available in trades
            if 'exposure_pct' in day_trades.columns:
                avg_exposure = day_trades['exposure_pct'].mean()
            elif 'portfolio_exposure_pct' in day_trades.columns:
                avg_exposure = day_trades['portfolio_exposure_pct'].mean()
            else:
                # Fallback: estimate from trade values
                avg_exposure = (total_value / portfolio_value) if portfolio_value > 0 else 0
            
            daily_data.append({
                'date': date,
                'gross_exposure_pct': avg_exposure * 100,
                'trade_count': len(day_trades),
                'total_value': total_value
            })
        
        self.daily_exposures = daily_data
        return daily_data
    
    def calculate_returns(self):
        """Calculate portfolio returns"""
        if not self.trades:
            return {}
        
        # Calculate total PnL
        total_pnl = sum(t.get('realized_pnl', 0) for t in self.trades if 'realized_pnl' in t)
        
        # Calculate return
        total_return = total_pnl / self.initial_capital
        
        # Estimate trading days
        df = pd.DataFrame(self.trades)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        start_date = df['timestamp'].min()
        end_date = df['timestamp'].max()
        days = (end_date - start_date).days
        
        trading_days = days * 0.7  # Rough estimate (weekdays)
        
        if trading_days > 0:
            # Annualize (250 trading days per year)
            years = trading_days / 250
            cagr = (1 + total_return) ** (1/years) - 1 if years > 0 else 0
        else:
            cagr = 0
        
        return {
            'total_pnl': total_pnl,
            'total_return': total_return,
            'cagr': cagr,
            'trading_days': trading_days
        }
    
    def calculate_capital_efficiency(self):
        """
        Calculate Capital Efficiency = CAGR / Avg Gross Exposure
        
        This is the KEY metric to understand:
        - How much return per unit of capital deployed
        - Whether portfolio can be scaled up
        """
        returns = self.calculate_returns()
        cagr = returns['cagr']
        
        if not self.daily_exposures:
            self.calculate_daily_exposure()
        
        if not self.daily_exposures:
            return None
        
        # Average gross exposure
        avg_exposure = np.mean([d['gross_exposure_pct'] for d in self.daily_exposures])
        max_exposure = np.max([d['gross_exposure_pct'] for d in self.daily_exposures])
        
        # Capital Efficiency
        capital_efficiency = (cagr / (avg_exposure / 100)) if avg_exposure > 0 else 0
        
        return {
            'cagr': cagr,
            'avg_exposure_pct': avg_exposure,
            'max_exposure_pct': max_exposure,
            'capital_efficiency': capital_efficiency,
            'interpretation': self._interpret_efficiency(capital_efficiency, avg_exposure)
        }
    
    def _interpret_efficiency(self, efficiency, avg_exposure):
        """Interpret capital efficiency score"""
        if efficiency >= 4.0:
            return {
                'rating': '🌟 Excellent',
                'action': 'SCALE UP - Add more symbols/strategies',
                'reason': 'Strategy is highly efficient but capital underutilized'
            }
        elif efficiency >= 2.0:
            return {
                'rating': '✅ Good',
                'action': 'MAINTAIN - Current allocation is optimal',
                'reason': 'Balanced efficiency and capital usage'
            }
        elif efficiency >= 1.0:
            return {
                'rating': '⚠️ Warning',
                'action': 'OPTIMIZE - Strategy uses too much capital for returns',
                'reason': 'High capital usage but low efficiency'
            }
        else:
            return {
                'rating': '❌ Fail',
                'action': 'REPLACE/REVISE - Strategy is inefficient',
                'reason': 'Very low return per unit of capital'
            }
    
    def calculate_symbol_efficiency(self):
        """
        Calculate efficiency per symbol:
        - Symbol CAGR
        - Avg Exposure (Capital allocated to this symbol)
        - Efficiency = Symbol CAGR / Avg Exposure
        """
        if not self.trades: return []
        
        df = pd.DataFrame(self.trades)
        if 'symbol' not in df.columns: return []
        
        symbols = df['symbol'].unique()
        symbol_metrics = []
        
        for sym in symbols:
            sym_trades = df[df['symbol'] == sym]
            
            # PnL
            pnl = sym_trades['realized_pnl'].sum() if 'realized_pnl' in sym_trades.columns else 0
            
            # Avg Exposure (Simplified: sum of trade values / days / initial_capital)
            # This is an approximation. Ideally we track daily holding value.
            total_volume = sum(abs(t.get('price', 0) * t.get('quantity', 0)) for t in sym_trades.to_dict('records'))
            
            # Estimate holding period (days)
            # If we don't have exact holding days, we use total_volume as proxy for activity
            # Better: Use 'avg_exposure_pct' if available in logs
            
            avg_exp = 0
            if 'exposure_pct' in sym_trades.columns:
                avg_exp = sym_trades['exposure_pct'].mean()
            else:
                # Fallback: Total Volume / Trading Days / Capital * (Avg Holding Period e.g. 5 days)
                # This is rough. Let's stick to PnL/Volume ratio as proxy for efficiency
                pass
                
            # Return Contribution
            ret_contrib = pnl / self.initial_capital
            
            symbol_metrics.append({
                'symbol': sym,
                'pnl': pnl,
                'return_contribution': ret_contrib,
                'trades': len(sym_trades)
            })
            
        return pd.DataFrame(symbol_metrics).sort_values('pnl', ascending=False)

    def generate_report(self):
        """Generate comprehensive efficiency report"""
        print("\n" + "="*70)
        print(" Portfolio Capital Efficiency Analysis")
        print("="*70 + "\n")
        
        # Returns
        returns = self.calculate_returns()
        print("📊 Returns")
        print(f"   Total PnL: ₩{returns['total_pnl']:,.0f}")
        print(f"   Total Return: {returns['total_return']:.2%}")
        print(f"   CAGR: {returns['cagr']:.2%}")
        print(f"   Trading Days: {returns['trading_days']:.0f}")
        
        # Symbol Efficiency
        sym_df = self.calculate_symbol_efficiency()
        if not sym_df.empty:
            print(f"\n🏆 Symbol Performance (Top 5)")
            print(f"   {'Symbol':<10} | {'PnL':<12} | {'Contrib':<8} | {'Trades':<6}")
            print("-" * 50)
            for _, row in sym_df.head(5).iterrows():
                print(f"   {row['symbol']:<10} | ₩{row['pnl']:,.0f} | {row['return_contribution']:.2%}   | {row['trades']:<6}")
        
        # Capital Efficiency
        efficiency = self.calculate_capital_efficiency()
        
        if efficiency:
            print(f"\n💰 Capital Utilization")
            print(f"   Avg Gross Exposure: {efficiency['avg_exposure_pct']:.1f}%")
            print(f"   Max Gross Exposure: {efficiency['max_exposure_pct']:.1f}%")
            
            print(f"\n⚡ Capital Efficiency: {efficiency['capital_efficiency']:.2f}")
            print(f"   Rating: {efficiency['interpretation']['rating']}")
            print(f"   Action: {efficiency['interpretation']['action']}")
            print(f"   Reason: {efficiency['interpretation']['reason']}")
            
            # Comparison scenarios
            print(f"\n🔮 What-If Scenarios")
            cagr = efficiency['cagr']
            avg_exp = efficiency['avg_exposure_pct']
            ce = efficiency['capital_efficiency']
            
            # Scenario 1: Double exposure
            new_exp = min(avg_exp * 2, 80)
            new_cagr_est = ce * (new_exp / 100)
            print(f"   If Exposure → {new_exp:.0f}%: Est. CAGR = {new_cagr_est:.1%}")
            
            # Scenario 2: Add symbols to reach 50% exposure
            target_exp = 50
            if avg_exp < target_exp:
                new_cagr_est = ce * (target_exp / 100)
                print(f"   If Exposure → {target_exp}%: Est. CAGR = {new_cagr_est:.1%}")
        
        # Daily exposure trend
        if self.daily_exposures:
            print(f"\n📈 Daily Exposure Trend")
            print(f"   Days with data: {len(self.daily_exposures)}")
            
            # Show last 5 days
            recent = sorted(self.daily_exposures, key=lambda x: x['date'], reverse=True)[:5]
            for day in reversed(recent):
                print(f"   {day['date']}: {day['gross_exposure_pct']:.1f}% ({day['trade_count']} trades)")
        
        print("\n" + "="*70 + "\n")
        
        return efficiency


    def run_rotation_simulation(self, universe_size=10):
        """
        Simulate Rotation vs No-Rotation scenarios.
        S1: Fixed Top 10 (No Rotation)
        S2: Rotation (Remove Dead Symbols)
        """
        print("\n" + "="*70)
        print(" Research C: Portfolio Efficiency (Rotation vs Fixed)")
        print("="*70)
        
        # This requires re-running a mini-backtest or filtering existing trades.
        # For this script, we will simulate the EFFECT by filtering the loaded trades.
        
        if not self.trades:
            print("No trades loaded.")
            return

        df = pd.DataFrame(self.trades)
        if 'symbol' not in df.columns: return
        
        # Identify "Dead" symbols based on PnL/Activity (Proxy for real Dead logic)
        # Real logic: 15d Range < 0.5%
        # Here: Bottom 20% of symbols by contribution
        
        symbol_metrics = self.calculate_symbol_efficiency()
        if symbol_metrics.empty: return
        
        n_symbols = len(symbol_metrics)
        n_dead = max(1, int(n_symbols * 0.2)) # Assume bottom 20% are dead
        
        dead_symbols = symbol_metrics.tail(n_dead)['symbol'].tolist()
        
        # S1: All Trades (Fixed)
        s1_trades = df
        s1_pnl = s1_trades['realized_pnl'].sum() if 'realized_pnl' in s1_trades.columns else 0
        s1_ret = s1_pnl / self.initial_capital
        
        # S2: Filtered Trades (Rotation - Removed Dead)
        s2_trades = df[~df['symbol'].isin(dead_symbols)]
        s2_pnl = s2_trades['realized_pnl'].sum() if 'realized_pnl' in s2_trades.columns else 0
        s2_ret = s2_pnl / self.initial_capital
        
        # Compare
        print(f"{'Metric':<15} | {'S1 (Fixed)':<12} | {'S2 (Rotation)':<12} | {'Diff':<8}")
        print("-" * 60)
        print(f"{'Return':<15} | {s1_ret:.2%}       | {s2_ret:.2%}       | {s2_ret-s1_ret:+.2%}")
        print(f"{'Active Syms':<15} | {n_symbols:<12} | {n_symbols-n_dead:<12} | -{n_dead}")
        
        # Efficiency Gain?
        # If S2 return is similar but exposure (active syms) is lower -> Efficiency UP
        eff_gain = (s2_ret / (n_symbols-n_dead)) / (s1_ret / n_symbols) if s1_ret > 0 else 1.0
        print(f"{'Est. Eff Gain':<15} | {'1.00':<12} | {eff_gain:.2f}       | {(eff_gain-1)*100:+.1f}%")
        
        # Cut-off Check
        status = "FAIL"
        if eff_gain >= 1.1: status = "PASS" # +10% Efficiency
        if s2_ret > s1_ret: status = "PASS" # Absolute return improvement
        
        print("-" * 60)
        print(f"🛑 Rotation Check: {status} (Target: Eff +10% or Return Increase)")
        print("="*70 + "\n")

def main():
    parser = argparse.ArgumentParser(description="Analyze portfolio capital efficiency")
    parser.add_argument('--trades', help='Path to trades CSV file')
    parser.add_argument('--paper-trading', action='store_true', help='Use paper trading logs')
    parser.add_argument('--date-range', help='Date range for paper trading (YYYYMMDD-YYYYMMDD)')
    parser.add_argument('--start', help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end', help='End date (YYYY-MM-DD)')
    parser.add_argument('--initial-capital', type=float, default=100_000_000, help='Initial capital (default: 100M KRW)')
    parser.add_argument('--rotation-check', action='store_true', help='Run Rotation vs Fixed comparison')
    
    args = parser.parse_args()
    
    analyzer = PortfolioEfficiencyAnalyzer(initial_capital=args.initial_capital)
    
    # Load data
    if args.paper_trading:
        if args.date_range:
            start_str, end_str = args.date_range.split('-')
            start_date = datetime.strptime(start_str, '%Y%m%d')
            end_date = datetime.strptime(end_str, '%Y%m%d')
        else:
            # Default: last 7 days
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)
        
        print(f"Loading paper trading logs: {start_date.date()} to {end_date.date()}")
        count = analyzer.load_paper_trading_logs(start_date, end_date)
        print(f"Loaded {count} trades\n")
    
    elif args.trades:
        print(f"Loading trades from: {args.trades}")
        count = analyzer.load_trades_from_csv(args.trades)
        print(f"Loaded {count} trades\n")
    
    else:
        print("Error: Specify either --trades or --paper-trading")
        return
    
    # Generate report
    analyzer.generate_report()
    
    if args.rotation_check:
        analyzer.run_rotation_simulation()

if __name__ == "__main__":
    main()
