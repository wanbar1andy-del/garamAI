#!/usr/bin/env python3
"""
Comprehensive Performance Analysis
실제 백테스트 결과 + 기존 시뮬레이션 상세 비교
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from pathlib import Path
import json

# 한글 폰트
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

class ComprehensiveAnalyzer:
    """종합 성과 분석기"""
    
    def __init__(self):
        # Load real backtest result (방금 실행한 것)
        self.df_real = pd.read_csv('reports/simulation_1year_equity.csv')
        self.df_real['date'] = pd.to_datetime(self.df_real['date'])
        
        # Load previous simulation (Base + Turbo 데이터)
        self.df_sim = pd.read_csv('GARAM_Data/reports/simulation_1year_turbo.csv')
        self.df_sim['date'] = pd.to_datetime(self.df_sim['date'])
        
        print(f"✓ Loaded real backtest: {len(self.df_real)} rows")
        print(f"✓ Loaded simulation: {len(self.df_sim)} rows")
        
    def analyze_monthly(self):
        """월별 상세 분석"""
        df = self.df_real.copy()
        df['month'] = df['date'].dt.to_period('M')
        
        monthly_stats = []
        
        for month, group in df.groupby('month'):
            start_eq = group.iloc[0]['equity']
            end_eq = group.iloc[-1]['equity']
            ret = (end_eq - start_eq) / start_eq
            
            # 거래 추정 (포지션 수 변화)
            if 'positions_count' in group.columns:
                trades_approx = group['positions_count'].diff().abs().sum()
            else:
                trades_approx = 0
            
            monthly_stats.append({
                'month': str(month),
                'start_equity': start_eq,
                'end_equity': end_eq,
                'return': ret,
                'max_equity': group['equity'].max(),
                'min_equity': group['equity'].min(),
                'trades_approx': int(trades_approx) if trades_approx > 0 else 'N/A'
            })
        
        return pd.DataFrame(monthly_stats)
    
    def create_overlay_chart(self, output_file='GARAM_Data/reports/final_comparison_overlay.png'):
        """Base + 실제백테스트 + KOSPI 오버레이"""
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 10))
        fig.suptitle('GARAM 1년 성과 종합 분석 (실제 백테스트)', fontsize=16, fontweight='bold')
        
        # 데이터 정규화 (100M 시작)
        real_norm = (self.df_real['equity'] / self.df_real['equity'].iloc[0]) * 100_000_000
        base_norm = (self.df_sim['engine1'] / self.df_sim['engine1'].iloc[0]) * 100_000_000
        kospi_norm = (self.df_sim['kospi'] / self.df_sim['kospi'].iloc[0]) * 100_000_000
        
        # Plot 1: 자산 추이
        ax1.plot(self.df_real['date'], real_norm, linewidth=2.5, color='#FF6B6B', 
                label=f'실제 백테스트 (+{(self.df_real["equity"].iloc[-1]/self.df_real["equity"].iloc[0]-1)*100:.1f}%)', 
                alpha=0.9)
        ax1.plot(self.df_sim['date'], base_norm, linewidth=2.5, color='#2E86AB', 
                label=f'Base 1.0x (+{(self.df_sim["engine1"].iloc[-1]/self.df_sim["engine1"].iloc[0]-1)*100:.1f}%)', 
                alpha=0.7, linestyle='--')
        ax1.plot(self.df_sim['date'], kospi_norm, linewidth=1.5, color='gray', 
                label=f'KOSPI (+{(self.df_sim["kospi"].iloc[-1]/self.df_sim["kospi"].iloc[0]-1)*100:.1f}%)', 
                alpha=0.5, linestyle=':')
        
        ax1.axhline(y=100_000_000, color='black', linestyle='--', alpha=0.2)
        ax1.set_ylabel('자산 (원)', fontsize=12)
        ax1.set_title('누적 자산 추이 비교', fontsize=13)
        ax1.legend(loc='upper left', fontsize=11)
        ax1.grid(True, alpha=0.3)
        ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'₩{x/1e6:.0f}M'))
        
        # Plot 2: Drawdown
        real_cummax = real_norm.cummax()
        real_dd = (real_norm - real_cummax) / real_cummax * 100
        
        base_cummax = base_norm.cummax()
        base_dd = (base_norm - base_cummax) / base_cummax * 100
        
        ax2.fill_between(self.df_real['date'], 0, real_dd, color='#FF6B6B', alpha=0.3, label='실제 백테스트')
        ax2.fill_between(self.df_sim['date'], 0, base_dd, color='#2E86AB', alpha=0.2, label='Base 1.0x')
        ax2.plot(self.df_real['date'], real_dd, color='#FF6B6B', linewidth=1.5)
        ax2.plot(self.df_sim['date'], base_dd, color='#2E86AB', linewidth=1.5, linestyle='--')
        
        ax2.set_xlabel('날짜', fontsize=12)
        ax2.set_ylabel('낙폭 (%)', fontsize=12)
        ax2.set_title('낙폭 비교 (Drawdown)', fontsize=13)
        ax2.legend(loc='lower left', fontsize=11)
        ax2.grid(True, alpha=0.3)
        
        for ax in [ax1, ax2]:
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
            ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        plt.tight_layout()
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        print(f"✓ Saved: {output_file}")
        plt.close()
        
        return output_file
    
    def generate_report(self):
        """종합 리포트 생성"""
        # Monthly analysis
        df_monthly = self.analyze_monthly()
        df_monthly.to_csv('GARAM_Data/reports/monthly_analysis_real.csv', index=False)
        print(f"✓ Saved: monthly_analysis_real.csv")
        
        # Create charts
        chart_file = self.create_overlay_chart()
        
        # Summary
        real_initial = self.df_real['equity'].iloc[0]
        real_final = self.df_real['equity'].iloc[-1]
        real_return = (real_final - real_initial) / real_initial
        
        base_initial = self.df_sim['engine1'].iloc[0]
        base_final = self.df_sim['engine1'].iloc[-1]
        base_return = (base_final - base_initial) / base_initial
        
        kospi_initial = self.df_sim['kospi'].iloc[0]
        kospi_final = self.df_sim['kospi'].iloc[-1]
        kospi_return = (kospi_final - kospi_initial) / kospi_initial
        
        # MDD
        real_cummax = self.df_real['equity'].cummax()
        real_dd = (self.df_real['equity'] - real_cummax) / real_cummax
        real_mdd = real_dd.min()
        
        base_cummax = self.df_sim['engine1'].cummax()
        base_dd = (self.df_sim['engine1'] - base_cummax) / base_cummax
        base_mdd = base_dd.min()
        
        summary = {
            'real_backtest': {
                'return': float(real_return),
                'mdd': float(real_mdd),
                'final_equity': float(real_final)
            },
            'base_simulation': {
                'return': float(base_return),
                'mdd': float(base_mdd),
                'final_equity': float(base_final)
            },
            'kospi': {
                'return': float(kospi_return),
                'final': float(kospi_final)
            }
        }
        
        with open('GARAM_Data/reports/final_summary.json', 'w') as f:
            json.dump(summary, f, indent=2)
        print(f"✓ Saved: final_summary.json")
        
        return df_monthly, chart_file, summary

def main():
    print(f"\n{'='*70}")
    print("GARAM 종합 성과 분석")
    print(f"{'='*70}\n")
    
    analyzer = ComprehensiveAnalyzer()
    df_monthly, chart, summary = analyzer.generate_report()
    
    print(f"\n{'='*70}")
    print("분석 결과 요약")
    print(f"{'='*70}\n")
    
    print("실제 백테스트:")
    print(f"  수익률: {summary['real_backtest']['return']:.1%}")
    print(f"  MDD: {summary['real_backtest']['mdd']:.1%}")
    print(f"  최종: ₩{summary['real_backtest']['final_equity']:,.0f}\n")
    
    print("Base 시뮬레이션:")
    print(f"  수익률: {summary['base_simulation']['return']:.1%}")
    print(f"  MDD: {summary['base_simulation']['mdd']:.1%}")
    print(f"  최종: ₩{summary['base_simulation']['final_equity']:,.0f}\n")
   
    print("KOSPI:")
    print(f"  수익률: {summary['kospi']['return']:.1%}\n")
    
    print(f"{'='*70}\n")
    print("월별 분석:")
    print(df_monthly.to_string(index=False))
    
    print(f"\n{'='*70}")
    print("✅ 종합 분석 완료")
    print(f"{'='*70}\n")
    print(f"차트: {chart}")

if __name__ == "__main__":
    main()
