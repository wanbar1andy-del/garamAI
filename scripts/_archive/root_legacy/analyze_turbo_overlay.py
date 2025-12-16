#!/usr/bin/env python3
"""
Base vs Turbo Overlay A/B 비교 시뮬레이션
일별 로그 데이터로 Turbo 가상 적용
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
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
    """
    포지션 수에 따른 집중도 추정
    
    실제로는 비중 정보가 필요하지만, 로그에 없으므로 휴리스틱 사용
    """
    if positions_count <= 0:
        return 0.0
    elif positions_count == 1:
        return 1.0
    elif positions_count == 2:
        return 1.0  # 2종목 = 최대 집중
    elif positions_count == 3:
        return 0.75  # 추정: top2가 75%
    elif positions_count == 4:
        return 0.65  # 추정: top2가 65%
    elif positions_count == 5:
        return 0.60  # 추정: top2가 60%
    else:
        return 0.50  # 6종목 이상: 분산

def get_turbo_multiplier(concentration, max_mult=2.5):
    """
    집중도에 따른 Turbo multiplier
    
    concentration 0.5 → 1.0x (No Turbo)
    concentration 1.0 → 2.5x (Max Turbo)
    """
    min_concentration = 0.5
    
    if concentration < min_concentration:
        return 1.0
    
    # 선형 보간
    multiplier = 1.0 + (max_mult - 1.0) * ((concentration - min_concentration) / (1.0 - min_concentration))
    
    return multiplier

def simulate_turbo_overlay(df, allowed_regimes=['R1_STRONG_UP', 'R2_UP']):
    """
    Turbo Overlay 가상 시뮬레이션
    """
    df = df.copy()
    
    # Turbo 활성화 조건 체크
    df['turbo_active'] = False
    df['concentration'] = 0.0
    df['turbo_multiplier'] = 1.0
    df['turbo_return'] = df['daily_return']
    df['turbo_equity'] = df['equity']
    
    equity = 100_000_000
    
    for idx in range(len(df)):
        row = df.iloc[idx]
        
        # 집중도 계산
        concentration = calculate_concentration(row['positions_count'])
        df.loc[df.index[idx], 'concentration'] = concentration
        
        # Regime 체크 (데이터에 없으므로 임시로 모두 허용)
        # 실제로는 regime 정보가 필요
        regime_ok = True  # 임시
        
        # Turbo 활성화
        if regime_ok and concentration >= 0.5:
            multiplier = get_turbo_multiplier(concentration)
            df.loc[df.index[idx], 'turbo_active'] = True
            df.loc[df.index[idx], 'turbo_multiplier'] = multiplier
            
            # Turbo return 적용
            turbo_return = row['daily_return'] * multiplier
            df.loc[df.index[idx], 'turbo_return'] = turbo_return
            
            equity = equity * (1 + turbo_return)
        else:
            # Base 그대로
            equity = equity * (1 + row['daily_return'])
        
        df.loc[df.index[idx], 'turbo_equity'] = equity
    
    return df

def main():
    print("="*70)
    print("Base vs Turbo Overlay A/B 비교")
    print("="*70)
    
    # 데이터 로드
    log_path = 'logs/daily_backtest_log.csv'
    if not Path(log_path).exists():
        print(f"❌ {log_path} not found. Run backtest first.")
        return
    
    df = pd.read_csv(log_path)
    df['date'] = pd.to_datetime(df['date'])
    
    print(f"\n데이터: {len(df)} 거래일")
    print(f"기간: {df['date'].min()} ~ {df['date'].max()}")
    
    # Base 성능
    base_return = (df['equity'].iloc[-1] / 100_000_000 - 1) * 100
    base_mdd = calculate_mdd(df['equity']) * 100
    
    # Turbo Overlay 시뮬레이션
    df_turbo = simulate_turbo_overlay(df)
    
    turbo_return = (df_turbo['turbo_equity'].iloc[-1] / 100_000_000 - 1) * 100
    turbo_mdd = calculate_mdd(df_turbo['turbo_equity']) * 100
    
    # 결과 출력
    print(f"\n{'='*70}")
    print(f"성과 비교")
    print(f"{'='*70}")
    print(f"{'Metric':<20} {'Base 1.0x':<20} {'Turbo Overlay':<20} {'Diff':<15}")
    print(f"{'-'*70}")
    print(f"{'수익률':<20} {base_return:>18.2f}% {turbo_return:>18.2f}% {turbo_return - base_return:>13.2f}%p")
    print(f"{'MDD':<20} {base_mdd:>18.2f}% {turbo_mdd:>18.2f}% {turbo_mdd - base_mdd:>13.2f}%p")
    
    base_sharpe = base_return / abs(base_mdd) if base_mdd != 0 else 0
    turbo_sharpe = turbo_return / abs(turbo_mdd) if turbo_mdd != 0 else 0
    
    print(f"{'Sharpe Approx':<20} {base_sharpe:>18.2f} {turbo_sharpe:>18.2f} {turbo_sharpe - base_sharpe:>13.2f}")
    
    # Turbo 활성화 통계
    turbo_days = df_turbo['turbo_active'].sum()
    total_days = len(df_turbo)
    turbo_pct = turbo_days / total_days * 100
    
    avg_concentration = df_turbo.loc[df_turbo['turbo_active'], 'concentration'].mean()
    avg_multiplier = df_turbo.loc[df_turbo['turbo_active'], 'turbo_multiplier'].mean()
    
    print(f"\n{'='*70}")
    print(f"Turbo 통계")
    print(f"{'='*70}")
    print(f"Turbo 활성화: {turbo_days}/{total_days} 일 ({turbo_pct:.1f}%)")
    print(f"평균 집중도: {avg_concentration:.1%} (Turbo 활성 시)")
    print(f"평균 Multiplier: {avg_multiplier:.2f}x")
    
    # 시각화
    fig = plt.figure(figsize=(16, 10))
    gs = fig.add_gridspec(3, 2, hspace=0.3, wspace=0.3)
    
    # Plot 1: Equity Curves
    ax1 = fig.add_subplot(gs[0, :])
    ax1.plot(df['date'], df['equity'], label='Base 1.0x', linewidth=2, color='#2E86AB', alpha=0.9)
    ax1.plot(df_turbo['date'], df_turbo['turbo_equity'], label=f'Turbo Overlay', linewidth=2, color='#A23B72', alpha=0.9)
    
    ax1.set_title(f'Base vs Turbo Overlay - Equity Curves\n(Base: +{base_return:.1f}%, MDD {base_mdd:.1f}% | Turbo: +{turbo_return:.1f}%, MDD {turbo_mdd:.1f}%)', 
                  fontsize=14, fontweight='bold', pad=15)
    ax1.set_ylabel('자산 (원)', fontsize=12)
    ax1.legend(loc='upper left', fontsize=11)
    ax1.grid(True, alpha=0.3)
    ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'₩{x/1e6:.0f}M'))
    
    # Plot 2: Daily Returns Comparison
    ax2 = fig.add_subplot(gs[1, 0])
    ax2.scatter(df['daily_return'] * 100, df_turbo['turbo_return'] * 100, alpha=0.3, s=10)
    ax2.plot([-10, 10], [-10, 10], 'r--', alpha=0.5, label='Base = Turbo')
    ax2.set_xlabel('Base Daily Return (%)', fontsize=11)
    ax2.set_ylabel('Turbo Daily Return (%)', fontsize=11)
    ax2.set_title('일별 수익률 비교', fontsize=12, fontweight='bold')
    ax2.legend(fontsize=9)
    ax2.grid(True, alpha=0.3)
    
    # Plot 3: Multiplier Over Time
    ax3 = fig.add_subplot(gs[1, 1])
    ax3.plot(df_turbo['date'], df_turbo['turbo_multiplier'], linewidth=1, color='#F18F01', alpha=0.7)
    ax3.fill_between(df_turbo['date'], 1, df_turbo['turbo_multiplier'], alpha=0.2, color='#F18F01')
    ax3.axhline(y=1.0, color='gray', linestyle='--', alpha=0.5, label='Base (1.0x)')
    ax3.axhline(y=2.5, color='red', linestyle='--', alpha=0.5, label='Max Turbo (2.5x)')
    ax3.set_ylabel('Multiplier', fontsize=11)
    ax3.set_title('Turbo Multiplier (집중도 기반)', fontsize=12, fontweight='bold')
    ax3.legend(fontsize=9)
    ax3.grid(True, alpha=0.3)
    ax3.set_ylim(0.9, 2.7)
    
    # Plot 4: Concentration Distribution
    ax4 = fig.add_subplot(gs[2, 0])
    ax4.hist(df_turbo['concentration'], bins=30, alpha=0.7, color='#6A994E', edgecolor='black')
    ax4.axvline(x=0.5, color='red', linestyle='--', alpha=0.7, label='Turbo 최소 임계값 (0.5)')
    ax4.set_xlabel('집중도', fontsize=11)
    ax4.set_ylabel('빈도', fontsize=11)
    ax4.set_title('집중도 분포', fontsize=12, fontweight='bold')
    ax4.legend(fontsize=9)
    ax4.grid(True, alpha=0.3, axis='y')
    
    # Plot 5: Position Count Over Time
    ax5 = fig.add_subplot(gs[2, 1])
    ax5.plot(df['date'], df['positions_count'], linewidth=1, color='#577590', alpha=0.7)
    ax5.fill_between(df['date'], 0, df['positions_count'], alpha=0.2, color='#577590')
    ax5.axhline(y=2, color='red', linestyle='--', alpha=0.5, label='2종목 (최대 집중)')
    ax5.set_ylabel('보유 종목 수', fontsize=11)
    ax5.set_title('보유 종목 수 추이', fontsize=12, fontweight='bold')
    ax5.legend(fontsize=9)
    ax5.grid(True, alpha=0.3)
    
    plt.suptitle(f'GARAM Turbo Overlay A/B Analysis', 
                fontsize=16, fontweight='bold', y=0.995)
    
    # 저장
    output_path = 'logs/turbo_overlay_ab_comparison.png'
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"\n✅ Saved: {output_path}")
    
    # CSV 저장
    df_turbo[['date', 'equity', 'turbo_equity', 'turbo_multiplier', 'concentration', 'positions_count']].to_csv(
        'logs/turbo_overlay_simulation.csv', index=False)
    print(f"✅ Saved: logs/turbo_overlay_simulation.csv")
    
    print(f"\n{'='*70}")
    print(f"✅ A/B 비교 분석 완료")
    print(f"{'='*70}\n")

if __name__ == "__main__":
    main()
