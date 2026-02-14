from __future__ import annotations

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
import pandas as pd
import glob

def _latest(pattern: str) -> str | None:
    files = sorted(glob.glob(pattern))
    return files[-1] if files else None

def generate_ops_report(
    project_root: Path,
    scan_path: str | None = None,
    diary_path: str | None = None,
    alloc_path: str | None = None,
    orders_dir: str | None = None,
):
    results_dir = project_root / "results"
    reports_dir = results_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    today_str = datetime.now().strftime("%Y%m%d")
    timestamp_str = datetime.now().strftime("%H%M%S")

    # 1. Load Scan (Truth)
    if not scan_path:
        scan_path = _latest(str(results_dir / "hero_scan_*.csv"))
        
    if not scan_path:
        print("[WARN] No scan file found. Cannot generate metric report.")
        return

    df_scan = pd.read_csv(scan_path)
    scan_meta = {
        "file": Path(scan_path).name,
        "total_symbols": len(df_scan),
        "invalid_ref_price_count": 0,
        "veto_count": 0,
        "veto_reasons": {},
        "score_stats": {}
    }

    # a) Ref Price Invalid (vetoed implies safe, but we track count)
    if "ref_price" in df_scan.columns:
        p = pd.to_numeric(df_scan["ref_price"], errors="coerce").fillna(0.0)
        invalid_mask = (p <= 0)
        scan_meta["invalid_ref_price_count"] = int(invalid_mask.sum())

    # b) Veto Stats
    if "veto" in df_scan.columns:
        # normalize
        v = df_scan["veto"].astype(str).str.lower().map({"true": True, "false": False, "1": True, "0": False}).fillna(False)
        scan_meta["veto_count"] = int(v.sum())

        if "veto_reason" in df_scan.columns:
            reasons = df_scan.loc[v, "veto_reason"].astype(str).tolist()
            from collections import Counter
            all_r = []
            for r in reasons:
                for sub in r.split(";"):
                    if sub.strip(): all_r.append(sub.strip())
            scan_meta["veto_reasons"] = dict(Counter(all_r).most_common(5))

    # c) Score Stats
    if "champion_score_norm" in df_scan.columns:
        s = pd.to_numeric(df_scan["champion_score_norm"], errors="coerce").fillna(0.0)
        scan_meta["score_stats"] = {
            "max": float(s.max()),
            "mean": float(s.mean()),
            "over_085": int((s >= 0.85).sum()),
            "over_093": int((s >= 0.93).sum()),
            "zeros": int((s == 0).sum())
        }

    # 2. Load Diary (Decision)
    if not diary_path:
        d_p = results_dir / "diary" / "hero_diary_latest.csv"
        diary_path = str(d_p) if d_p.exists() else None

    diary_meta = {
        "file": Path(diary_path).name if diary_path else None,
        "k_decision": "Unknown",
        "k_state": 0,
        "selected_count": 0,
        "weights_sum": 0.0,
        "selected_symbols": []
    }

    if diary_path and Path(diary_path).exists():
        df_diary = pd.read_csv(diary_path)
        
        # Selected are HERO or HOLD
        mask_sel = df_diary["decision"].isin(["HERO", "HOLD"])
        selected = df_diary[mask_sel].copy()
        
        count = len(selected)
        w_sum = pd.to_numeric(selected["target_weight"], errors="coerce").sum()
        
        diary_meta["selected_count"] = count
        diary_meta["weights_sum"] = float(round(w_sum, 2))
        
        # Populate selected_symbols detail
        sel_list = []
        for _, r in selected.iterrows():
            item = {
                "symbol": str(r["symbol"]).zfill(6),
                "weight": float(r["target_weight"]),
                "champion_score_norm": float(r.get("champion_score_norm", 0.0)),
                "ref_price": float(r.get("ref_price", 0.0)),
                "veto": bool(r.get("veto", False)),
                "veto_reason": str(r.get("veto_reason", ""))
            }
            sel_list.append(item)
        diary_meta["selected_symbols"] = sel_list

        # K State Logic
        if count == 0:
            diary_meta["k_state"] = 0
            diary_meta["k_decision"] = "K=0 (Rest)"
        else:
            w_vals = pd.to_numeric(selected["target_weight"], errors="coerce")
            if (w_vals >= 0.49).any():
                diary_meta["k_state"] = 2
                diary_meta["k_decision"] = "K=2 (Strong)"
            else:
                diary_meta["k_state"] = 5
                diary_meta["k_decision"] = "K=5 (Weak)"

    # 3. Output Orders Check
    if not orders_dir:
        orders_dir = str(project_root / "GARAM_Data" / "orders" / "inbox")
    
    orders_created_count = 0
    # Logic: Count files in orders_dir matching today's date pattern or simply *json if assumed clean
    # Robust: Count files with modification time within last 1 hour? Or just count all in inbox?
    # User said: "counts created". 
    # Let's count JSONs in the provided dir.
    # To be more specific about "this run", we'd need a batch ID. But counting inbox is decent proxy if we clear or manage it.
    # Let's just count all .json files in inbox as "orders_in_inbox".
    if Path(orders_dir).exists():
        orders_created_count = len(list(Path(orders_dir).glob("*.json")))

    if not alloc_path:
        alloc_path = _latest(str(results_dir / f"allocation_*.csv"))
    
    # 4. Compile Report
    report = {
        "date": today_str,
        "run_id": f"{today_str}_{timestamp_str}",
        "contract_version": "v1.2.0",
        "k_state": diary_meta["k_state"],
        "k_decision": diary_meta["k_decision"],
        "orders_created": orders_created_count,
        "scan": scan_meta,
        "diary": diary_meta,
        "pointers": {
            "hero_scan": str(Path(scan_path).absolute()) if scan_path else None,
            "hero_diary": str(Path(diary_path).absolute()) if diary_path else None,
            "allocation": str(Path(alloc_path).absolute()) if alloc_path else None,
            "orders_dir": str(Path(orders_dir).absolute()),
            "report_file": str(reports_dir.absolute() / f"ops_report_{today_str}_{timestamp_str}.json")
        }
    }

    out_file = reports_dir / f"ops_report_{today_str}_{timestamp_str}.json"
    latest_file = reports_dir / "ops_report_latest.json"
    
    # Save
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    with open(latest_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
        
    print(f"\n[OPS REPORT] Generated: {out_file}")
    print(f"  K-State: {diary_meta['k_state']} ({diary_meta['k_decision']})")
    print(f"  Orders In Inbox: {orders_created_count}")
    print(f"  Vetoes: {scan_meta['veto_count']}")
    
def main():
    p = argparse.ArgumentParser()
    p.add_argument("--scan", help="Hero Scan CSV Path")
    p.add_argument("--diary", help="Hero Diary CSV Path")
    p.add_argument("--alloc", help="Allocation CSV Path")
    p.add_argument("--orders", help="Orders Inbox Dir")
    args = p.parse_args()
    
    root = Path(__file__).resolve().parent.parent
    generate_ops_report(
        project_root=root,
        scan_path=args.scan,
        diary_path=args.diary,
        alloc_path=args.alloc,
        orders_dir=args.orders
    )

if __name__ == "__main__":
    main()
