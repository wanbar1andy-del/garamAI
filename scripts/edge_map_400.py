import json
from pathlib import Path
import pandas as pd
import sys

# 1) 리포트 위치
# Use absolute or relative path correctly
REPORT_ROOT = Path("garam_core/reports") # verify_turbo_v3.py saves to garam_core/reports usually?
# Let's check verify_turbo_v3.py's reports_root path.
# verify_turbo_v3.py Line 307: reports_root = project_root / "reports"
# project_root = "c:/garam/garam/garam_core"
# So REPORT_ROOT = "c:/garam/garam/garam_core/reports"
# BUT the scripts I run might be relative.
# I will check iteratively.

def main():
    # Try finding reports dir
    candidates = [Path("garam_core/reports"), Path("reports"), Path("../garam_core/reports")]
    report_root = None
    for c in candidates:
        if c.exists():
            report_root = c
            break
            
    if not report_root:
        print("Reports directory not found!")
        return

    print(f"Scanning reports in: {report_root}")

    # 2) 전체 결과 저장용
    rows = []
    by_regime_rows = []

    for run_dir in report_root.iterdir():
        if not run_dir.is_dir():
            continue
        # Filter for verify_turbo_v3
        if "verify_turbo_v3_" not in run_dir.name:
            continue
            
        report_path = run_dir / "report.json"
        if not report_path.exists():
            continue
        
        try:
            with open(report_path, "r", encoding="utf-8") as f:
                report = json.load(f)
        except Exception as e:
            print(f"Error reading {report_path}: {e}")
            continue

        meta = report.get("meta", {})
        sym = meta.get("data", {}).get("universe", run_dir.name)
        
        # Overall
        if "edge_analysis" not in report:
             print(f"Skipping {run_dir.name} (No edge_analysis)")
             continue
             
        ov = report["edge_analysis"].get("overall", {})
        summary_kpis = report.get("summary", {}).get("kpis", {})
        
        row = {
            "symbol": sym,
            "total_return": summary_kpis.get("total_return", 0.0),
            "net_expectancy": ov.get("expectancy_net", 0.0),
            "gross_expectancy": ov.get("expectancy_gross", 0.0),
            "cost_avg": ov.get("cost_per_trade_avg", 0.0),
            "win_rate": ov.get("win_rate", 0.0),
            "mdd": ov.get("mdd", 0.0),
            "trades": ov.get("trades", 0),
            "trades_per_day": ov.get("trades_per_day", 0.0),
            "run_id": meta.get("run_id", "")
        }
        rows.append(row)
        
        # By regime
        by_regime = report["edge_analysis"].get("by_regime", {})
        for regime, data in by_regime.items():
            if data.get("trades", 0) > 0:
                by_regime_rows.append({
                    "symbol": sym,
                    "regime": regime,
                    "net_expectancy": data.get("expectancy_net", 0.0),
                    "trades": data.get("trades", 0),
                    "win_rate": data.get("win_rate", 0.0),
                    "cost_avg": data.get("cost_per_trade_avg", 0.0),
                })

    if not rows:
        print("No reports found.")
        return

    # 통합 DataFrame 생성
    df_overall = pd.DataFrame(rows)
    df_regime = pd.DataFrame(by_regime_rows)

    # CSV 저장
    df_overall.to_csv("edge_map_overall_400.csv", index=False)
    df_regime.to_csv("edge_map_by_regime_400.csv", index=False)

    print("400종목 EdgeMap CSV 생성 완료!")
    print(f"Overall Shape: {df_overall.shape}")
    print(f"By Regime Shape: {df_regime.shape}")

if __name__ == "__main__":
    main()
