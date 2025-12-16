import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import sys
import os

# Ensure root directory is in python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

try:
    from config import PATHS
except ImportError:
    from garam.config import PATHS

class AutoReporter:
    def __init__(self):
        self.history_path = PATHS.ACCOUNT_SNAPSHOT
        self.report_dir = PATHS.REPORTS_DIR
        
        # Ensure report dir exists
        self.report_dir.mkdir(parents=True, exist_ok=True)
        
    def load_data(self):
        if not self.history_path.exists():
            print(f"[AutoReporter] History file not found: {self.history_path}")
            return None
            
        df = pd.read_csv(self.history_path)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)
        df.sort_index(inplace=True)
        return df
        
    def generate_monthly_report(self):
        df = self.load_data()
        if df is None: return
        
        # Resample to Monthly
        # Equity is point-in-time, take last value of month
        monthly_eq = df['total_equity'].resample('M').last()
        monthly_ret = monthly_eq.pct_change().fillna(0.0)
        
        # Calculate Stats per month
        monthly_stats = []
        for date, ret in monthly_ret.items():
            month_start = date.replace(day=1)
            # Filter daily data for this specific month
            daily_in_month = df[df.index.month == date.month]
            daily_in_month = daily_in_month[daily_in_month.index.year == date.year]
            
            # MDD in Month
            mdd = 0.0
            if not daily_in_month.empty:
                peak = daily_in_month['total_equity'].expanding().max()
                dd = (daily_in_month['total_equity'] - peak) / peak
                mdd = dd.min()
                
            monthly_stats.append({
                'Month': date.strftime("%Y-%m"),
                'Return': ret * 100,
                'MDD': mdd * 100,
                'EndEquity': monthly_eq[date]
            })
            
        # Create Markdown Content
        report_date = datetime.now().strftime("%Y-%m-%d")
        md_content = f"# 월간 성과 보고서 (Monthly Performance Report)\n\n**작성일**: {report_date}\n\n"
        md_content += "| 월 (Month) | 수익률 (Return) | MDD | 기말 자산 (End Equity) |\n"
        md_content += "| :--- | :--- | :--- | :--- |\n"
        
        for stat in monthly_stats:
            md_content += f"| **{stat['Month']}** | {stat['Return']:.2f}% | {stat['MDD']:.2f}% | {stat['EndEquity']:,.0f} |\n"
            
        # Overall Stats
        total_ret = (df['total_equity'].iloc[-1] / df['total_equity'].iloc[0]) - 1
        days = (df.index[-1] - df.index[0]).days
        years = days / 365.25 if days > 0 else 0
        cagr = ((1 + total_ret) ** (1/years)) - 1 if years >= 1 else total_ret
        
        peak = df['total_equity'].expanding().max()
        dd = (df['total_equity'] - peak) / peak
        total_mdd = dd.min()
        
        md_content += "\n## 종합 통계 (Overall Statistics)\n"
        md_content += f"- **분석 기간**: {df.index[0].date()} ~ {df.index[-1].date()} ({days}일)\n"
        md_content += f"- **누적 수익률 (Total Return)**: {total_ret*100:.2f}%\n"
        md_content += f"- **연평균 수익률 (CAGR)**: {cagr*100:.2f}%\n"
        md_content += f"- **최대 낙폭 (Max Drawdown)**: {total_mdd*100:.2f}%\n"
        
        # Save Report
        filename = f"Performance_Report_{datetime.now().strftime('%Y%m%d')}.md" # Keep filename English for compatibility
        filepath = self.report_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(md_content)
            
        print(f"[AutoReporter] Report generated: {filepath}")
        return filepath

if __name__ == "__main__":
    reporter = AutoReporter()
    reporter.generate_monthly_report()
