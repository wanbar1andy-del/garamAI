#!/usr/bin/env python3
"""
1분 데이터 기반 Turbo V2.1/V2.2 일중 백테스트
실제 intraday data로 Exit 전략 성과 비교
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from datetime import datetime, timedelta

plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

def load_minute_data(symbol='005930', data_dir='g:/내 드라이브/garamdata/history/minute'):
    """1분 데이터 로드"""
    file_path = Path(data_dir) / f"{symbol}_1m.csv"
    
    if not file_path.exists():
        raise FileNotFoundError(f"Data not found: {file_path}")
    
    df = pd.read_csv(file_path)
    
    # 타임스탬프 파싱
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
    elif 'datetime' in df.columns:
        df['timestamp'] = pd.to_datetime(df['datetime'])
    else:
        # 첫 번째 컬럼이 timestamp라고 가정
        df['timestamp'] = pd.to_datetime(df.iloc[:, 0])
    
    # 필수 컬럼 확인
    required_cols = ['close', 'open', 'high', 'low']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")
    
    df = df.sort_values('timestamp').reset_index(drop=True)
    
    return df

def simulate_intraday_turbo(df, exit_threshold=0.02, version='V2.1'):
    """
    일중 터보 시뮬레이션
    
    Args:
        df: 1분 데이터 (timestamp, close 필수)
        exit_threshold: Exit 기준 (-2% = 0.02)
        version: 'V2.1' or 'V2.2'
    """
    df = df.copy()
    
    # 일별로 그룹화
    df['date'] = df['timestamp'].dt.date
    unique_dates = df['date'].unique()
    
    results = []
    
    for date in unique_dates:
        day_df = df[df['date'] == date].copy()
        
        if len(day_df) < 10:  # 데이터가 너무 적으면 스킵
            continue
        
        # 시뮬레이션 변수
        equity = 100_000_000  # 1억 시작
        turbo_active = True
        multiplier = 2.5
        day_high_equity = equity
        exit_time = None
        exit_reason = ''
        
        # 시작 가격
        start_price = day_df.iloc[0]['close']
        
        for idx, row in day_df.iterrows():
            current_price = row['close']
            timestamp = row['timestamp']
            
            # 수익률 계산 (장 시작 기준)
            daily_return = (current_price - start_price) / start_price
            
            # Turbo 적용
            if turbo_active:
                actual_return = daily_return * multiplier
            else:
                actual_return = daily_return
            
            equity = 100_000_000 * (1 + actual_return)
            
            # 고점 업데이트
            if equity > day_high_equity:
                day_high_equity = equity
            
            # Exit 조건 체크 (Turbo 활성 시만)
            if turbo_active and daily_return <= -exit_threshold:
                turbo_active = False
                multiplier = 1.0
                exit_time = timestamp
                exit_reason = f'Daily drop {daily_return*100:.2f}%'
            
            # 결과 저장
            results.append({
                'timestamp': timestamp,
                'price': current_price,
                'daily_return': daily_return,
                'equity': equity,
                'turbo_active': turbo_active,
                'multiplier': multiplier,
                'exit_time': exit_time,
                'exit_reason': exit_reason,
                'version': version
            })
    
    return pd.DataFrame(results)

def main():
    print("="*80)
    print("1분 데이터 Turbo V2.1/V2.2 일중 백테스트")
    print("="*80)
    
    # 종목 설정
    symbol = '005930'  # 삼성전자
    symbol_name = '삼성전자'
    
    print(f"\n📊 종목: {symbol_name} ({symbol})")
    print(f"📁 데이터 로드 중...")
    
    try:
        df = load_minute_data(symbol)
        print(f"✅ 데이터 로드 완료: {len(df):,} rows")
        print(f"   기간: {df['timestamp'].min()} ~ {df['timestamp'].max()}")
    except Exception as e:
        print(f"❌ 데이터 로드 실패: {e}")
        return
    
    # 테스트 기간 선택 (최근 5일)
    latest_date = df['timestamp'].max().date()
    start_date = latest_date - timedelta(days=7)
    
    test_df = df[df['timestamp'].dt.date >= start_date].copy()
    print(f"\n🔍 테스트 기간: {start_date} ~ {latest_date} ({len(test_df):,} rows)")
    
    if len(test_df) < 100:
        print(f"⚠️  데이터가 부족합니다 ({len(test_df)} rows). 전체 데이터로 테스트합니다.")
        test_df = df.copy()
    
    # V2.1 시뮬레이션 (-2% exit)
    print(f"\n🚀 V2.1 시뮬레이션 실행 중 (Exit: -2%)...")
    sim_v2_1 = simulate_intraday_turbo(test_df, exit_threshold=0.02, version='V2.1')
    
    # V2.2 시뮬레이션 (-1.5% exit)
    print(f"🚀 V2.2 시뮬레이션 실행 중 (Exit: -1.5%)...")
    sim_v2_2 = simulate_intraday_turbo(test_df, exit_threshold=0.015, version='V2.2')
    
    # 성과 계산
    v2_1_final = sim_v2_1['equity'].iloc[-1]
    v2_2_final = sim_v2_2['equity'].iloc[-1]
    
    v2_1_return = (v2_1_final / 100_000_000 - 1) * 100
    v2_2_return = (v2_2_final / 100_000_000 - 1) * 100
    
    v2_1_exits = sim_v2_1[sim_v2_1['exit_reason'] != '']['exit_reason'].count()
    v2_2_exits = sim_v2_2[sim_v2_2['exit_reason'] != '']['exit_reason'].count()
    
    # 결과 출력
    print(f"\n{'='*80}")
    print(f"📈 성과 요약")
    print(f"{'='*80}")
    print(f"{'버전':<15} {'최종 자산':<20} {'수익률':<15} {'Exit 횟수':<15}")
    print(f"{'-'*80}")
    print(f"{'V2.1 (-2%)':<15} ₩{v2_1_final:>17,.0f} {v2_1_return:>13.2f}% {v2_1_exits:>13}회")
    print(f"{'V2.2 (-1.5%)':<15} ₩{v2_2_final:>17,.0f} {v2_2_return:>13.2f}% {v2_2_exits:>13}회")
    print(f"{'-'*80}")
    
    diff_return = v2_2_return - v2_1_return
    diff_symbol = '+' if diff_return >= 0 else ''
    print(f"{'차이':<15} ₩{v2_2_final - v2_1_final:>17,.0f} {diff_symbol}{diff_return:>12.2f}% {v2_2_exits - v2_1_exits:>+13}회")
    
    # Exit 이벤트 출력
    v2_1_exit_events = sim_v2_1[sim_v2_1['exit_reason'] != ''].drop_duplicates('exit_time')
    v2_2_exit_events = sim_v2_2[sim_v2_2['exit_reason'] != ''].drop_duplicates('exit_time')
    
    print(f"\n{'='*80}")
    print(f"🚨 Exit 이벤트")
    print(f"{'='*80}")
    
    print(f"\n V2.1 Exit ({len(v2_1_exit_events)}회):")
    for _, event in v2_1_exit_events.iterrows():
        print(f"   {event['exit_time']}: {event['exit_reason']}")
    
    print(f"\n V2.2 Exit ({len(v2_2_exit_events)}회):")
    for _, event in v2_2_exit_events.iterrows():
        print(f"   {event['exit_time']}: {event['exit_reason']}")
    
    # 시각화
    print(f"\n📊 차트 생성 중...")
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 10))
    
    # Plot 1: Equity Curves
    ax1 = axes[0, 0]
    ax1.plot(sim_v2_1['timestamp'], sim_v2_1['equity'], label='V2.1 (-2%)', linewidth=2, color='#3498DB', alpha=0.8)
    ax1.plot(sim_v2_2['timestamp'], sim_v2_2['equity'], label='V2.2 (-1.5%)', linewidth=2, color='#2ECC71', alpha=0.9)
    ax1.axhline(y=100_000_000, color='gray', linestyle='--', alpha=0.5, label='시작')
    
    # Exit 마커
    if len(v2_1_exit_events) > 0:
        ax1.scatter(v2_1_exit_events['exit_time'], v2_1_exit_events['equity'], 
                   s=100, color='#3498DB', marker='v', zorder=5, label='V2.1 Exit')
    if len(v2_2_exit_events) > 0:
        ax1.scatter(v2_2_exit_events['exit_time'], v2_2_exit_events['equity'], 
                   s=100, color='#2ECC71', marker='v', zorder=5, label='V2.2 Exit')
    
    ax1.set_title(f'{symbol_name} 일중 성과 (V2.1 vs V2.2)', fontsize=14, fontweight='bold')
    ax1.set_ylabel('자산 (원)', fontsize=11)
    ax1.legend(fontsize=9)
    ax1.grid(True, alpha=0.3)
    ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'₩{x/1e6:.0f}M'))
    
    # Plot 2: Price Chart
    ax2 = axes[0, 1]
    ax2.plot(test_df['timestamp'], test_df['close'], linewidth=1, color='black', alpha=0.7)
    ax2.set_title(f'{symbol_name} 가격 추이', fontsize=12, fontweight='bold')
    ax2.set_ylabel('가격 (원)', fontsize=10)
    ax2.grid(True, alpha=0.3)
    
    # Plot 3: Multiplier Comparison
    ax3 = axes[1, 0]
    ax3.plot(sim_v2_1['timestamp'], sim_v2_1['multiplier'], linewidth=1.5, color='#3498DB', label='V2.1', alpha=0.7)
    ax3.plot(sim_v2_2['timestamp'], sim_v2_2['multiplier'], linewidth=1.5, color='#2ECC71', label='V2.2', alpha=0.9)
    ax3.axhline(y=1.0, color='gray', linestyle='--', alpha=0.5)
    ax3.axhline(y=2.5, color='red', linestyle='--', alpha=0.5)
    ax3.set_ylabel('Multiplier', fontsize=10)
    ax3.set_title('Turbo Multiplier 변화', fontsize=12, fontweight='bold')
    ax3.legend(fontsize=9)
    ax3.grid(True, alpha=0.3)
    ax3.set_ylim(0.9, 2.7)
    
    # Plot 4: Summary Table
    ax4 = axes[1, 1]
    ax4.axis('off')
    
    table_data = [
        ['지표', 'V2.1 (-2%)', 'V2.2 (-1.5%)'],
        ['최종 수익률', f'{v2_1_return:.2f}%', f'{v2_2_return:.2f}%'],
        ['Exit 횟수', f'{v2_1_exits}회', f'{v2_2_exits}회'],
        ['최종 자산', f'₩{v2_1_final/1e6:.1f}M', f'₩{v2_2_final/1e6:.1f}M'],
    ]
    
    table = ax4.table(cellText=table_data, cellLoc='center', loc='center',
                     colWidths=[0.35, 0.325, 0.325])
    table.auto_set_font_size(False)
    table.set_fontsize(11)
    table.scale(1, 3.0)
    
    # 헤더
    for i in range(3):
        table[(0, i)].set_facecolor('#34495E')
        table[(0, i)].set_text_props(weight='bold', color='white')
    
    # V2.2 열 강조
    for i in range(1, 4):
        table[(i, 2)].set_facecolor('#D5F4E6')
        table[(i, 2)].set_text_props(weight='bold')
    
    ax4.set_title('성과 요약', fontsize=14, fontweight='bold', pad=20)
    
    plt.suptitle(f'1분 데이터 Turbo 백테스트: {symbol_name} ({start_date} ~ {latest_date})', 
                fontsize=16, fontweight='bold', y=0.995)
    
    plt.tight_layout()
    
    # 저장
    output_dir = Path('c:/garam/garam/logs')
    output_dir.mkdir(exist_ok=True, parents=True)
    
    chart_path = output_dir / 'intraday_turbo_comparison.png'
    plt.savefig(chart_path, dpi=150, bbox_inches='tight')
    print(f"✅ 차트 저장: {chart_path}")
    
    # CSV 저장
    combined_df = pd.concat([
        sim_v2_1[['timestamp', 'equity', 'turbo_active', 'exit_reason']].rename(columns={
            'equity': 'v2_1_equity',
            'turbo_active': 'v2_1_active',
            'exit_reason': 'v2_1_exit'
        }),
        sim_v2_2[['equity', 'turbo_active', 'exit_reason']].rename(columns={
            'equity': 'v2_2_equity',
            'turbo_active': 'v2_2_active',
            'exit_reason': 'v2_2_exit'
        })
    ], axis=1)
    
    csv_path = output_dir / 'intraday_turbo_comparison.csv'
    combined_df.to_csv(csv_path, index=False, encoding='utf-8-sig')
    print(f"✅ 데이터 저장: {csv_path}")
    
    print(f"\n{'='*80}")
    print(f"✅ 백테스트 완료!")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    main()
