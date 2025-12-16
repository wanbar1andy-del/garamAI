"""
Paper Trading Log Analyzer

Analyzes paper trading logs to provide insights on:
- Signal generation frequency
- Trade execution success rate
- Simulated PnL performance
- Strategy effectiveness

Usage:
    python analyze_paper_trading_logs.py --date today
    python analyze_paper_trading_logs.py --date 20251126
    python analyze_paper_trading_logs.py --start 20251120 --end 20251126
"""

import pandas as pd
import json
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from garam.config import PATHS


class PaperTradingAnalyzer:
    """Analyzer for paper trading logs"""
    
    def __init__(self, data_root=None):
        self.data_root = Path(data_root) if data_root else PATHS.DATA_ROOT
        self.logs_dir = self.data_root / "kr" / "paper_trading"
        self.trades = []
        self.signals = []
        
    def load_trades(self, date_str):
        """Load trades for a specific date"""
        try:
            trades_file = self.logs_dir / f"trades_{date_str}.json"
            if not trades_file.exists():
                print(f"No trades file for {date_str}")
                return []
            
            with open(trades_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('trades', [])
        except Exception as e:
            print(f"Error loading trades for {date_str}: {e}")
            return []
    
    def load_signals(self, date_str):
        """Load signals for a specific date"""
        try:
            signals_file = self.logs_dir / f"signals_{date_str}.json"
            if not signals_file.exists():
                print(f"No signals file for {date_str}")
                return []
            
            with open(signals_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('signals', [])
        except Exception as e:
            print(f"Error loading signals for {date_str}: {e}")
            return []
    
    def analyze_date(self, date_str):
        """Analyze paper trading for a single date"""
        print(f"\n{'='*60}")
        print(f"Paper Trading Analysis: {date_str}")
        print(f"{'='*60}\n")
        
        trades = self.load_trades(date_str)
        signals = self.load_signals(date_str)
        
        # Signal Analysis
        print(f"📊 Signal Generation")
        print(f"   Total Signals: {len(signals)}")
        
        if signals:
            signal_types = defaultdict(int)
            for sig in signals:
                signal_types[sig.get('signal', 'UNKNOWN')] += 1
            
            for sig_type, count in signal_types.items():
                print(f"   - {sig_type}: {count}")
            
            # Signal frequency (signals per hour)
            if len(signals) > 0:
                first_time = datetime.fromisoformat(signals[0].get('timestamp', ''))
                last_time = datetime.fromisoformat(signals[-1].get('timestamp', ''))
                duration_hours = (last_time - first_time).total_seconds() / 3600
                if duration_hours > 0:
                    freq = len(signals) / duration_hours
                    print(f"   Signal Frequency: {freq:.2f} signals/hour")
        
        # Trade Analysis
        print(f"\n💼 Trade Execution")
        print(f"   Total Trades: {len(trades)}")
        
        if trades:
            # Trade types
            trade_types = defaultdict(int)
            for trade in trades:
                trade_types[trade.get('side', 'UNKNOWN')] += 1
            
            for t_type, count in trade_types.items():
                print(f"   - {t_type}: {count}")
            
            # Success rate (trades with realized_pnl)
            trades_with_pnl = [t for t in trades if 'realized_pnl' in t]
            winning_trades = [t for t in trades_with_pnl if t['realized_pnl'] > 0]
            
            if trades_with_pnl:
                win_rate = len(winning_trades) / len(trades_with_pnl)
                print(f"   Win Rate: {win_rate:.1%} ({len(winning_trades)}/{len(trades_with_pnl)})")
            
            # PnL Analysis
            total_pnl = sum(t.get('realized_pnl', 0) for t in trades)
            print(f"\n💰 Performance")
            print(f"   Total PnL: ₩{total_pnl:,.0f}")
            
            if trades_with_pnl:
                avg_win = sum(t['realized_pnl'] for t in winning_trades) / len(winning_trades) if winning_trades else 0
                losing_trades = [t for t in trades_with_pnl if t['realized_pnl'] < 0]
                avg_loss = sum(t['realized_pnl'] for t in losing_trades) / len(losing_trades) if losing_trades else 0
                
                print(f"   Avg Win: ₩{avg_win:,.0f}")
                print(f"   Avg Loss: ₩{avg_loss:,.0f}")
                
                if avg_loss != 0:
                    payoff_ratio = abs(avg_win / avg_loss)
                    print(f"   Payoff Ratio: {payoff_ratio:.2f}")
        
        # Execution Quality
        print(f"\n🎯 Execution Quality")
        if len(signals) > 0 and len(trades) > 0:
            execution_rate = len(trades) / len(signals)
            print(f"   Execution Rate: {execution_rate:.1%} ({len(trades)} trades / {len(signals)} signals)")
        else:
            print(f"   Execution Rate: N/A")
        
        # Save summary
        summary = {
            'date': date_str,
            'total_signals': len(signals),
            'total_trades': len(trades),
            'win_rate': win_rate if trades_with_pnl else 0,
            'total_pnl': total_pnl,
            'execution_rate': len(trades) / len(signals) if signals else 0
        }
        
        return summary
    
    def analyze_range(self, start_date_str, end_date_str):
        """Analyze paper trading over a date range"""
        print(f"\n{'='*60}")
        print(f"Paper Trading Range Analysis: {start_date_str} to {end_date_str}")
        print(f"{'='*60}\n")
        
        start = datetime.strptime(start_date_str, '%Y%m%d')
        end = datetime.strptime(end_date_str, '%Y%m%d')
        
        summaries = []
        current = start
        
        while current <= end:
            date_str = current.strftime('%Y%m%d')
            summary = self.analyze_date(date_str)
            summaries.append(summary)
            current += timedelta(days=1)
        
        # Aggregate Statistics
        print(f"\n{'='*60}")
        print(f"Aggregate Statistics")
        print(f"{'='*60}\n")
        
        total_signals = sum(s['total_signals'] for s in summaries)
        total_trades = sum(s['total_trades'] for s in summaries)
        total_pnl = sum(s['total_pnl'] for s in summaries)
        
        print(f"📊 Total Signals: {total_signals}")
        print(f"💼 Total Trades: {total_trades}")
        print(f"💰 Total PnL: ₩{total_pnl:,.0f}")
        
        if total_signals > 0:
            avg_execution_rate = total_trades / total_signals
            print(f"🎯 Avg Execution Rate: {avg_execution_rate:.1%}")
        
        days_with_data = sum(1 for s in summaries if s['total_trades'] > 0)
        print(f"📅 Trading Days: {days_with_data}/{len(summaries)}")
        
        return summaries


def main():
    parser = argparse.ArgumentParser(description="Analyze paper trading logs")
    parser.add_argument('--date', help='Single date to analyze (today or YYYYMMDD)')
    parser.add_argument('--start', help='Start date for range analysis (YYYYMMDD)')
    parser.add_argument('--end', help='End date for range analysis (YYYYMMDD)')
    parser.add_argument('--data-root', help='Custom data root path')
    
    args = parser.parse_args()
    
    analyzer = PaperTradingAnalyzer(data_root=args.data_root)
    
    if args.date:
        if args.date.lower() == 'today':
            date_str = datetime.now().strftime('%Y%m%d')
        else:
            date_str = args.date
        
        analyzer.analyze_date(date_str)
    
    elif args.start and args.end:
        analyzer.analyze_range(args.start, args.end)
    
    else:
        # Default: analyze today
        date_str = datetime.now().strftime('%Y%m%d')
        print(f"No date specified, analyzing today: {date_str}\n")
        analyzer.analyze_date(date_str)


if __name__ == "__main__":
    main()
