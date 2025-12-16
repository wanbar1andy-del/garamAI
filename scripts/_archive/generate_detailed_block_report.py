import pandas as pd
import pickle
import argparse
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root.parent))

from garam.research.regime.miracle_engine import Trade

def generate_report(miracle_path, baseline_path, out_path):
    output_lines = []
    
    # 1. Load Miracle Results
    with open(miracle_path, 'rb') as f:
        miracle_res = pickle.load(f)
    
    miracle_logs = miracle_res.get('signal_logs', [])
    
    # Filter for RegimeFilter blocks
    regime_blocks = [
        log for log in miracle_logs 
        if log['block_source'] == 'Filter' and log['filter_reason'] == 'RegimeFilter'
    ]
    
    output_lines.append(f"# 상세 분석 보고서 (Detailed Analysis Report)\n")
    output_lines.append(f"## 1. Miracle 전략: RegimeFilter 차단 목록 (총 {len(regime_blocks)}건)")
    output_lines.append(f"> **설명**: 아래 날짜들은 Miracle 전략이 진입 신호를 보냈으나, 시장 상황(Regime)이 'GREEN'이 아니어서 `RegimeFilter`에 의해 차단된 경우입니다.\n")
    
    output_lines.append("| 날짜 (Date) | 차단 원인 (Reason) |")
    output_lines.append("|---|---|")
    for log in regime_blocks:
        date_str = log['timestamp'].strftime('%Y-%m-%d')
        output_lines.append(f"| {date_str} | {log['filter_reason']} |")
    
    output_lines.append("\n---\n")
    
    # 2. Load Baseline Results
    with open(baseline_path, 'rb') as f:
        baseline_res = pickle.load(f)
        
    baseline_trades = baseline_res.get('trades', [])
    
    output_lines.append(f"## 2. Baseline 전략: 체결 거래 목록 (총 {len(baseline_trades)}건)")
    output_lines.append(f"> **설명**: Baseline 전략(이동평균 20/60)에서 실제로 체결된 거래들의 상세 내역입니다.\n")
    
    output_lines.append("| 진입 날짜 | 포지션 | 진입가 | 청산 날짜 | 청산가 | 수익률(%) | 청산 사유 |")
    output_lines.append("|---|---|---|---|---|---|---|")
    
    for t in baseline_trades:
        side_str = "Long" if t.side == 1 else "Short"
        entry_date = t.entry_time.strftime('%Y-%m-%d')
        exit_date = t.exit_time.strftime('%Y-%m-%d') if t.exit_time else "N/A"
        pnl_pct = f"{t.pnl_pct * 100:.2f}%"
        
        output_lines.append(f"| {entry_date} | {side_str} | {t.entry_price:,.0f} | {exit_date} | {t.exit_price:,.0f} | {pnl_pct} | {t.exit_reason} |")

    output_lines.append("\n---\n")
    
    # 3. Filtering Logic Explanation
    output_lines.append("## 3. 필터링 로직 (Filtering Logic)")
    output_lines.append("### RegimeFilter 작동 원리")
    output_lines.append("`RegimeFilter`는 현재 시장의 상태(Regime)가 전략이 허용하는 상태 목록(`allowed_regimes`)에 포함되어 있는지를 확인합니다.")
    output_lines.append("- **입력 데이터**: 일별 시장 데이터의 `state` 컬럼 (예: 'GREEN', 'RED', 'NEUTRAL')")
    output_lines.append("- **설정 (Config)**: `allowed_regimes: ['GREEN']`")
    output_lines.append("- **로직**:")
    output_lines.append("  ```python")
    output_lines.append("  def check_filter(self, row, context):")
    output_lines.append("      allowed = self.params.get('allowed_regimes', [])")
    output_lines.append("      current_state = row.get('state', 'UNKNOWN')")
    output_lines.append("      return current_state in allowed")
    output_lines.append("  ```")
    output_lines.append("- **의의**: 하락장('RED')이나 횡보장('NEUTRAL')에서 발생하는 거짓 신호(False Signals)를 원천적으로 차단하여 손실을 방지합니다.")

    # Save to file
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(output_lines))
        
    print(f"Report generated at {out_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--miracle", default="c:/garam/garam/data/miracle_with_logs.pkl")
    parser.add_argument("--baseline", default="c:/garam/garam/data/baseline_with_logs.pkl")
    parser.add_argument("--out", default="c:/garam/garam/data/detailed_report.md")
    args = parser.parse_args()
    
    generate_report(args.miracle, args.baseline, args.out)
