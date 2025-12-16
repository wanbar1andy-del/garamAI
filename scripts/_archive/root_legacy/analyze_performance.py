#!/usr/bin/env python3
"""
Investment Performance Analyzer
백테스트 결과를 투자 수익률 관점에서 분석 및 시각화
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from pathlib import Path
from datetime import datetime
import json

# 한글 폰트 설정 (Windows)
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

class PerformanceAnalyzer:
    """투자 성과 분석기"""
    
    def __init__(self, equity_file, trades_file=None):
        self.equity_file = equity_file
        self.trades_file = trades_file
        
        # Load data
        self.df_equity = pd.read_csv(equity_file)
        self.df_equity['date'] = pd.to_datetime(self.df_equity['date'])
        self.df_equity.set_index('date', inplace=True)
        
        if trades_file:
            self.df_trades = pd.read_csv(trades_file)
            self.df_trades['date'] = pd.to_datetime(self.df_trades['date'])
        else:
            self.df_trades = None
    
    def calculate_metrics(self):
        """주요 투자 지표 계산"""
        equity = self.df_equity['equity']
        
        # Basic metrics
        initial = equity.iloc[0]
        final = equity.iloc[-1]
        total_return = (final - initial) / initial
        
        # Daily returns
        daily_returns = equity.pct_change().dropna()
        
        # Cumulative max
        cummax = equity.cummax()
        drawdown = (equity - cummax) / cummax
        max_dd = drawdown.min()
        
        # Volatility (annualized)
        volatility = daily_returns.std() * np.sqrt(252)
        
        # Sharpe Ratio (assuming 0% risk-free rate)
        sharpe = (daily_returns.mean() * 252) / (daily_returns.std() * np.sqrt(252)) if daily_returns.std() > 0 else 0
        
        # Annualized return
        days = len(equity)
        years = days / 252
        annual_return = (final / initial) ** (1 / years) - 1 if years > 0 else total_return
        
        # Win rate (if trades available)
        win_rate = None
        if self.df_trades is not None and len(self.df_trades) > 0:
            # Simple approximation: count profitable trades
            sells = self.df_trades[self.df_trades['action'] == 'SELL']
            # This is simplified - real P&L calculation would be more complex
            pass
        
        return {
            'initial_capital': initial,
            'final_equity': final,
            'total_return': total_return,
            'annual_return': annual_return,
            'max_drawdown': max_dd,
            'volatility': volatility,
            'sharpe_ratio': sharpe,
            'trading_days': days,
            'years': years,
            'daily_avg_return': daily_returns.mean(),
            'daily_std_return': daily_returns.std()
        }
    
    def generate_charts(self, output_dir='GARAM_Data/backtest'):
        """성과 차트 생성"""
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)
        
        equity = self.df_equity['equity']
        dates = self.df_equity.index
        
        # Create figure with 2 subplots
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
        fig.suptitle('GARAM 1년 백테스트 성과 분석', fontsize=16, fontweight='bold')
        
        # 1. Equity Curve
        ax1.plot(dates, equity, linewidth=2, color='#2E86AB', label='자산 추이')
        ax1.axhline(y=equity.iloc[0], color='gray', linestyle='--', alpha=0.5, label=f'초기자본: ₩{equity.iloc[0]:,.0f}')
        ax1.fill_between(dates, equity.iloc[0], equity, where=(equity >= equity.iloc[0]), 
                         color='green', alpha=0.1, label='수익 구간')
        ax1.fill_between(dates, equity.iloc[0], equity, where=(equity < equity.iloc[0]), 
                         color='red', alpha=0.1, label='손실 구간')
        
        ax1.set_ylabel('자산 (원)', fontsize=12)
        ax1.set_title(f'자산 추이 (₩{equity.iloc[0]:,.0f} → ₩{equity.iloc[-1]:,.0f})', fontsize=13)
        ax1.legend(loc='upper left')
        ax1.grid(True, alpha=0.3)
        ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'₩{x/1e6:.1f}M'))
        
        # 2. Drawdown
        cummax = equity.cummax()
        drawdown = (equity - cummax) / cummax * 100
        
        ax2.fill_between(dates, 0, drawdown, color='red', alpha=0.3, label='낙폭 (MDD)')
        ax2.plot(dates, drawdown, color='darkred', linewidth=1.5)
        ax2.axhline(y=drawdown.min(), color='red', linestyle='--', 
                   label=f'최대낙폭: {drawdown.min():.1f}%')
        
        ax2.set_xlabel('날짜', fontsize=12)
        ax2.set_ylabel('낙폭 (%)', fontsize=12)
        ax2.set_title('낙폭 추이 (Drawdown)', fontsize=13)
        ax2.legend(loc='lower left')
        ax2.grid(True, alpha=0.3)
        
        # Format x-axis
        for ax in [ax1, ax2]:
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
            ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        plt.tight_layout()
        
        # Save
        chart_file = output_dir / 'performance_chart.png'
        plt.savefig(chart_file, dpi=150, bbox_inches='tight')
        print(f"✓ Chart saved to {chart_file}")
        
        plt.close()
        
        return chart_file
    
    def generate_monthly_returns_chart(self, output_dir='GARAM_Data/backtest'):
        """월별 수익률 차트"""
        output_dir = Path(output_dir)
        
        # Calculate monthly returns
        equity = self.df_equity['equity']
        monthly = equity.resample('M').last()
        monthly_returns = monthly.pct_change().dropna() * 100
        
        # Create bar chart
        fig, ax = plt.subplots(figsize=(14, 6))
        
        colors = ['green' if x > 0 else 'red' for x in monthly_returns.values]
        bars = ax.bar(range(len(monthly_returns)), monthly_returns.values, color=colors, alpha=0.7)
        
        ax.set_xlabel('월', fontsize=12)
        ax.set_ylabel('수익률 (%)', fontsize=12)
        ax.set_title('월별 수익률', fontsize=14, fontweight='bold')
        ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
        ax.grid(True, axis='y', alpha=0.3)
        
        # X-axis labels
        ax.set_xticks(range(len(monthly_returns)))
        ax.set_xticklabels([d.strftime('%Y-%m') for d in monthly_returns.index], 
                          rotation=45, ha='right')
        
        # Add value labels on bars
        for i, (bar, val) in enumerate(zip(bars, monthly_returns.values)):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{val:.1f}%', ha='center', va='bottom' if val > 0 else 'top',
                   fontsize=9)
        
        plt.tight_layout()
        
        chart_file = output_dir / 'monthly_returns.png'
        plt.savefig(chart_file, dpi=150, bbox_inches='tight')
        print(f"✓ Monthly chart saved to {chart_file}")
        
        plt.close()
        
        return chart_file
    
    def print_report(self, metrics):
        """투자 성과 리포트 출력"""
        print(f"\n{'='*60}")
        print("GARAM 1년 백테스트 투자 성과")
        print(f"{'='*60}\n")
        
        print(f"📊 기간 정보")
        print(f"  시작일: {self.df_equity.index[0].date()}")
        print(f"  종료일: {self.df_equity.index[-1].date()}")
        print(f"  거래일수: {metrics['trading_days']}일")
        print(f"  운용기간: {metrics['years']:.2f}년\n")
        
        print(f"💰 수익률")
        print(f"  초기자본: ₩{metrics['initial_capital']:>15,.0f}")
        print(f"  최종자산: ₩{metrics['final_equity']:>15,.0f}")
        print(f"  총 수익: ₩{metrics['final_equity'] - metrics['initial_capital']:>15,.0f}")
        print(f"  총수익률: {metrics['total_return']:>15.2%}")
        print(f"  연환산 수익률: {metrics['annual_return']:>15.2%}\n")
        
        print(f"📉 리스크")
        print(f"  최대낙폭(MDD): {metrics['max_drawdown']:>15.2%}")
        print(f"  변동성(연환산): {metrics['volatility']:>15.2%}")
        print(f"  샤프비율: {metrics['sharpe_ratio']:>15.2f}\n")
        
        print(f"📈 일별 통계")
        print(f"  평균 일수익률: {metrics['daily_avg_return']:>15.4%}")
        print(f"  일수익률 표준편차: {metrics['daily_std_return']:>15.4%}\n")
        
        # Calculate some additional stats
        equity = self.df_equity['equity']
        positive_days = (equity.pct_change() > 0).sum()
        total_days = len(equity) - 1
        win_rate = positive_days / total_days if total_days > 0 else 0
        
        print(f"📊 승률")
        print(f"  상승일: {positive_days}일")
        print(f"  하락일: {total_days - positive_days}일")
        print(f"  승률: {win_rate:>15.2%}\n")
        
        # KOSPI comparison (assumed ~5% annual return)
        kospi_return = 0.05 * metrics['years']
        alpha = metrics['total_return'] - kospi_return
        
        print(f"📊 벤치마크 비교 (KOSPI 가정)")
        print(f"  KOSPI 추정 수익률: {kospi_return:>15.2%}")
        print(f"  초과 수익(Alpha): {alpha:>15.2%}\n")
        
        print(f"{'='*60}\n")

def main():
    analyzer = PerformanceAnalyzer(
        equity_file='GARAM_Data/backtest/equity_1y.csv',
        trades_file='GARAM_Data/backtest/trades_1y.csv'
    )
    
    # Calculate metrics
    metrics = analyzer.calculate_metrics()
    
    # Print report
    analyzer.print_report(metrics)
    
    # Generate charts
    print("Generating charts...")
    chart1 = analyzer.generate_charts()
    chart2 = analyzer.generate_monthly_returns_chart()
    
    # Save metrics to JSON
    metrics_clean = {k: float(v) if isinstance(v, (np.floating, np.integer)) else v 
                    for k, v in metrics.items()}
    
    with open('GARAM_Data/backtest/performance_metrics.json', 'w') as f:
        json.dump(metrics_clean, f, indent=2)
    print("✓ Metrics saved to performance_metrics.json")
    
    print(f"\n{'='*60}")
    print("✅ 성과 분석 완료")
    print(f"{'='*60}")
    print(f"\n차트 파일:")
    print(f"  1. {chart1}")
    print(f"  2. {chart2}\n")

if __name__ == "__main__":
    main()
