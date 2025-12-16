"""
Generate Garam System Report
Aggregates status from Data, Alpha Lab, Test Trading, and Surfing Brain.
"""

import json
import pandas as pd
from pathlib import Path
import sys
from datetime import datetime
import yaml

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import PATHS

def generate_report():
    report_path = PATHS.DATA_DIR / "reports" / f"garam_system_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 1. Gather Data
    
    # US Data Coverage
    us_coverage = {}
    us_json_path = PATHS.US_SP500_ROOT / "coverage_summary.json"
    if us_json_path.exists():
        with open(us_json_path, 'r') as f:
            us_coverage = json.load(f)
            
    # Alpha Lab Results
    alpha_results = []
    exp_dir = PATHS.EXPERIMENTS_DIR / "us_factors"
    if exp_dir.exists():
        for run_dir in sorted(exp_dir.glob("*"), reverse=True)[:5]: # Check last 5 runs
            metrics_file = run_dir / "metrics.csv"
            if metrics_file.exists():
                try:
                    metrics = pd.read_csv(metrics_file, index_col=0).to_dict()['0']
                    metrics['name'] = run_dir.name
                    alpha_results.append(metrics)
                except:
                    pass
                    
    # Surfing Brain Logs
    surfing_stats = {"regime_dist": {}, "mode_dist": {}, "avg_uncertainty": 0.0}
    surfing_log_dir = PATHS.LOGS_DIR / "surfing_decisions"
    if surfing_log_dir.exists():
        log_files = sorted(surfing_log_dir.glob("*.csv"), reverse=True)
        if log_files:
            try:
                df = pd.read_csv(log_files[0])
                surfing_stats["regime_dist"] = df['regime'].value_counts().to_dict()
                surfing_stats["mode_dist"] = df['mode'].value_counts().to_dict()
                surfing_stats["avg_uncertainty"] = df['uncertainty'].mean()
            except:
                pass

    # 2. Write Report
    with open(report_path, "w", encoding='utf-8') as f:
        f.write(f"# Garam System Health Report\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # Overview
        f.write("## 1. Overview\n")
        status = "🟢 NORMAL" if us_coverage.get('total_symbols', 0) > 0 else "🔴 DATA MISSING"
        f.write(f"- **System Status:** {status}\n")
        f.write(f"- **US Data:** {us_coverage.get('total_symbols', 0)} symbols, {us_coverage.get('start_date', 'N/A')} ~ {us_coverage.get('end_date', 'N/A')}\n")
        f.write(f"- **Active Strategies:** {len(alpha_results)}\n\n")
        
        # Data Coverage
        f.write("## 2. Data Coverage\n")
        f.write("### US S&P 500\n")
        f.write(f"- **Symbols:** {us_coverage.get('total_symbols', 0)}\n")
        f.write(f"- **Coverage:** {us_coverage.get('coverage_pct', 0)}%\n")
        if us_coverage.get('missing_symbols'):
            f.write(f"- **Missing:** {len(us_coverage['missing_symbols'])} symbols\n")
        f.write("\n")
        
        # Alpha Lab
        f.write("## 3. Alpha Lab (US Factors)\n")
        if alpha_results:
            f.write("| Strategy | Sharpe | MaxDD | CAGR | Status |\n")
            f.write("|----------|--------|-------|------|--------|\n")
            for res in alpha_results:
                name = res.get('name', 'Unknown').split('_20')[0] # Remove timestamp
                sharpe = res.get('sharpe', 0)
                mdd = res.get('max_drawdown', 0)
                cagr = res.get('cagr', 0)
                # Simple check against defaults
                status = "✅" if sharpe > 0.7 else "⚠️"
                f.write(f"| {name} | {sharpe:.2f} | {mdd:.2%}| {cagr:.2%} | {status} |\n")
        else:
            f.write("No backtest results found.\n")
        f.write("\n")
        
        # Surfing Brain
        f.write("## 4. Surfing Brain v1\n")
        f.write(f"- **Avg Uncertainty:** {surfing_stats['avg_uncertainty']:.2f}\n")
        f.write("### Regime Distribution\n")
        for k, v in surfing_stats['regime_dist'].items():
            f.write(f"- {k}: {v}\n")
        f.write("### Mode Distribution\n")
        for k, v in surfing_stats['mode_dist'].items():
            f.write(f"- {k}: {v}\n")
        f.write("\n")
        
        # Gaps & TODO
        f.write("## 5. Gaps & TODO List\n")
        f.write("### High Priority\n")
        if us_coverage.get('total_symbols', 0) < 500:
            f.write("- [ ] **Expand US Data:** Currently only have partial S&P 500 symbols. Need full 500+ historical.\n")
        f.write("- [ ] **Historical Constituents:** Using current constituents for history (Survivorship Bias risk).\n")
        
        f.write("### Medium Priority\n")
        f.write("- [ ] **Real Fundamentals:** Factor strategies use mock/price-derived data. Need real fundamental API.\n")
        f.write("- [ ] **Transaction Costs:** Current model (20bps) is static. Need dynamic slippage model.\n")
        
        f.write("### Low Priority\n")
        f.write("- [ ] **UI Integration:** Surfing Brain state not yet fully visible in GaramUI.\n")
        
        f.write("\n## 6. Next Action Suggestions\n")
        f.write("1. Run `scripts/collect_us_sp500_20y.py` with full list (remove limit).\n")
        f.write("2. Integrate a paid data source for historical constituents (e.g. Sharadar/Polygon).\n")
        f.write("3. Connect Alpha Lab to real fundamental data loader.\n")

    print(f"System Report generated: {report_path}")

if __name__ == "__main__":
    generate_report()
