# scripts/phase25/paper_ops_after_close_report.py
# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
import pandas as pd
import numpy as np

def _load_tape(tape_csv: Path) -> pd.DataFrame:
    df = pd.read_csv(tape_csv)
    # ts 정규화
    if "ts" in df.columns:
        df["ts"] = pd.to_datetime(df["ts"])
    else:
        raise ValueError("decision_tape.csv must have 'ts' column")
    # symbol 정규화(종목코드 6자리)
    if "symbol" in df.columns:
        df["symbol"] = df["symbol"].astype(str).str.zfill(6)
    return df

def _best_competitor_score_per_ts(tape: pd.DataFrame, hold_symbol: str) -> pd.DataFrame:
    # 각 ts마다 hold_symbol 제외한 best score 산출
    x = tape.copy()
    x = x[x["symbol"] != hold_symbol]
    if "score" not in x.columns:
        # if dummy tape or simple tape, score might be missing, but standard decision tape has it.
        # Fallback or raise? Standard decision_tape.csv has 'score'.
        raise ValueError("decision_tape.csv must have 'score' column")
    
    # Sort by ts asc, score desc -> take head(1) per ts
    best = x.sort_values(["ts", "score"], ascending=[True, False]).groupby("ts", as_index=False).head(1)
    best = best.rename(columns={"score": "best_comp_score", "symbol": "best_comp_symbol"})
    return best[["ts", "best_comp_symbol", "best_comp_score"]]

def _regret_proxy_from_switch_log(
    switch_log_csv: Path,
    tape_csv: Path,
    hold_symbol: str = "005930",
    horizon_min: int = 60,
    bar_min: int = 5,
) -> dict:
    """
    regret_proxy 정의(테이프 기반):
      각 ts에서 '지금 보유 점수(hold_score)' 대비,
      앞으로 horizon(기본 60분) 내에 등장하는 competitor best_score의 최대치 차이.
    """
    if not switch_log_csv.exists():
        return {}

    log = pd.read_csv(switch_log_csv)
    if log.empty:
        return {}
        
    if "ts" not in log.columns:
        # Try finding 'time' or other
        return {}
    log["ts"] = pd.to_datetime(log["ts"])

    if "hold_score" not in log.columns:
        return {"error": "no_hold_score"}

    tape = _load_tape(tape_csv)
    best = _best_competitor_score_per_ts(tape, hold_symbol=hold_symbol.strip().zfill(6))

    df = log.merge(best, on="ts", how="left")

    # 미래 최대 competitor score 계산(rolling forward window)
    # 60분=12 bars(5분 기준)
    k = max(1, int(horizon_min / bar_min))

    # ts 정렬 후, best_comp_score의 forward max를 계산
    df = df.sort_values("ts").reset_index(drop=True)
    arr = df["best_comp_score"].astype(float).to_numpy()
    fwd_max = []
    n = len(arr)
    # Simple rolling max window
    # Optimized: using pandas rolling with forward looking is tricky, manual loop is safe for small data
    # (Here standard daily log is small ~78 rows, manual loop is fine)
    for i in range(n):
        j = min(n, i + k)
        # i 포함, i~j-1 구간
        window = arr[i:j]
        m = float("nan")
        if len(window) > 0:
            # handle NaNs if any
            valid = window[~np.isnan(window)]
            if len(valid) > 0:
                m = float(np.max(valid))
        fwd_max.append(m)
    
    df["best_comp_score_fwdmax"] = fwd_max
    
    # Regret = (Max Future Competitor Score) - (Current Hold Score)
    # If Regret > 0, we missed a better opportunity.
    # Lower Regret is better.
    df["regret_proxy"] = df["best_comp_score_fwdmax"] - df["hold_score"].astype(float)

    # 요약 KPI
    out = {
        "regret_mean": float(df["regret_proxy"].mean(skipna=True)),
        "regret_p95": float(df["regret_proxy"].quantile(0.95, interpolation="linear")),
        "regret_max": float(df["regret_proxy"].max(skipna=True)),
        # "rows": int(len(df)),
    }
    return out

def read_one(run_dir: Path, tape_csv: Path):
    reg = pd.read_csv(run_dir / "regime_summary.csv", encoding="utf-8-sig")
    js = json.loads((run_dir / "summary.json").read_text(encoding="utf-8-sig"))
    kpi = js["kpi"]
    params = js.get("params", {})
    def pick(r):
        x = reg[reg["regime"]==r]
        if x.empty: return 0.0, 0, 0
        return float(x["switch_rate"].iloc[0]), int(x["switches"].iloc[0]), int(x["ts_count"].iloc[0])
    ir, isw, its = pick("INFLOW")
    orr, osw, ots = pick("OUTFLOW")
    nr, nsw, nts = pick("NEUTRAL")
    chase = ir - orr
    
    # Regret Proxy
    sw_log = run_dir / "switch_log_ts.csv"
    regret = _regret_proxy_from_switch_log(sw_log, tape_csv)
    
    cap_binding = False
    if "max_switches_per_day" in params and int(params["max_switches_per_day"]) < 999:
        if int(kpi["total_switches"]) >= int(params["max_switches_per_day"]) * int(kpi["days"]):
            cap_binding = True

    return {
        "run_dir": run_dir.name, # short name
        # "params": params,
        "total_switches": int(kpi["total_switches"]),
        "switch_rate": float(kpi["switch_rate"]),
        "INFLOW_rate": ir, "OUTFLOW_rate": orr, 
        "chase_score": chase,
        "regret_mean": regret.get("regret_mean", np.nan),
        "regret_max": regret.get("regret_max", np.nan),
        "cap_binding": cap_binding
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run_dirs", required=True, help="comma-separated run dirs")
    ap.add_argument("--out_md", required=True)
    # We need tape_csv to calculate regret. 
    # User's batch file doesn't pass it yet, but we can infer or add arg.
    # For robustnes, I'll try to find it from run logs OR add arg.
    # User instruction: "regret_proxy (tape based) ... I need tape path"
    # User provided batch file invokes: --run_dirs ... --out_md ...
    # It does NOT pass --tape_csv.
    # I should add --tape_csv arg and UPDATE batch file OR infer it.
    # Inferring is safer if standard path. 
    # But batch file has set TAPE=... so passing it is best.
    # I will add optional --tape_csv arg. Defaults to standard path if verified.
    ap.add_argument("--tape_csv", default="results/phase24/tape/decision_tape.csv")
    
    args = ap.parse_args()

    runs = [Path(x.strip()) for x in args.run_dirs.split(",") if x.strip()]
    tape_csv = Path(args.tape_csv)
    
    rows = [read_one(r, tape_csv) for r in runs]
    df = pd.DataFrame(rows).sort_values(["chase_score","switch_rate"], ascending=[False, True])

    out = []
    out.append("# Phase25 Paper Ops After-Close Report\n")
    out.append(f"- Tape: `{tape_csv}`")
    out.append(df.to_markdown(index=False, floatfmt=".4f"))
    out.append("\n## Notes\n")
    out.append("- **chase_score** = INFLOW_rate - OUTFLOW_rate (Positive is better)")
    out.append("- **regret_proxy**: (Forward Max Competitor Score - Current Hold Score). Lower is better.")
    out.append("- **cap_binding**: If True, switch count was capped.")

    Path(args.out_md).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out_md).write_text("\n".join(out), encoding="utf-8")
    print("[OK]", args.out_md)

if __name__ == "__main__":
    main()
