#!/usr/bin/env python3
"""
Stage 2: Adaptive Turbo Virtual Simulation
백분위 기반 가상 터보 시뮬레이션
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

def simulate_adaptive_turbo(df, percentile_high, percentile_low, turbo_mult, abs_mult):
    """
    백분위 기반 Adaptive Turbo 시뮬레이션
    
    Args:
        df: daily_backtest_log DataFrame
        percentile_high: Turbo 발동 백분위 (예: 0.8 = 상위 20%)
        percentile_low: ABS 발동 백분위 (예: 0.2 = 하위 20%)
        turbo_mult: Turbo 배율 (예: 2.0)
        abs_mult: ABS 배율 (예: 0.5)
    """
    df = df.copy()
    
    # Score 백분위 계산 (NaN 제외)
    valid_scores = df['final_score'].dropna()
    if len(valid_scores) == 0:
        # Score가 없으면 equity 증가율로 대체
        df['score_percentile'] = df['daily_return'].rank(pct=True)
    else:
        df['score_percentile'] = df['final_score'].rank(pct=True)
    
    # Adaptive multiplier 적용
    def get_mult(percentile):
        if pd.isna(percentile):
            return 1.0
        if percentile > percentile_high:
            return turbo_mult
        elif percentile < percentile_low:
            return abs_mult
        else:
            return 1.0
    
    df['multiplier'] = df['score_percentile'].apply(get_mult)
    df['adjusted_return'] = df['daily_return'] * df['multiplier']
    
    # Equity curve 계산
    df['equity_adaptive'] = (1 + df['adjusted_return']).cumprod() * 100_000_000
    
    # 성과 지표
    final_equity = df['equity_adaptive'].iloc[-1]
    total_return = (final_equity - 100_000_000) / 100_000_000
    mdd = calculate_mdd(df['equity_adaptive'])
    
    # Turbo/ABS 발동 통계
    turbo_days = (df['multiplier'] > 1.0).sum()
    abs_days = (df['multiplier'] < 1.0).sum()
    normal_days = (df['multiplier'] == 1.0).sum()
    
    return {
        'final_equity': final_equity,
        'return': total_return,
        'mdd': mdd,
        'turbo_days': turbo_days,
        'abs_days': abs_days,
        'normal_days': normal_days,
        'df': df
    }

def main():
    print("="*70)
    print("Stage 2: Adaptive Turbo 가상 시뮬레이션")
    print("="*70)
    
    # 데이터 로드
    df = pd.read_csv('logs/daily_backtest_log.csv')
    df['date'] = pd.to_datetime(df['date'])
    
    print(f"\n데이터: {len(df)} 거래일")
    print(f"Score 데이터: {df['final_score'].notna().sum()} 일")
    print(f"Base 최종 수익률: {(df['equity'].iloc[-1] / 100_000_000 - 1) * 100:.2f}%\n")
    
    # 시나리오 정의
    scenarios = [
        # (이름, percentile_high, percentile_low, turbo_mult, abs_mult)
        ('Top10_Turbo2.4', 0.90, 0.10, 2.4, 0.5),
        ('Top10_Turbo2.0', 0.90, 0.10, 2.0, 0.5),
        ('Top20_Turbo2.4', 0.80, 0.20, 2.4, 0.5),
        ('Top20_Turbo2.0', 0.80, 0.20, 2.0, 0.5),
        ('Top20_Turbo1.5', 0.80, 0.20, 1.5, 0.5),
        ('Top30_Turbo2.0', 0.70, 0.30, 2.0, 0.5),
        ('Top30_Turbo1.5', 0.70, 0.30, 1.5, 0.5),
        ('Conservative20', 0.80, 0.20, 1.5, 0.7),
        ('Aggressive10', 0.90, 0.10, 2.8, 0.3),
        ('Balanced25', 0.75, 0.25, 2.0, 0.6),
    ]
    
    # 시뮬레이션 실행
    results = []
    for name, p_high, p_low, t_mult, a_mult in scenarios:
        result = simulate_adaptive_turbo(df, p_high, p_low, t_mult, a_mult)
        results.append({
            'Scenario': name,
            'Return': result['return'],
            'MDD': result['mdd'],
            'Final_Equity': result['final_equity'],
            'Turbo_Days': result['turbo_days'],
            'ABS_Days': result['abs_days'],
            'Normal_Days': result['normal_days'],
            'Turbo_Pct': result['turbo_days'] / len(df) * 100,
            'ABS_Pct': result['abs_days'] / len(df) * 100,
            'Sharpe_Approx': result['return'] / abs(result['mdd']) if result['mdd'] != 0 else 0
        })
    
    # 결과 정리
    df_results = pd.DataFrame(results)
    df_results = df_results.sort_values('Return', ascending=False)
    
    print("="*70)
    print("시뮬레이션 결과")
    print("="*70)
    print(df_results[['Scenario', 'Return', 'MDD', 'Turbo_Pct', 'Sharpe_Approx']].to_string(index=False))
    
    # 상세 결과 저장
    df_results.to_csv('logs/adaptive_turbo_scenarios.csv', index=False)
    print(f"\n✅ Saved: logs/adaptive_turbo_scenarios.csv")
    
    # 최적 시나리오 선정 (Sharpe 기준)
    best = df_results.iloc[df_results['Sharpe_Approx'].idxmax()]
    print(f"\n{'='*70}")
    print("최적 시나리오 (Sharpe Ratio 기준)")
    print(f"{'='*70}")
    print(f"시나리오: {best['Scenario']}")
    print(f"수익률: {best['Return']:.1%}")
    print(f"MDD: {best['MDD']:.1%}")
    print(f"Turbo 발동: {best['Turbo_Pct']:.1f}% ({int(best['Turbo_Days'])}일)")
    print(f"ABS 발동: {best['ABS_Pct']:.1f}% ({int(best['ABS_Days'])}일)")
    print(f"Sharpe Approx: {best['Sharpe_Approx']:.2f}")
    
    # 상위 3개 시나리오 시각화
    top3_names = df_results.head(3)['Scenario'].tolist()
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
    
    # Plot 1: Equity Curves
    ax1.plot(df['date'], df['equity'], label='Base 1.0x', linewidth=2, color='gray', alpha=0.7)
    
    for i, name in enumerate(top3_names):
        scenario = [s for s in scenarios if s[0] == name][0]
        result = simulate_adaptive_turbo(df, scenario[1], scenario[2], scenario[3], scenario[4])
        ax1.plot(df['date'], result['df']['equity_adaptive'], 
                label=f"{name} ({result['return']:.1%})", linewidth=2, alpha=0.9)
    
    ax1.set_title('Base vs Adaptive Turbo 시나리오 (상위 3개)', fontsize=14, fontweight='bold')
    ax1.set_ylabel('자산 (원)', fontsize=12)
    ax1.legend(loc='upper left')
    ax1.grid(True, alpha=0.3)
    ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'₩{x/1e6:.0f}M'))
    
    # Plot 2: Return vs MDD
    ax2.scatter(df_results['MDD'] * 100, df_results['Return'] * 100, s=100, alpha=0.6)
    ax2.scatter(best['MDD'] * 100, best['Return'] * 100, s=200, color='red', marker='*', 
               label=f"Best: {best['Scenario']}", zorder=5)
    
    for idx, row in df_results.iterrows():
        ax2.annotate(row['Scenario'], (row['MDD'] * 100, row['Return'] * 100), 
                    fontsize=8, alpha=0.7, xytext=(5, 5), textcoords='offset points')
    
    ax2.axhline(y=71.6, color='gray', linestyle='--', alpha=0.5, label='Base +71.6%')
    ax2.set_xlabel('MDD (%)', fontsize=12)
    ax2.set_ylabel('총 수익률 (%)', fontsize=12)
    ax2.set_title('수익률 vs MDD (모든 시나리오)', fontsize=14)
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('logs/adaptive_turbo_analysis.png', dpi=150)
    print(f"✅ Saved: logs/adaptive_turbo_analysis.png")
    
    print(f"\n{'='*70}")
    print("✅ Stage 2 완료")
    print(f"{'='*70}\n")

if __name__ == "__main__":
    main()
