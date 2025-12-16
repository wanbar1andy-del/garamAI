#!/usr/bin/env python3
"""
Turbo Overlay V1.1 A/B 비교 시뮬레이션
V1.1: 포트폴리오 DD 스탑 + 가변 Trailing 추가
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# 한글 폰트
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

def simulate_turbo_v1_1(df, portfolio_dd_stop=0.18, tight_trailing=0.03, normal_trailing=0.05):
    """
    Turbo Overlay V1.1 시뮬레이션
    
    개선사항:
    - 포트폴리오 DD -18% 도달 시 전량 청산
    - 2.5x 구간: 3% trailing
    - 나머지: 5% trailing
    """
    df = df.copy()
    
    df['turbo_active'] = False
    df['concentration'] = 0.0
    df['turbo_multiplier'] = 1.0
    df['turbo_return'] = df['daily_return']
    df['turbo_equity_v1_1'] = df['equity']
    
    equity = 100_000_000
    portfolio_high = equity
    is_turbo_active = False
    position_highs = {}  # {symbol_idx: high_price}
    
    for idx in range(len(df)):
        row = df.iloc[idx]
        
        # 집중도 계산
        concentration = calculate_concentration(row['positions_count'])
        df.loc[df.index[idx], 'concentration'] = concentration
        
        # Turbo 활성화 조건
        regime_ok = True
        
        if regime_ok and concentration >= 0.5:
            multiplier = get_turbo_multiplier(concentration)
            
            # Exit 체크 전에 포트폴리오 DD 체크
            if equity > portfolio_high:
                portfolio_high = equity
            
            portfolio_dd = (equity - portfolio_high) / portfolio_high if portfolio_high > 0 else 0
            
            # Exit 조건들
            should_exit = False
            
            # 1. 포트폴리오 DD -18% 체크
            if portfolio_dd <= -portfolio_dd_stop:
                should_exit = True
                # print(f"  Portfolio DD Exit at {row['date']}: {portfolio_dd:.2%}")
            
            # 2. Trailing stop (가변)
            # 간단화: 일별 return 기반 추정
            if is_turbo_active:
                # 2.5x 구간: tight trailing
                if multiplier >= 2.0:
                    if row['daily_return'] <= -tight_trailing:
                        should_exit = True
                        # print(f"  Tight Trailing Exit at {row['date']}: {row['daily_return']:.2%}")
                # 나머지: normal trailing
                else:
                    if row['daily_return'] <= -normal_trailing:
                        should_exit = True
            
            if should_exit:
                # Turbo 청산
                is_turbo_active = False
                multiplier = 1.0
                # 쿨다운 없이 바로 재진입 가능 (간단화)
            
            if not is_turbo_active:
                is_turbo_active = True
            
            df.loc[df.index[idx], 'turbo_active'] = is_turbo_active
            df.loc[df.index[idx], 'turbo_multiplier'] = multiplier
            
            # Turbo return 적용
            turbo_return = row['daily_return'] * multiplier
            df.loc[df.index[idx], 'turbo_return'] = turbo_return
            
            equity = equity * (1 + turbo_return)
        else:
            # Base 그대로
            is_turbo_active = False
            equity = equity * (1 + row['daily_return'])
        
        df.loc[df.index[idx], 'turbo_equity_v1_1'] = equity
    
    return df

def main():
    print("="*70)
    print("Turbo Overlay V1 vs V1.1 비교")
    print("="*70)
    
    # 데이터 로드
    log_path = 'logs/daily_backtest_log.csv'
    if not Path(log_path).exists():
        print(f"❌ {log_path} not found.")
        return
    
    df = pd.read_csv(log_path)
    df['date'] = pd.to_datetime(df['date'])
    
    # V1 시뮬레이션 (기존)
    from analyze_turbo_overlay import simulate_turbo_overlay
    df_v1 = simulate_turbo_overlay(df)
    
    # V1.1 시뮬레이션 (개선)
    df_v1_1 = simulate_turbo_v1_1(df, portfolio_dd_stop=0.18, tight_trailing=0.03, normal_trailing=0.05)
    
    # 성과 계산
    base_return = (df['equity'].iloc[-1] / 100_000_000 - 1) * 100
    base_mdd = calculate_mdd(df['equity']) * 100
    
    v1_return = (df_v1['turbo_equity'].iloc[-1] / 100_000_000 - 1) * 100
    v1_mdd = calculate_mdd(df_v1['turbo_equity']) * 100
    
    v1_1_return = (df_v1_1['turbo_equity_v1_1'].iloc[-1] / 100_000_000 - 1) * 100
    v1_1_mdd = calculate_mdd(df_v1_1['turbo_equity_v1_1']) * 100
    
    # 결과 출력
    print(f"\n{'='*70}")
    print(f"성과 비교")
    print(f"{'='*70}")
    print(f"{'Metric':<20} {'Base 1.0x':<15} {'V1':<15} {'V1.1':<15}")
    print(f"{'-'*70}")
    print(f"{'수익률':<20} {base_return:>13.2f}% {v1_return:>13.2f}% {v1_1_return:>13.2f}%")
    print(f"{'MDD':<20} {base_mdd:>13.2f}% {v1_mdd:>13.2f}% {v1_1_mdd:>13.2f}%")
    
    base_sharpe = base_return / abs(base_mdd) if base_mdd != 0 else 0
    v1_sharpe = v1_return / abs(v1_mdd) if v1_mdd != 0 else 0
    v1_1_sharpe = v1_1_return / abs(v1_1_mdd) if v1_1_mdd != 0 else 0
    
    print(f"{'Sharpe Approx':<20} {base_sharpe:>13.2f} {v1_sharpe:>13.2f} {v1_1_sharpe:>13.2f}")
    
    print(f"\n{'='*70}")
    print(f"V1 → V1.1 개선")
    print(f"{'='*70}")
    print(f"수익률: {v1_return:.1f}% → {v1_1_return:.1f}% ({v1_1_return - v1_return:+.1f}%p)")
    print(f"MDD: {v1_mdd:.1f}% → {v1_1_mdd:.1f}% ({v1_1_mdd - v1_mdd:+.1f}%p)")
    print(f"Sharpe: {v1_sharpe:.2f} → {v1_1_sharpe:.2f} ({v1_1_sharpe - v1_sharpe:+.2f})")
    
    # 시각화
    fig, axes = plt.subplots(2, 2, figsize=(16, 10))
    
    # Plot 1: Equity Curves
    ax1 = axes[0, 0]
    ax1.plot(df['date'], df['equity'], label='Base 1.0x', linewidth=2, color='#2E86AB', alpha=0.9)
    ax1.plot(df_v1['date'], df_v1['turbo_equity'], label=f'V1 (+{v1_return:.1f}%)', linewidth=2, color='#A23B72', alpha=0.7)
    ax1.plot(df_v1_1['date'], df_v1_1['turbo_equity_v1_1'], label=f'V1.1 (+{v1_1_return:.1f}%)', linewidth=2, color='#F18F01', alpha=0.9)
    
    ax1.set_title(f'Base vs V1 vs V1.1 - Equity Curves', fontsize=14, fontweight='bold')
    ax1.set_ylabel('자산 (원)', fontsize=11)
    ax1.legend(loc='upper left', fontsize=10)
    ax1.grid(True, alpha=0.3)
    ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'₩{x/1e6:.0f}M'))
    
    # Plot 2: Drawdown Comparison
    ax2 = axes[0, 1]
    
    # Base DD
    base_cummax = df['equity'].cummax()
    base_dd = (df['equity'] - base_cummax) / base_cummax * 100
    
    # V1 DD
    v1_cummax = df_v1['turbo_equity'].cummax()
    v1_dd = (df_v1['turbo_equity'] - v1_cummax) / v1_cummax * 100
    
    # V1.1 DD
    v1_1_cummax = df_v1_1['turbo_equity_v1_1'].cummax()
    v1_1_dd = (df_v1_1['turbo_equity_v1_1'] - v1_1_cummax) / v1_1_cummax * 100
    
    ax2.fill_between(df['date'], 0, base_dd, alpha=0.3, color='#2E86AB', label=f'Base (MDD: {base_mdd:.1f}%)')
    ax2.plot(df_v1['date'], v1_dd, linewidth=1.5, color='#A23B72', alpha=0.7, label=f'V1 (MDD: {v1_mdd:.1f}%)')
    ax2.plot(df_v1_1['date'], v1_1_dd, linewidth=2, color='#F18F01', label=f'V1.1 (MDD: {v1_1_mdd:.1f}%)')
    
    ax2.axhline(y=-18, color='red', linestyle='--', alpha=0.5, label='V1.1 Portfolio DD Stop (-18%)')
    ax2.set_title('Drawdown 비교', fontsize=14, fontweight='bold')
    ax2.set_ylabel('Drawdown (%)', fontsize=11)
    ax2.legend(loc='lower left', fontsize=9)
    ax2.grid(True, alpha=0.3)
    
    # Plot 3: Return Distribution
    ax3 = axes[1, 0]
    ax3.hist(df['daily_return'] * 100, bins=50, alpha=0.5, color='#2E86AB', label='Base', density=True)
    ax3.hist(df_v1['turbo_return'] * 100, bins=50, alpha=0.5, color='#A23B72', label='V1', density=True)
    ax3.hist(df_v1_1['turbo_return'] * 100, bins=50, alpha=0.5, color='#F18F01', label='V1.1', density=True)
    ax3.set_xlabel('일별 수익률 (%)', fontsize=11)
    ax3.set_ylabel('밀도', fontsize=11)
    ax3.set_title('일별 수익률 분포', fontsize=12, fontweight='bold')
    ax3.legend(fontsize=10)
    ax3.grid(True, alpha=0.3, axis='y')
    
    # Plot 4: Summary Table
    ax4 = axes[1, 1]
    ax4.axis('off')
    
    table_data = [
        ['지표', 'Base', 'V1', 'V1.1'],
        ['수익률', f'{base_return:.1f}%', f'{v1_return:.1f}%', f'{v1_1_return:.1f}%'],
        ['MDD', f'{base_mdd:.1f}%', f'{v1_mdd:.1f}%', f'{v1_1_mdd:.1f}%'],
        ['Sharpe', f'{base_sharpe:.2f}', f'{v1_sharpe:.2f}', f'{v1_1_sharpe:.2f}'],
        ['수익/MDD', f'{base_return/abs(base_mdd):.2f}', f'{v1_return/abs(v1_mdd):.2f}', f'{v1_1_return/abs(v1_1_mdd):.2f}'],
    ]
    
    table = ax4.table(cellText=table_data, cellLoc='center', loc='center',
                     colWidths=[0.3, 0.23, 0.23, 0.23])
    table.auto_set_font_size(False)
    table.set_fontsize(11)
    table.scale(1, 2.5)
    
    # 헤더 스타일
    for i in range(4):
        table[(0, i)].set_facecolor('#4A90E2')
        table[(0, i)].set_text_props(weight='bold', color='white')
    
    # V1.1 열 강조
    for i in range(1, 5):
        table[(i, 3)].set_facecolor('#FFF4E6')
        table[(i, 3)].set_text_props(weight='bold')
    
    ax4.set_title('성과 요약', fontsize=14, fontweight='bold', pad=20)
    
    plt.suptitle('GARAM Turbo Overlay V1.1 개선 분석', 
                fontsize=16, fontweight='bold', y=0.995)
    
    plt.tight_layout()
    
    # 저장
    output_path = 'logs/turbo_overlay_v1_1_comparison.png'
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"\n✅ Saved: {output_path}")
    
    # CSV 저장
    comparison_df = pd.DataFrame({
        'date': df['date'],
        'base_equity': df['equity'],
        'v1_equity': df_v1['turbo_equity'],
        'v1_1_equity': df_v1_1['turbo_equity_v1_1'],
        'v1_1_multiplier': df_v1_1['turbo_multiplier'],
        'concentration': df_v1_1['concentration']
    })
    comparison_df.to_csv('logs/turbo_v1_v1_1_comparison.csv', index=False)
    print(f"✅ Saved: logs/turbo_v1_v1_1_comparison.csv")
    
    print(f"\n{'='*70}")
    print(f"✅ V1.1 분석 완료")
    print(f"{'='*70}\n")

if __name__ == "__main__":
    main()
