import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt

PROJECT_ROOT = Path("C:/garam/garam")
LOG_DIR = PROJECT_ROOT / "logs/phase4_sweep"
OUTPUT_DIR = PROJECT_ROOT / "logs/phase8_audit"
OUTPUT_DIR.mkdir(exist_ok=True)

def calculate_stats(equity_file):
    if not equity_file.exists():
        return None
    
    df = pd.read_csv(equity_file)
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)
    
    initial_equity = df['equity'].iloc[0]
    final_equity = df['equity'].iloc[-1]
    total_return = (final_equity - initial_equity) / initial_equity * 100
    profit = final_equity - initial_equity
    
    # MDD
    roll_max = df['equity'].cummax()
    drawdown = (df['equity'] - roll_max) / roll_max
    mdd = drawdown.min() * 100
    
    return {
        'total_return': total_return,
        'profit': profit,
        'mdd': mdd,
        'final_equity': final_equity
    }

scenarios = [
    {
        "name": "Baseline",
        "file": LOG_DIR / "equity_PYRAMID_0.7_AESTHETIC_INTELLIGENT_PM0.8.csv"
    },
    {
        "name": "Scenario A (Init 40%)",
        "file": LOG_DIR / "equity_PYRAMID_0.7_AESTHETIC_INTELLIGENT_PM0.8_I40.csv"
    },
    {
        "name": "Scenario B (Fast Pyramid)",
        "file": LOG_DIR / "equity_PYRAMID_0.7_AESTHETIC_INTELLIGENT_PM0.8_T3-7.csv"
    },
    {
        "name": "Scenario C (Optimized)",
        "file": LOG_DIR / "equity_PYRAMID_0.7_AESTHETIC_INTELLIGENT_PM0.8_I40_T3-7.csv"
    }
]

results = []
print("="*60)
print("Phase 8.2 Scenario Comparison")
print("="*60)

for scen in scenarios:
    stats = calculate_stats(scen['file'])
    if stats:
        stats['name'] = scen['name']
        results.append(stats)
        print(f"[{scen['name']}]")
        print(f"  Return: {stats['total_return']:.2f}% ({stats['profit']:,.0f} KRW)")
        print(f"  MDD:    {stats['mdd']:.2f}%")
    else:
        print(f"[!] File not found: {scen['file']}")

# Comparative Analysis
if not results:
    exit()

baseline = results[0]
best_scen = max(results, key=lambda x: x['profit'])

print("-" * 60)
print(f"Best Scenario: {best_scen['name']}")
improvement = best_scen['profit'] - baseline['profit']
imp_pct = 0
if baseline['profit'] != 0:
    imp_pct = (improvement / abs(baseline['profit'])) * 100 # Improvement relative to baseline magnitude
    # Or simple growth check if baseline is negative?
    # Let's use simple logic: (New - Old)
    
print(f"Profit Improvement: +{improvement:,.0f} KRW")

# Generate Report Markdown
md_lines = []
md_lines.append("# Phase 8.2: 피라미딩 속도 최적화 결과 Report")
md_lines.append(f"\n**분석 일시**: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}")
md_lines.append("\n## 📊 시나리오별 성과 요약")
md_lines.append("| 시나리오 | 설명 | 수익률 | 총손익(KRW) | MDD | 비고 |")
md_lines.append("| :--- | :--- | :--- | :--- | :--- | :--- |")

for r in results:
    mark = ""
    if r['name'] == best_scen['name']: mark = "🏆 **Best**"
    elif r['name'] == "Baseline": mark = "Base"
    
    md_lines.append(f"| {r['name']} | - | {r['total_return']:.2f}% | **{r['profit']:,.0f}** | {r['mdd']:.2f}% | {mark} |")

md_lines.append("\n## 💡 핵심 발견")
if best_scen['profit'] > baseline['profit']:
    diff = best_scen['profit'] - baseline['profit']
    md_lines.append(f"1. **수익성 대폭 개선**: Baseline 대비 **+{diff:,.0f}원** 수익 증가")
    md_lines.append(f"2. **최적 조합 입증**: {best_scen['name']}가 가장 우수한 성과를 기록했습니다.")
    
    if best_scen['name'] == "Scenario C (Optimized)":
        md_lines.append("3. **시너지 효과**: 초기 비중 상향(40%)과 빠른 피라미딩(3%/7%)이 결합되어 급등주 수익을 극대화했습니다.")
else:
    md_lines.append("1. **개선 효과 미미**: 예상과 달리 큰 수익 개선이 관찰되지 않았습니다.")

md_lines.append("\n## 🚀 결론 및 제안")
md_lines.append(f"> **최종 선택**: **{best_scen['name']}**")
md_lines.append("- 위 설정을 라이브 트레이딩(`garam_commander.py` / `run_live_trading.py`)에 즉시 적용할 것을 권장합니다.")

report_path = OUTPUT_DIR / "Scenario_Comparison_Report.md"
with open(report_path, "w", encoding="utf-8") as f:
    f.write("\n".join(md_lines))

print(f"\n[Report Saved] {report_path}")
