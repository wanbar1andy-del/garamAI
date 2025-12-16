#!/usr/bin/env python3
"""
Portfolio Exposure Checker
포트폴리오 노출도를 계산하고 목표와 비교
"""
import json
import sys
from pathlib import Path
from datetime import datetime
import yaml

def check_exposure(portfolio_file="portfolio_state.json", 
                   config_file="config/profile_champion_v3_weighted_400.yaml",
                   log_file=None):
    """
    포트폴리오 노출도를 계산하고 목표와 비교
    
    Args:
        portfolio_file: portfolio_state.json 경로
        config_file: profile YAML 경로
        log_file: 로그 파일 경로 (옵션)
    
    Returns:
        dict: 노출도 통계
    """
    # Load portfolio
    with open(portfolio_file, encoding='utf-8') as f:
        portfolio = json.load(f)
    
    # Load config for target
    with open(config_file, encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    target_exposure = config.get('allocation', {}).get('target_gross_exposure', 0.95)
    
    # Calculate
    cash = portfolio.get('cash', 0)
    positions = portfolio.get('positions', {})
    
    position_value = 0
    for sym, pos in positions.items():
        qty = pos.get('qty', 0)
        price = pos.get('entry_price', 0)
        position_value += qty * price
    
    equity = cash + position_value
    actual_exposure = position_value / equity if equity > 0 else 0
    
    # Calculate position details
    position_details = {}
    for sym, pos in positions.items():
        qty = pos.get('qty', 0)
        price = pos.get('entry_price', 0)
        value = qty * price
        weight = value / equity if equity > 0 else 0
        
        position_details[sym] = {
            'qty': qty,
            'price': price,
            'value': value,
            'weight': weight,
            'entry_date': pos.get('entry_date', 'N/A')
        }
    
    # Build report
    report = {
        'timestamp': str(datetime.now()),
        'equity': equity,
        'position_value': position_value,
        'cash': cash,
        'actual_exposure': actual_exposure,
        'target_exposure': target_exposure,
        'deviation': actual_exposure - target_exposure,
        'positions_count': len(positions),
        'positions': position_details
    }
    
    # Print
    print(f"{'='*60}")
    print(f"Portfolio Exposure Report - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*60}")
    print(f"총 자산:      {equity:>15,.0f} 원")
    print(f"포지션 가치:  {position_value:>15,.0f} 원")
    print(f"현금:         {cash:>15,.0f} 원")
    print(f"")
    print(f"실제 노출도:  {actual_exposure:>15.1%}")
    print(f"목표 노출도:  {target_exposure:>15.1%}")
    print(f"편차:         {report['deviation']:>15.1%}")
    
    # Warning if deviation is large
    if abs(report['deviation']) > 0.10:
        print(f"\n⚠️  WARNING: Exposure deviation exceeds 10%p!")
    
    print(f"")
    print(f"보유 종목: {len(positions)}개")
    print(f"{'-'*60}")
    
    for sym, info in sorted(position_details.items(), key=lambda x: x[1]['value'], reverse=True):
        print(f"{sym}: {info['qty']:>6}주 @ {info['price']:>10,.0f}원 "
              f"= {info['value']:>12,.0f}원 ({info['weight']:>6.1%})")
    
    print(f"{'='*60}")
    
    # Log to file
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Check if file exists to add header
        is_new = not log_path.exists()
        
        with open(log_path, 'a', encoding='utf-8') as f:
            if is_new:
                f.write("timestamp,equity,actual_exposure,target_exposure,deviation,positions_count\n")
            f.write(f"{report['timestamp']},{equity},{actual_exposure:.4f},"
                   f"{target_exposure:.4f},{report['deviation']:.4f},{len(positions)}\n")
    
    return report

if __name__ == "__main__":
    portfolio_file = "portfolio_state.json"
    config_file = "config/profile_champion_v3_weighted_400.yaml"
    log_file = "logs/exposure_history.csv"
    
    if len(sys.argv) > 1:
        portfolio_file = sys.argv[1]
    if len(sys.argv) > 2:
        config_file = sys.argv[2]
    
    try:
        report = check_exposure(portfolio_file, config_file, log_file)
        
        # Exit with error if deviation is large
        if abs(report['deviation']) > 0.20:  # 20%p 이상
            sys.exit(1)
        else:
            sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
