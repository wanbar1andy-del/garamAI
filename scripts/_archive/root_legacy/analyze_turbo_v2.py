#!/usr/bin/env python3
"""
Turbo Overlay V2 시뮬레이션
V2: 빠른 Exit + 신중한 재진입
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

def calculate_mdd(equity_series):
    """MDD 계산"""
    cummax = equity_series.cummax()
    dd = (equity_series - cummax) / cummax
    return dd.min()

def calculate_concentration(positions_count):
    """포지션 수에 따른 집중도 추정"""
    if positions_count <= 0:
        return 0.0
    elif positions_count == 1:
        return 1.0
    elif positions_count == 2:
        return 1.0
    elif positions_count == 3:
        return 0.75
    elif positions_count == 4:
        return 0.65
    elif positions_count == 5:
        return 0.60
    else:
        return 0.50

def get_turbo_multiplier(concentration, max_mult=2.5):
    """집중도에 따른 Turbo multiplier"""
    min_concentration = 0.5
    
    if concentration < min_concentration:
        return 1.0
    
    multiplier = 1.0 + (max_mult - 1.0) * ((concentration - min_concentration) / (1.0 - min_concentration))
    
    return multiplier

def simulate_turbo_v2(df):
    """
    Turbo Overlay V2 시뮬레이션
    
    V2 핵심 개선:
    1. Exit: daily_return <= -3% 시 즉시 Turbo OFF
    2. 재진입 조건:
       - 3일 쿨다운
       - DD 50% 이상 회복
       - 최근 2-3일 수익률 합 >= +3% 또는 당일 >= +2%
       - 집중도 >= 0.8 유지
    """
    df = df.copy()
    
    df['turbo_active_v2'] = False
    df['concentration'] = 0.0
    df['turbo_multiplier_v2'] = 1.0
    df['turbo_equity_v2'] = df['equity'].copy()
    df['exit_reason'] = ''
    df['reentry_reason'] = ''
    
    equity = 100_000_000
    is_turbo_active = False
    turbo_off_date = None
    turbo_off_dd = 0  # Turbo OFF 당시 DD
    turbo_off_equity = equity
    portfolio_high = equity
    
    recent_returns = []  # 최근 3일 수익률
    
    for idx in range(len(df)):
        row = df.iloc[idx]
        date = row['date']
        
        # 집중도 계산
        concentration = calculate_concentration(row['positions_count'])
        df.loc[df.index[idx], 'concentration'] = concentration
        
        # 최근 수익률 추적 (rolling 3일)
        recent_returns.append(row['daily_return'])
        if len(recent_returns) > 3:
            recent_returns.pop(0)
        
        # Turbo 기본 활성화 조건
        regime_ok = True  # 임시 (실제로는 regime 체크)
        can_activate_turbo = regime_ok and concentration >= 0.5
        
        # === V2 EXIT 조건 ===
        if is_turbo_active:
            multiplier = get_turbo_multiplier(concentration)
            
            # Exit 조건 1: 단일일 급락 -3%
            if multiplier >= 2.0 and row['daily_return'] <= -0.03:
                is_turbo_active = False
                turbo_off_date = date
                turbo_off_equity = equity
                turbo_off_dd = (equity - portfolio_high) / portfolio_high if portfolio_high > 0 else 0
                df.loc[df.index[idx], 'exit_reason'] = f'Daily drop {row["daily_return"]*100:.1f}%'
                multiplier = 1.0
            
            # Exit 조건 2: 연속 하락 (3일 합 <= -4%)
            elif multiplier >= 2.0 and len(recent_returns) >= 3:
                sum_3d = sum(recent_returns)
                if sum_3d <= -0.04:
                    is_turbo_active = False
                    turbo_off_date = date
                    turbo_off_equity = equity
                    turbo_off_dd = (equity - portfolio_high) / portfolio_high if portfolio_high > 0 else 0
                    df.loc[df.index[idx], 'exit_reason'] = f'3-day decline {sum_3d*100:.1f}%'
                    multiplier = 1.0
        
        # === V2 재진입 조건 ===
        if not is_turbo_active and can_activate_turbo:
            # 쿨다운 체크
            if turbo_off_date is not None:
                days_since_exit = (pd.to_datetime(date) - pd.to_datetime(turbo_off_date)).days
                
                if days_since_exit >= 3:
                    # 재진입 조건 체크
                    current_dd = (equity - portfolio_high) / portfolio_high if portfolio_high > 0 else 0
                    
                    # 조건 1: DD 50% 이상 회복
                    if turbo_off_dd < 0:
                        recovery_ratio = 1 - (current_dd / turbo_off_dd)
                    else:
                        recovery_ratio = 1.0
                    
                    # 조건 2: 단기 모멘텀
                    recent_sum = sum(recent_returns[-2:]) if len(recent_returns) >= 2 else 0
                    momentum_ok = (recent_sum >= 0.03) or (row['daily_return'] >= 0.02)
                    
                    # 조건 3: 집중도 유지
                    concentration_ok = concentration >= 0.8
                    
                    # 재진입
                    if recovery_ratio >= 0.5 and momentum_ok and concentration_ok:
                        is_turbo_active = True
                        df.loc[df.index[idx], 'reentry_reason'] = f'Recovery {recovery_ratio*100:.0f}%, Mom {recent_sum*100:.1f}%'
            else:
                # 첫 진입
                if concentration >= 0.8:
                    is_turbo_active = True
                    df.loc[df.index[idx], 'reentry_reason'] = 'Initial entry'
        
        # Multiplier 계산
        if is_turbo_active and can_activate_turbo:
            multiplier = get_turbo_multiplier(concentration)
        else:
            multiplier = 1.0
        
        df.loc[df.index[idx], 'turbo_active_v2'] = is_turbo_active
        df.loc[df.index[idx], 'turbo_multiplier_v2'] = multiplier
        
        # Equity 계산
        turbo_return = row['daily_return'] * multiplier
        equity = equity * (1 + turbo_return)
        
        # 포트폴리오 고점 업데이트
        if equity > portfolio_high:
            portfolio_high = equity
        
        df.loc[df.index[idx], 'turbo_equity_v2'] = equity
    
    return df

def main():
    print("="*70)
    print("Turbo Overlay V2 분석")
    print("="*70)
    
    # 데이터 로드
    df = pd.read_csv('logs/daily_backtest_log.csv')
    df['date'] = pd.to_datetime(df['date'])
    
    # 기존 버전들
    from analyze_turbo_overlay import simulate_turbo_overlay
    df_v1 = simulate_turbo_overlay(df)
    
    from analyze_turbo_v1_1 import simulate_turbo_v1_1
    df_v1_1 = simulate_turbo_v1_1(df)
    
    # V2 시뮬레이션
    df_v2 = simulate_turbo_v2(df)
    
    # 성과 계산
    base_return = (df['equity'].iloc[-1] / 100_000_000 - 1) * 100
    base_mdd = calculate_mdd(df['equity']) * 100
    
    v1_return = (df_v1['turbo_equity'].iloc[-1] / 100_000_000 - 1) * 100
    v1_mdd = calculate_mdd(df_v1['turbo_equity']) * 100
    
    v1_1_return = (df_v1_1['turbo_equity_v1_1'].iloc[-1] / 100_000_000 - 1) * 100
    v1_1_mdd = calculate_mdd(df_v1_1['turbo_equity_v1_1']) * 100
    
    v2_return = (df_v2['turbo_equity_v2'].iloc[-1] / 100_000_000 - 1) * 100
    v2_mdd = calculate_mdd(df_v2['turbo_equity_v2']) * 100
    
    # 결과 출력
    print(f"\n{'='*70}")
    print(f"성과 비교")
    print(f"{'='*70}")
    print(f"{'Metric':<20} {'Base':<12} {'V1':<12} {'V1.1':<12} {'V2':<12}")
    print(f"{'-'*70}")
    print(f"{'수익률':<20} {base_return:>10.2f}% {v1_return:>10.2f}% {v1_1_return:>10.2f}% {v2_return:>10.2f}%")
    print(f"{'MDD':<20} {base_mdd:>10.2f}% {v1_mdd:>10.2f}% {v1_1_mdd:>10.2f}% {v2_mdd:>10.2f}%")
    
    base_sharpe = base_return / abs(base_mdd) if base_mdd != 0 else 0
    v1_sharpe = v1_return / abs(v1_mdd) if v1_mdd != 0 else 0
    v1_1_sharpe = v1_1_return / abs(v1_1_mdd) if v1_1_mdd != 0 else 0
    v2_sharpe = v2_return / abs(v2_mdd) if v2_mdd != 0 else 0
    
    print(f"{'Sharpe Approx':<20} {base_sharpe:>10.2f} {v1_sharpe:>10.2f} {v1_1_sharpe:>10.2f} {v2_sharpe:>10.2f}")
    
    # 9월 구간 상세 분석
    print(f"\n{'='*70}")
    print(f"9월 구간 상세 (V2 Exit/Re-entry)")
    print(f"{'='*70}")
    
    sep_df = df_v2[(df_v2['date'] >= '2025-09-15') & (df_v2['date'] <= '2025-10-05')]
    
    for idx, row in sep_df.iterrows():
        date_str = row['date'].strftime('%m/%d')
        equity_m = row['turbo_equity_v2'] / 1e6
        ret_pct = row['daily_return'] * 100
        mult = row['turbo_multiplier_v2']
        active = "🔥" if row['turbo_active_v2'] else "  "
        
        info = ""
        if row['exit_reason']:
            info = f" EXIT: {row['exit_reason']}"
        elif row['reentry_reason']:
            info = f" ENTRY: {row['reentry_reason']}"
        
        print(f"{active} {date_str}: {equity_m:6.1f}M ({ret_pct:+6.2f}%) Mult:{mult:.2f}x{info}")
    
    # Turbo 활성화 통계
    v2_active_days = df_v2['turbo_active_v2'].sum()
    v2_exit_count = (df_v2['exit_reason'] != '').sum()
    v2_reentry_count = (df_v2['reentry_reason'] != '').sum()
    
    print(f"\n{'='*70}")
    print(f"V2 통계")
    print(f"{'='*70}")
    print(f"Turbo 활성 일수: {v2_active_days}/{len(df_v2)} ({v2_active_days/len(df_v2)*100:.1f}%)")
    print(f"Exit 횟수: {v2_exit_count}")
    print(f"Re-entry 횟수: {v2_reentry_count}")
    print(f"평균 Multiplier (활성시): {df_v2[df_v2['turbo_active_v2']]['turbo_multiplier_v2'].mean():.2f}x")
    
    # 시각화
    fig, axes = plt.subplots(2, 2, figsize=(16, 10))
    
    # Plot 1: Equity Curves
    ax1 = axes[0, 0]
    ax1.plot(df['date'], df['equity'], label='Base 1.0x', linewidth=2, color='#2E86AB', alpha=0.9)
    ax1.plot(df_v1['date'], df_v1['turbo_equity'], label=f'V1 (+{v1_return:.1f}%)', linewidth=1.5, color='#A23B72', alpha=0.5)
    ax1.plot(df_v1_1['date'], df_v1_1['turbo_equity_v1_1'], label=f'V1.1 (+{v1_1_return:.1f}%)', linewidth=1.5, color='#F18F01', alpha=0.7)
    ax1.plot(df_v2['date'], df_v2['turbo_equity_v2'], label=f'V2 (+{v2_return:.1f}%)', linewidth=2, color='#06D6A0', alpha=0.9)
    
    ax1.set_title('Base vs V1 vs V1.1 vs V2 - Equity Curves', fontsize=14, fontweight='bold')
    ax1.set_ylabel('자산 (원)', fontsize=11)
    ax1.legend(loc='upper left', fontsize=10)
    ax1.grid(True, alpha=0.3)
    ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'₩{x/1e6:.0f}M'))
    
    # Plot 2: September Detail
    ax2 = axes[0, 1]
    sep_range = (df_v2['date'] >= '2025-09-01') & (df_v2['date'] <= '2025-10-10')
    ax2.plot(df_v2[sep_range]['date'], df_v2[sep_range]['turbo_equity_v2'], linewidth=2, color='#06D6A0', label='V2')
    ax2.plot(df_v1_1[sep_range]['date'], df_v1_1[sep_range]['turbo_equity_v1_1'], linewidth=1.5, color='#F18F01', alpha=0.7, label='V1.1')
    
    # Exit/Re-entry 마커
    exits = df_v2[sep_range & (df_v2['exit_reason'] != '')]
    entries = df_v2[sep_range & (df_v2['reentry_reason'] != '') & (df_v2['reentry_reason'] != 'Initial entry')]
    
    ax2.scatter(exits['date'], exits['turbo_equity_v2'], s=100, color='red', marker='v', label='Exit', zorder=5)
    ax2.scatter(entries['date'], entries['turbo_equity_v2'], s=100, color='green', marker='^', label='Re-entry', zorder=5)
    
    ax2.set_title('9월 구간 상세 (Exit/Re-entry)', fontsize=14, fontweight='bold')
    ax2.set_ylabel('자산 (원)', fontsize=11)
    ax2.legend(fontsize=9)
    ax2.grid(True, alpha=0.3)
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'₩{x/1e6:.0f}M'))
    
    # Plot 3: Multiplier Comparison
    ax3 = axes[1, 0]
    ax3.plot(df_v1_1['date'], df_v1_1['turbo_multiplier'], linewidth=1, color='#F18F01', alpha=0.5, label='V1.1')
    ax3.plot(df_v2['date'], df_v2['turbo_multiplier_v2'], linewidth=1.5, color='#06D6A0', label='V2')
    ax3.axhline(y=1.0, color='gray', linestyle='--', alpha=0.5)
    ax3.axhline(y=2.5, color='red', linestyle='--', alpha=0.5)
    ax3.set_ylabel('Multiplier', fontsize=11)
    ax3.set_title('Multiplier 비교 (V1.1 vs V2)', fontsize=12, fontweight='bold')
    ax3.legend(fontsize=10)
    ax3.grid(True, alpha=0.3)
    ax3.set_ylim(0.9, 2.7)
    
    # Plot 4: Summary Table
    ax4 = axes[1, 1]
    ax4.axis('off')
    
    table_data = [
        ['지표', 'Base', 'V1', 'V1.1', 'V2'],
        ['수익률', f'{base_return:.1f}%', f'{v1_return:.1f}%', f'{v1_1_return:.1f}%', f'{v2_return:.1f}%'],
        ['MDD', f'{base_mdd:.1f}%', f'{v1_mdd:.1f}%', f'{v1_1_mdd:.1f}%', f'{v2_mdd:.1f}%'],
        ['Sharpe', f'{base_sharpe:.2f}', f'{v1_sharpe:.2f}', f'{v1_1_sharpe:.2f}', f'{v2_sharpe:.2f}'],
        ['활성률', '-', f'{88.9:.1f}%', '-', f'{v2_active_days/len(df_v2)*100:.1f}%'],
    ]
    
    table = ax4.table(cellText=table_data, cellLoc='center', loc='center',
                     colWidths=[0.25, 0.19, 0.19, 0.19, 0.19])
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 2.5)
    
    # 헤더
    for i in range(5):
        table[(0, i)].set_facecolor('#4A90E2')
        table[(0, i)].set_text_props(weight='bold', color='white')
    
    # V2 열 강조
    for i in range(1, 5):
        table[(i, 4)].set_facecolor('#E6F9F5')
        table[(i, 4)].set_text_props(weight='bold')
    
    ax4.set_title('성과 요약', fontsize=14, fontweight='bold', pad=20)
    
    plt.suptitle('GARAM Turbo Overlay V2: Smart Exit/Re-entry', 
                fontsize=16, fontweight='bold', y=0.995)
    
    plt.tight_layout()
    
    # 저장
    output_path = 'logs/turbo_overlay_v2_comparison.png'
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"\n✅ Saved: {output_path}")
    
    # CSV 저장
    df_v2[['date', 'turbo_equity_v2', 'turbo_multiplier_v2', 'turbo_active_v2', 
           'exit_reason', 'reentry_reason', 'concentration']].to_csv(
        'logs/turbo_v2_simulation.csv', index=False)
    print(f"✅ Saved: logs/turbo_v2_simulation.csv")
    
    print(f"\n{'='*70}")
    print(f"✅ V2 분석 완료")
    print(f"{'='*70}\n")

if __name__ == "__main__":
    main()
