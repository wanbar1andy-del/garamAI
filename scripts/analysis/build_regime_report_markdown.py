"""
Build Regime Report Markdown
- Inputs: summary_by_regime.csv, summary_by_market_phase.csv
- Output: report_champion_v2_regime.md
"""
import pandas as pd
import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--regime-summary', required=True)
    parser.add_argument('--phase-summary', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    
    regime_df = pd.read_csv(args.regime_summary)
    phase_df = pd.read_csv(args.phase_summary)
    
    md = "# Champion Rule v2 Regime Performance Report\n\n"
    
    md += "## 1. Market Phase Analysis (Bull/Sideways/Bear)\n"
    md += phase_df.to_markdown(index=False, floatfmt=".2f")
    md += "\n\n"
    
    md += "## 2. Detailed Regime Analysis (R1~R7)\n"
    md += regime_df.to_markdown(index=False, floatfmt=".2f")
    md += "\n\n"
    
    md += "## 3. Key Insights\n"
    md += "- **Bull (R1/R2)**: Check 'Win Rate' and 'Avg Win %'. Should be high.\n"
    md += "- **Sideways (R3)**: Check 'Num Trades'. Should be low (due to Gate/Cap).\n"
    md += "- **Bear (R4/R5)**: Check 'Total Return'. Should be near zero (avoidance).\n"
    
    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(md)
        
    print(f"Report saved to {args.output}")

if __name__ == "__main__":
    main()
