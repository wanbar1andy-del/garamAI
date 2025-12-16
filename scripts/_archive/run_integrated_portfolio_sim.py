"""
Integrated Portfolio Simulation Runner
Runs a multi-year simulation combining KR Intraday and US Factor strategies.
"""

import argparse
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import sys
import json
import logging

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import PATHS
from sim.portfolio_simulator import PortfolioSimulator
from strategies.kr_intraday.gap_reversal import GapReversalStrategy
from strategies.kr_intraday.momentum_breakout import MomentumBreakoutStrategy
# Import US strategies if available, otherwise use placeholders or mocks
# from strategies.us_factors.momentum import MomentumStrategy 

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(PATHS.LOGS_DIR / "portfolio_sim.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("PortfolioRunner")

def load_kr_pnl(run_id: str = None) -> pd.DataFrame:
    """Load KR Intraday P&L from experiments"""
    exp_dir = PATHS.EXPERIMENTS_DIR / "kr_intraday"
    
    if run_id:
        file_path = exp_dir / f"daily_pnl_{run_id}.csv"
    else:
        # Find latest
        files = list(exp_dir.glob("daily_pnl_*.csv"))
        if not files:
            logger.warning("No KR P&L files found.")
            return pd.DataFrame()
        file_path = sorted(files)[-1]
        
    logger.info(f"Loading KR P&L from {file_path}")
    df = pd.read_csv(file_path)
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)
    return df

def load_us_pnl() -> pd.DataFrame:
    """Load US Factor P&L from experiments"""
    # Use the specific directory found
    us_dir = PATHS.EXPERIMENTS_DIR / "us_factors" / "US_MOM_12_1_20251125_082115"
    file_path = us_dir / "equity.csv"
    
    if not file_path.exists():
        logger.warning(f"US data not found at {file_path}, using synthetic.")
        # Generate synthetic US returns (uncorrelated to KR)
        dates = pd.date_range(start="2025-01-01", end="2025-12-31", freq="B")
        data = []
        for date in dates:
            ret = np.random.normal(0.0005, 0.01) 
            pnl = 100_000_000 * ret 
            data.append({'date': date, 'pnl': pnl})
        df = pd.DataFrame(data)
        df.set_index('date', inplace=True)
        return df
        
    logger.info(f"Loading US P&L from {file_path}")
    try:
        df = pd.read_csv(file_path)
        print(f"US Data Head:\n{df.head()}")
        
        # Ensure timestamp column exists
        if 'timestamp' not in df.columns:
            logger.error(f"Column 'timestamp' not found in {file_path}. Columns: {df.columns}")
            return pd.DataFrame()
            
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        df = df.dropna(subset=['timestamp'])
        df['date'] = df['timestamp'].dt.date
        df = df.sort_values('timestamp')
        
        # Calculate daily P&L from cumulative pnl_balance
        # Group by date and take last
        daily_cum = df.groupby('date')['pnl_balance'].last()
        daily_pnl = daily_cum.diff().fillna(daily_cum.iloc[0])
        
        # Convert to DataFrame
        pnl_df = pd.DataFrame(daily_pnl).rename(columns={'pnl_balance': 'pnl'})
        pnl_df.index = pd.to_datetime(pnl_df.index)
        
        return pnl_df
    except Exception as e:
        logger.error(f"Error loading US P&L: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()

def run_simulation(start_date: str, end_date: str):
    """Run integrated simulation"""
    
    # 1. Load Data
    kr_pnl_df = load_kr_pnl()
    us_pnl_df = load_us_pnl()
    
    if kr_pnl_df.empty:
        logger.error("KR Data missing. Run NP-1 first.")
        return
        
    # Align dates
    start_dt = pd.to_datetime(start_date)
    end_dt = pd.to_datetime(end_date)
    
    # 2. Initialize Simulator
    # We pass empty lists for strategies because we are feeding pre-calculated P&L
    sim = PortfolioSimulator(
        kr_strategies=[], 
        us_strategies=[],
        base_capital=100_000_000
    )
    
    # 3. Run Backtest
    results = sim.run_backtest(
        start_date=start_date,
        end_date=end_date,
        kr_data=kr_pnl_df,
        us_data=us_pnl_df
    )
    
    # 4. Generate Report
    _generate_report(results, sim)

def _generate_report(results: dict, sim: PortfolioSimulator):
    """Generate Markdown report"""
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = PATHS.EXPERIMENTS_DIR / "portfolio"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    metrics = sim.get_portfolio_metrics()
    
    report_path = output_dir / f"portfolio_report_{run_id}.md"
    
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(f"# Integrated Portfolio Report ({run_id})\n\n")
        f.write(f"**Period:** {results['start_date']} to {results['end_date']}\n\n")
        
        f.write("## 1. Performance Summary\n")
        f.write(f"- **Total P&L:** {metrics['total_pnl']:,.0f} KRW\n")
        f.write(f"- **Total Return:** {metrics['total_return_pct']:.2f}%\n")
        f.write(f"- **KR Contribution:** {metrics['kr_pnl']:,.0f} KRW\n")
        f.write(f"- **US Contribution:** {metrics['us_pnl']:,.0f} KRW\n\n")
        
        f.write("## 2. Allocation Stats\n")
        f.write(f"- **Avg KR Allocation:** {metrics['avg_kr_allocation']*100:.1f}%\n")
        f.write(f"- **Avg US Allocation:** {metrics['avg_us_allocation']*100:.1f}%\n")
        f.write(f"- **Avg Cash:** {metrics['avg_cash_allocation']*100:.1f}%\n\n")
        
        f.write("## 3. Daily Metrics (Last 10 Days)\n")
        f.write("| Date | KR P&L | US P&L | Total P&L | Equity |\n")
        f.write("|------|--------|--------|-----------|--------|\n")
        
        daily = results.get('daily_metrics', [])
        for day in daily[-10:]:
            f.write(f"| {day['date'].date()} | {day['kr_pnl']:,.0f} | {day['us_pnl']:,.0f} | {day['total_pnl']:,.0f} | {day['equity']:,.0f} |\n")
            
    # Save JSON Summary
    json_path = output_dir / f"portfolio_metrics_{run_id}.json"
    with open(json_path, "w") as f:
        json.dump(metrics, f, indent=2)
        
    # Save Daily CSV
    if daily:
        csv_path = output_dir / f"portfolio_daily_{run_id}.csv"
        pd.DataFrame(daily).to_csv(csv_path, index=False)
            
    logger.info(f"Report generated: {report_path}")
    print(f"Report saved to {report_path}")
    print(f"JSON saved to {json_path}")
    print(f"CSV saved to {csv_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Integrated Portfolio Simulation")
    parser.add_argument("--start", type=str, default="2025-01-01", help="Start date")
    parser.add_argument("--end", type=str, default="2025-12-31", help="End date")
    
    args = parser.parse_args()
    
    run_simulation(args.start, args.end)
