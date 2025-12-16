#!/usr/bin/env python3
"""
Turbo Overlay V2 / V2.1 / V2.2 종합 비교
실제 데이터로 AB 테스트
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# 모듈 임포트
from analyze_turbo_v2 import simulate_turbo_v2
from analyze_turbo_v2_1 import simulate_turbo_v2_1
from analyze_turbo_v2_2 import simulate_turbo_v2_2

plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

def calculate_mdd(equity_series):
    """MDD 계산"""
    cummax = equity_series.cummax()
    dd = (equity_series - cummax) / cummax
    return dd.min()

def main():
    print("="*80)
    print("GARAM Turbo Overlay V2/V2.1/V2.2 종합 AB 테스트")
    print("="*80)
    
    # 데이터 로드
    print("\n📊 데이터 로드 중...")
    df = pd.read_csv('logs/daily_backtest_log.csv')
    df['date'] = pd.to_datetime(df['date'])
    print(f"✅ 데이터 로드 완료: {len(df)} 거래일")
    
    # 시뮬레이션 실행
    print("\n🚀 시뮬레이션 실행 중...")
    print("  - V2 (Exit -3%)...")
    df_v2 = simulate_turbo_v2(df)
    print("  - V2.1 (Exit -2%)...")
    df_v2_1 = simulate_turbo_v2_1(df)
    print("  - V2.2 (Exit -1.5%)...")
    df_v2_2 = simulate_turbo_v2_2(df)
    print("✅ 시뮬레이션 완료")
    
    # 성과 계산
    base_return = (df['equity'].iloc[-1] / 100_000_000 - 1) * 100
    base_mdd = calculate_mdd(df['equity']) * 100
    
    v2_return = (df_v2['turbo_equity_v2'].iloc[-1] / 100_000_000 - 1) * 100
    v2_mdd = calculate_mdd(df_v2['turbo_equity_v2']) * 100
    
    v2_1_return = (df_v2_1['turbo_equity_v2_1'].iloc[-1] / 100_000_000 - 1) * 100
    v2_1_mdd = calculate_mdd(df_v2_1['turbo_equity_v2_1']) * 100
    
    v2_2_return = (df_v2_2['turbo_equity_v2_2'].iloc[-1] / 100_000_000 - 1) * 100
    v2_2_mdd = calculate_mdd(df_v2_2['turbo_equity_v2_2']) * 100
    
    # Sharpe 계산
    base_sharpe = base_return / abs(base_mdd) if base_mdd != 0 else 0
    v2_sharpe = v2_return / abs(v2_mdd) if v2_mdd != 0 else 0
    v2_1_sharpe = v2_1_return / abs(v2_1_mdd) if v2_1_mdd != 0 else 0
    v2_2_sharpe = v2_2_return / abs(v2_2_mdd) if v2_2_mdd != 0 else 0
    
    # Exit 통계
    v2_exits = (df_v2['exit_reason'] != '').sum()
    v2_1_exits = (df_v2_1['exit_reason_v2_1'] != '').sum()
    v2_2_exits = (df_v2_2['exit_reason_v2_2'] != '').sum()
    
    v2_active_days = df_v2['turbo_active_v2'].sum()
    v2_1_active_days = df_v2_1['turbo_active_v2_1'].sum()
    v2_2_active_days = df_v2_2['turbo_active_v2_2'].sum()
    
    # 결과 출력
    print(f"\n{'='*80}")
    print(f"📈 성과 비교")
    print(f"{'='*80}")
    print(f"{'Metric':<20} {'Base':<15} {'V2 (-3%)':<15} {'V2.1 (-2%)':<15} {'V2.2 (-1.5%)':<15}")
    print(f"{'-'*80}")
    print(f"{'최종 수익률':<20} {base_return:>13.2f}% {v2_return:>13.2f}% {v2_1_return:>13.2f}% {v2_2_return:>13.2f}%")
    print(f"{'MDD':<20} {base_mdd:>13.2f}% {v2_mdd:>13.2f}% {v2_1_mdd:>13.2f}% {v2_2_mdd:>13.2f}%")
    print(f"{'Sharpe Ratio':<20} {base_sharpe:>13.2f} {v2_sharpe:>13.2f} {v2_1_sharpe:>13.2f} {v2_2_sharpe:>13.2f}")
    print(f"{'Exit 횟수':<20} {'-':>13} {v2_exits:>13} {v2_1_exits:>13} {v2_2_exits:>13}")
    print(f"{'활성 일수':<20} {'-':>13} {v2_active_days:>13} {v2_1_active_days:>13} {v2_2_active_days:>13}")
    print(f"{'활성률':<20} {'-':>13} {v2_active_days/len(df)*100:>12.1f}% {v2_1_active_days/len(df)*100:>12.1f}% {v2_2_active_days/len(df)*100:>12.1f}%")
    
    # 개선 효과
    print(f"\n{'='*80}")
    print(f"💡 V2 대비 개선 효과")
    print(f"{'='*80}")
    print(f"{'Metric':<30} {'V2.1':<20} {'V2.2':<20}")
    print(f"{'-'*80}")
    print(f"{'수익률 차이':<30} {v2_1_return - v2_return:>+18.2f}% {v2_2_return - v2_return:>+18.2f}%")
    print(f"{'MDD 개선':<30} {v2_1_mdd - v2_mdd:>+18.2f}% {v2_2_mdd - v2_mdd:>+18.2f}%")
    print(f"{'Sharpe 개선':<30} {v2_1_sharpe - v2_sharpe:>+18.2f} {v2_2_sharpe - v2_sharpe:>+18.2f}")
    print(f"{'Exit 횟수 증가':<30} {v2_1_exits - v2_exits:>+18} {v2_2_exits - v2_exits:>+18}")
    
    # 9월 구간 상세 분석
    print(f"\n{'='*80}")
    print(f"🔍 9월 급락 구간 상세 분석 (2025-09-15 ~ 2025-10-05)")
    print(f"{'='*80}")
    
    sep_mask = (df_v2['date'] >= '2025-09-15') & (df_v2['date'] <= '2025-10-05')
    sep_dates = df_v2[sep_mask]
    
    print(f"\n{'Date':<12} {'V2 Equity':<15} {'V2.1 Equity':<15} {'V2.2 Equity':<15} {'Events':<40}")
    print(f"{'-'*100}")
    
    for idx, row in sep_dates.iterrows():
        v2_row = df_v2.loc[idx]
        v2_1_row = df_v2_1.loc[idx]
        v2_2_row = df_v2_2.loc[idx]
        
        date_str = v2_row['date'].strftime('%Y-%m-%d')
        v2_eq = v2_row['turbo_equity_v2'] / 1e6
        v2_1_eq = v2_1_row['turbo_equity_v2_1'] / 1e6
        v2_2_eq = v2_2_row['turbo_equity_v2_2'] / 1e6
        
        events = []
        if v2_row['exit_reason']:
            events.append(f"V2:EXIT({v2_row['exit_reason']})")
        if v2_1_row['exit_reason_v2_1']:
            events.append(f"V2.1:EXIT({v2_1_row['exit_reason_v2_1']})")
        if v2_2_row['exit_reason_v2_2']:
            events.append(f"V2.2:EXIT({v2_2_row['exit_reason_v2_2']})")
        
        event_str = " | ".join(events) if events else ""
        
        print(f"{date_str:<12} ₩{v2_eq:>7.1f}M      ₩{v2_1_eq:>7.1f}M      ₩{v2_2_eq:>7.1f}M      {event_str}")
    
    # 시각화
    print(f"\n📊 차트 생성 중...")
    fig = plt.figure(figsize=(20, 12))
    gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
    
    # Plot 1: Full Equity Curves
    ax1 = fig.add_subplot(gs[0, :])
    ax1.plot(df['date'], df['equity'], label='Base 1.0x', linewidth=2, color='#95A5A6', alpha=0.6)
    ax1.plot(df_v2['date'], df_v2['turbo_equity_v2'], label=f'V2 (-3%): +{v2_return:.1f}%', linewidth=2, color='#3498DB', alpha=0.8)
    ax1.plot(df_v2_1['date'], df_v2_1['turbo_equity_v2_1'], label=f'V2.1 (-2%): +{v2_1_return:.1f}%', linewidth=2, color='#2ECC71', alpha=0.9)
    ax1.plot(df_v2_2['date'], df_v2_2['turbo_equity_v2_2'], label=f'V2.2 (-1.5%): +{v2_2_return:.1f}%', linewidth=2, color='#E74C3C', alpha=0.9)
    
    ax1.set_title('Turbo Overlay V2 / V2.1 / V2.2 - Full Performance', fontsize=16, fontweight='bold')
    ax1.set_ylabel('자산 (원)', fontsize=12)
    ax1.legend(loc='upper left', fontsize=11)
    ax1.grid(True, alpha=0.3)
    ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'₩{x/1e6:.0f}M'))
    
    # Plot 2: September Detail
    ax2 = fig.add_subplot(gs[1, 0])
    sep_range = (df_v2['date'] >= '2025-09-01') & (df_v2['date'] <= '2025-10-10')
    ax2.plot(df_v2[sep_range]['date'], df_v2[sep_range]['turbo_equity_v2'], linewidth=2, color='#3498DB', label='V2', alpha=0.7)
    ax2.plot(df_v2_1[sep_range]['date'], df_v2_1[sep_range]['turbo_equity_v2_1'], linewidth=2, color='#2ECC71', label='V2.1')
    ax2.plot(df_v2_2[sep_range]['date'], df_v2_2[sep_range]['turbo_equity_v2_2'], linewidth=2, color='#E74C3C', label='V2.2', linestyle='--')
    
    # Exit markers
    v2_exits_sep = df_v2[sep_range & (df_v2['exit_reason'] != '')]
    v2_1_exits_sep = df_v2_1[sep_range & (df_v2_1['exit_reason_v2_1'] != '')]
    v2_2_exits_sep = df_v2_2[sep_range & (df_v2_2['exit_reason_v2_2'] != '')]
    
    ax2.scatter(v2_exits_sep['date'], v2_exits_sep['turbo_equity_v2'], s=80, color='#3498DB', marker='v', zorder=5)
    ax2.scatter(v2_1_exits_sep['date'], v2_1_exits_sep['turbo_equity_v2_1'], s=80, color='#2ECC71', marker='v', zorder=5)
    ax2.scatter(v2_2_exits_sep['date'], v2_2_exits_sep['turbo_equity_v2_2'], s=80, color='#E74C3C', marker='v', zorder=5)
    
    ax2.set_title('9월 급락 구간 (Exit 비교)', fontsize=12, fontweight='bold')
    ax2.set_ylabel('자산', fontsize=10)
    ax2.legend(fontsize=9)
    ax2.grid(True, alpha=0.3)
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x/1e6:.0f}M'))
    
    # Plot 3: MDD Comparison
    ax3 = fig.add_subplot(gs[1, 1])
    mdds = [abs(base_mdd), abs(v2_mdd), abs(v2_1_mdd), abs(v2_2_mdd)]
    labels = ['Base', 'V2\n(-3%)', 'V2.1\n(-2%)', 'V2.2\n(-1.5%)']
    colors = ['#95A5A6', '#3498DB', '#2ECC71', '#E74C3C']
    
    bars = ax3.bar(labels, mdds, color=colors, alpha=0.8)
    ax3.set_title('MDD 비교', fontsize=12, fontweight='bold')
    ax3.set_ylabel('MDD (%)', fontsize=10)
    ax3.grid(True, alpha=0.3, axis='y')
    
    for i, (bar, mdd) in enumerate(zip(bars, mdds)):
        height = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width()/2., height,
                f'{mdd:.1f}%', ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    # Plot 4: Sharpe Comparison
    ax4 = fig.add_subplot(gs[1, 2])
    sharpes = [base_sharpe, v2_sharpe, v2_1_sharpe, v2_2_sharpe]
    
    bars = ax4.bar(labels, sharpes, color=colors, alpha=0.8)
    ax4.set_title('Sharpe Ratio 비교', fontsize=12, fontweight='bold')
    ax4.set_ylabel('Sharpe Ratio', fontsize=10)
    ax4.grid(True, alpha=0.3, axis='y')
    
    for i, (bar, sharpe) in enumerate(zip(bars, sharpes)):
        height = bar.get_height()
        ax4.text(bar.get_x() + bar.get_width()/2., height,
                f'{sharpe:.1f}', ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    # Plot 5: Return vs MDD Scatter
    ax5 = fig.add_subplot(gs[2, 0])
    scatter_data = [
        ('Base', base_return, abs(base_mdd), '#95A5A6', 100),
        ('V2', v2_return, abs(v2_mdd), '#3498DB', 150),
        ('V2.1', v2_1_return, abs(v2_1_mdd), '#2ECC71', 200),
        ('V2.2', v2_2_return, abs(v2_2_mdd), '#E74C3C', 150),
    ]
    
    for name, ret, mdd, color, size in scatter_data:
        ax5.scatter(mdd, ret, s=size, color=color, label=name, alpha=0.7, edgecolors='black')
    
    ax5.set_xlabel('MDD (%)', fontsize=10)
    ax5.set_ylabel('수익률 (%)', fontsize=10)
    ax5.set_title('수익률 vs MDD (우상단이 최적)', fontsize=12, fontweight='bold')
    ax5.legend(fontsize=9)
    ax5.grid(True, alpha=0.3)
    
    # Plot 6: Summary Table
    ax6 = fig.add_subplot(gs[2, 1:])
    ax6.axis('off')
    
    table_data = [
        ['지표', 'Base', 'V2 (-3%)', 'V2.1 (-2%)', 'V2.2 (-1.5%)'],
        ['수익률', f'{base_return:.1f}%', f'{v2_return:.1f}%', f'{v2_1_return:.1f}%', f'{v2_2_return:.1f}%'],
        ['MDD', f'{base_mdd:.1f}%', f'{v2_mdd:.1f}%', f'{v2_1_mdd:.1f}%', f'{v2_2_mdd:.1f}%'],
        ['Sharpe', f'{base_sharpe:.2f}', f'{v2_sharpe:.2f}', f'{v2_1_sharpe:.2f}', f'{v2_2_sharpe:.2f}'],
        ['Exit 횟수', '-', f'{v2_exits}회', f'{v2_1_exits}회', f'{v2_2_exits}회'],
        ['활성률', '-', f'{v2_active_days/len(df)*100:.1f}%', f'{v2_1_active_days/len(df)*100:.1f}%', f'{v2_2_active_days/len(df)*100:.1f}%'],
    ]
    
    table = ax6.table(cellText=table_data, cellLoc='center', loc='center',
                     colWidths=[0.20, 0.20, 0.20, 0.20, 0.20])
    table.auto_set_font_size(False)
    table.set_fontsize(11)
    table.scale(1, 2.8)
    
    # 헤더
    for i in range(5):
        table[(0, i)].set_facecolor('#34495E')
        table[(0, i)].set_text_props(weight='bold', color='white')
    
    # V2.1 열 강조
    for i in range(1, 6):
        table[(i, 3)].set_facecolor('#D5F4E6')
        table[(i, 3)].set_text_props(weight='bold')
    
    ax6.set_title('성과 요약 (V2.1 권장)', fontsize=14, fontweight='bold', pad=20)
    
    plt.suptitle('GARAM Turbo Overlay AB Test: V2 vs V2.1 vs V2.2', 
                fontsize=18, fontweight='bold', y=0.995)
    
    # 저장
    output_path = 'logs/turbo_v2_comprehensive_comparison.png'
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"✅ 차트 저장: {output_path}")
    
    # CSV 저장
    comparison_df = pd.DataFrame({
        'date': df['date'],
        'base_equity': df['equity'],
        'v2_equity': df_v2['turbo_equity_v2'],
        'v2_1_equity': df_v2_1['turbo_equity_v2_1'],
        'v2_2_equity': df_v2_2['turbo_equity_v2_2'],
        'v2_exits': df_v2['exit_reason'],
        'v2_1_exits': df_v2_1['exit_reason_v2_1'],
        'v2_2_exits': df_v2_2['exit_reason_v2_2'],
    })
    
    comparison_df.to_csv('logs/turbo_v2_comprehensive_comparison.csv', index=False)
    print(f"✅ 데이터 저장: logs/turbo_v2_comprehensive_comparison.csv")
    
    print(f"\n{'='*80}")
    print(f"✅ AB 테스트 완료!")
    print(f"{'='*80}\n")
    
    # 권장 사항
    print(f"\n{'='*80}")
    print(f"🎯 권장 사항")
    print(f"{'='*80}")
    
    if v2_1_sharpe > v2_sharpe and v2_1_sharpe > v2_2_sharpe:
        print(f"✅ 최종 권장: V2.1 (-2% Exit)")
        print(f"   이유: 최고 Sharpe Ratio ({v2_1_sharpe:.2f}), MDD {v2_1_mdd:.1f}%로 안정적")
    elif v2_2_sharpe > v2_sharpe and v2_2_sharpe > v2_1_sharpe:
        print(f"✅ 최종 권장: V2.2 (-1.5% Exit)")
        print(f"   이유: 최고 Sharpe Ratio ({v2_2_sharpe:.2f}), MDD {v2_2_mdd:.1f}%로 초보수적")
    else:
        print(f"✅ 최종 권장: V2 (-3% Exit, 기존)")
        print(f"   이유: 최고 수익률 ({v2_return:.1f}%), 충분한 안정성")
    
    print(f"{'='*80}\n")

if __name__ == "__main__":
    main()
