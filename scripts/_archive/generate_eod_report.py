"""
GARAM EOD (End-of-Day) Report Generator
Collects Shadow Trading results and generates daily performance report
"""

import json
import sys
from pathlib import Path
from datetime import datetime, date
from typing import Dict, List, Any
import logging

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from garam.config import PATHS

logger = logging.getLogger(__name__)

class EODReportGenerator:
    """Generate End-of-Day performance reports"""
    
    def __init__(self, report_date: date = None):
        self.report_date = report_date or date.today()
        self.reports_dir = PATHS.BASE_DIR / "reports"
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
    def collect_shadow_data(self) -> Dict[str, Any]:
        """Collect Shadow Trading execution data"""
        # In production, this would read from Shadow Trader logs
        # For now, return mock data based on current portfolio state
        
        return {
            "total_equity": 117_092_366,
            "cash": 4_683_694,
            "daily_return": 0.025,
            "cumulative_return": 0.17,
            "max_drawdown": -0.05,
            "sharpe_ratio": 1.85,
            "win_rate": 0.62,
            "total_trades": 12,
            "winning_trades": 8,
            "losing_trades": 4
        }
    
    def collect_trades(self) -> List[Dict[str, Any]]:
        """Collect today's trade execution history"""
        # In production, read from trade logs
        return [
            {
                "symbol": "005930",
                "name": "삼성전자",
                "action": "BUY",
                "time": "09:15:00",
                "price": 78000,
                "quantity": 100,
                "reason": "외국인 순매수 + 섹터 동조화",
                "heatscore": 0.75
            },
            {
                "symbol": "000660",
                "name": "SK하이닉스",
                "action": "BUY",
                "time": "10:30:00",
                "price": 132000,
                "quantity": 50,
                "reason": "AI 반도체 모멘텀 지속",
                "heatscore": 0.68
            },
            {
                "symbol": "035420",
                "name": "NAVER",
                "action": "SELL",
                "time": "14:20:00",
                "price": 198000,
                "quantity": 80,
                "reason": "목표가 도달",
                "pnl": 4_800_000
            }
        ]
    
    def collect_positions(self) -> List[Dict[str, Any]]:
        """Collect current portfolio positions"""
        return [
            {
                "symbol": "005930",
                "name": "삼성전자",
                "quantity": 450,
                "avg_price": 76500,
                "current_price": 78000,
                "value": 35_127_710,
                "pnl_pct": 0.025,
                "allocation": 0.30
            },
            {
                "symbol": "000660",
                "name": "SK하이닉스",
                "quantity": 220,
                "avg_price": 129000,
                "current_price": 132000,
                "value": 29_273_091,
                "pnl_pct": 0.012,
                "allocation": 0.25
            },
            {
                "symbol": "035420",
                "name": "NAVER",
                "quantity": 120,
                "avg_price": 200000,
                "current_price": 198000,
                "value": 23_418_473,
                "pnl_pct": -0.005,
                "allocation": 0.20
            },
            {
                "symbol": "005380",
                "name": "현대차",
                "quantity": 100,
                "avg_price": 248000,
                "current_price": 250000,
                "value": 24_589_396,
                "pnl_pct": 0.008,
                "allocation": 0.21
            }
        ]
    
    def collect_alerts(self) -> List[Dict[str, str]]:
        """Collect system alerts and warnings"""
        return [
            {
                "level": "INFO",
                "time": "09:00:00",
                "message": "시스템 정상 시작. 모든 안전 검사 통과"
            },
            {
                "level": "INFO",
                "time": "15:30:00",
                "message": "장마감. 총 3건의 거래 실행"
            }
        ]
    
    def calculate_metrics(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate additional performance metrics"""
        return {
            "avg_win": data.get("cumulative_return", 0) / max(data.get("winning_trades", 1), 1),
            "avg_loss": -data.get("max_drawdown", 0) / max(data.get("losing_trades", 1), 1),
            "profit_factor": abs(data.get("cumulative_return", 0) / max(data.get("max_drawdown", 0.01), 0.01)),
            "exposure": (data.get("total_equity", 0) - data.get("cash", 0)) / max(data.get("total_equity", 1), 1)
        }
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive EOD report"""
        logger.info(f"Generating EOD report for {self.report_date}")
        
        # Collect data
        summary_data = self.collect_shadow_data()
        trades = self.collect_trades()
        positions = self.collect_positions()
        alerts = self.collect_alerts()
        metrics = self.calculate_metrics(summary_data)
        
        # Build report
        report = {
            "date": self.report_date.isoformat(),
            "generated_at": datetime.now().isoformat(),
            "summary": {
                **summary_data,
                **metrics
            },
            "trades": trades,
            "positions": positions,
            "alerts": alerts,
            "metadata": {
                "version": "1.0",
                "generator": "GARAM EOD Report Generator"
            }
        }
        
        return report
    
    def save_report(self, report: Dict[str, Any]) -> Path:
        """Save report to JSON file"""
        filename = f"eod_{self.report_date.strftime('%Y%m%d')}.json"
        filepath = self.reports_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Report saved to {filepath}")
        return filepath
    
    def save_latest(self, report: Dict[str, Any]) -> Path:
        """Save as latest.json for quick access"""
        latest_path = self.reports_dir / "latest.json"
        
        with open(latest_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Latest report saved to {latest_path}")
        return latest_path


def main():
    """Main entry point"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    import argparse
    parser = argparse.ArgumentParser(description='Generate EOD Report')
    parser.add_argument('--date', type=str, help='Report date (YYYY-MM-DD)')
    parser.add_argument('--mock', action='store_true', help='Use mock data')
    args = parser.parse_args()
    
    # Parse date
    report_date = None
    if args.date:
        report_date = datetime.strptime(args.date, '%Y-%m-%d').date()
    
    # Generate report
    generator = EODReportGenerator(report_date)
    report = generator.generate_report()
    
    # Save reports
    filepath = generator.save_report(report)
    latest_path = generator.save_latest(report)
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"📊 EOD Report Generated: {report['date']}")
    print(f"{'='*60}")
    print(f"총 자산:        ₩{report['summary']['total_equity']:,}")
    print(f"일일 수익률:    {report['summary']['daily_return']*100:+.2f}%")
    print(f"누적 수익률:    {report['summary']['cumulative_return']*100:+.2f}%")
    print(f"Sharpe Ratio:  {report['summary']['sharpe_ratio']:.2f}")
    print(f"승률:          {report['summary']['win_rate']*100:.1f}%")
    print(f"거래 건수:      {report['summary']['total_trades']}")
    print(f"{'='*60}")
    print(f"저장 위치: {filepath}")
    print(f"최신본: {latest_path}")
    print(f"{'='*60}\n")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
