"""
Performance Reporter - 10분마다 성과 보고

실시간으로 포트폴리오 성과를 모니터링하고 10분마다 보고합니다.
"""

import sys
import time
import json
from datetime import datetime
from pathlib import Path

sys.path.insert(0, 'c:/garam')
from garam.config import PATHS

def get_current_performance():
    """Get current trading performance"""
    
    # Load signals_live.json
    signals_file = PATHS.STRATEGY_SIGNALS_LIVE
    
    if not signals_file.exists():
        return None
    
    with open(signals_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    equity = data.get('equity', 0)
    cash = data.get('cash', 0)
    holdings = data.get('holdings', {})
    
    # Calculate metrics
    initial_capital = 100_000_000
    total_return = ((equity / initial_capital) - 1) * 100
    invested = equity - cash
    invested_ratio = (invested / equity) * 100 if equity > 0 else 0
    
    # PnL
    total_pnl = sum(h.get('pnl', 0) for h in holdings.values())
    
    return {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'equity': equity,
        'cash': cash,
        'invested': invested,
        'invested_ratio': invested_ratio,
        'total_return': total_return,
        'total_pnl': total_pnl,
        'positions': len(holdings),
        'holdings': holdings
    }

def print_performance_report(perf):
    """Print performance report"""
    
    if perf is None:
        print("❌ No performance data available")
        return
    
    print("\n" + "=" * 60)
    print(f"📊 PERFORMANCE REPORT - {perf['timestamp']}")
    print("=" * 60)
    
    print(f"\n💰 Account Summary:")
    print(f"   Total Equity: {perf['equity']:>15,.0f} KRW")
    print(f"   Cash Balance: {perf['cash']:>15,.0f} KRW")
    print(f"   Invested:     {perf['invested']:>15,.0f} KRW ({perf['invested_ratio']:.1f}%)")
    
    print(f"\n📈 Performance:")
    print(f"   Total Return: {perf['total_return']:>14.2f}%")
    print(f"   Total PnL:    {perf['total_pnl']:>15,.0f} KRW")
    
    print(f"\n📦 Portfolio:")
    print(f"   Positions:    {perf['positions']:>15}")
    
    if perf['holdings']:
        print(f"\n🔹 Holdings:")
        for symbol, info in perf['holdings'].items():
            pnl = info.get('pnl', 0)
            pnl_pct = info.get('pnl_pct', 0)
            value = info.get('value', 0)
            pnl_sign = '+' if pnl >= 0 else ''
            
            print(f"   {symbol}: {value:>12,.0f} KRW | PnL: {pnl_sign}{pnl:>10,.0f} ({pnl_sign}{pnl_pct:.2f}%)")
    
    print("=" * 60)

def run_reporter(interval_minutes=10):
    """Run performance reporter every N minutes"""
    
    print("\n🚀 Performance Reporter Started")
    print(f"📅 Reporting Interval: {interval_minutes} minutes")
    print(f"⏰ First report: Now")
    print(f"⏰ Next report: {interval_minutes} minutes from now")
    print("\nPress Ctrl+C to stop...\n")
    
    try:
        count = 0
        while True:
            count += 1
            
            print(f"\n{'='*60}")
            print(f"Report #{count}")
            print(f"{'='*60}")
            
            perf = get_current_performance()
            print_performance_report(perf)
            
            # Wait for next report
            if count == 1:
                print(f"\n⏳ Waiting {interval_minutes} minutes until next report...")
            
            time.sleep(interval_minutes * 60)
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Reporter stopped by user")
        print(f"📊 Total reports generated: {count}")

if __name__ == "__main__":
    # Run reporter every 10 minutes
    run_reporter(interval_minutes=10)
