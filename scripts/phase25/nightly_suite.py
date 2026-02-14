# scripts/phase25/nightly_suite.py
# -*- coding: utf-8 -*-
import argparse
import json
from pathlib import Path
from datetime import datetime
import numpy as np
import pandas as pd

def iso_now():
    return datetime.now().astimezone().isoformat(timespec="seconds")

def ensure_dir(p: Path):
    p.mkdir(parents=True, exist_ok=True)
    return p

def load_opt10059_csv(raw_csv: Path) -> pd.DataFrame:
    df = pd.read_csv(raw_csv)
    if "일자" not in df.columns:
        raise ValueError("OPT10059 raw csv must contain '일자' column")
    df["date"] = pd.to_datetime(df["일자"].astype(str), format="%Y%m%d", errors="coerce")
    df = df.dropna(subset=["date"])
    # 날짜 정렬 + 중복 제거(최신행)
    df = df.sort_values("date")
    df = df.drop_duplicates(subset=["date"], keep="last")
    return df

def zscore_rolling(s: pd.Series, win: int = 20) -> pd.Series:
    m = s.rolling(win).mean()
    sd = s.rolling(win).std(ddof=0)
    return (s - m) / sd.replace(0, np.nan)

def ratio_feature(s: pd.Series, win: int = 20, eps: float = 1.0) -> pd.Series:
    # “규모 변화”에 강한 정규화: net / rolling(abs(net)) 평균
    denom = s.abs().rolling(win).mean() + eps
    return s / denom

def build_flow_metrics(raw_df: pd.DataFrame, cols: list[str], win: int = 20) -> pd.DataFrame:
    out = pd.DataFrame({"date": raw_df["date"]})
    for c in cols:
        if c not in raw_df.columns:
            continue
        x = pd.to_numeric(raw_df[c], errors="coerce").fillna(0.0)
        out[f"{c}"] = x
        out[f"{c}_z{win}"] = zscore_rolling(x, win)
        r = ratio_feature(x, win=win)
        out[f"{c}_ratio"] = r
        out[f"{c}_ratio_z{win}"] = zscore_rolling(r, win)
    return out

def load_tape(tape_csv: Path) -> pd.DataFrame:
    df = pd.read_csv(tape_csv)
    if "ts" not in df.columns:
        raise ValueError("tape_csv must contain 'ts' column")
    df["ts"] = pd.to_datetime(df["ts"])
    # 필수 컬럼 보정
    for col in ["rank", "symbol", "score"]:
        if col not in df.columns:
            raise ValueError(f"tape_csv must contain '{col}' column")
    df["rank"] = pd.to_numeric(df["rank"], errors="coerce").fillna(999).astype(int)
    df["score"] = pd.to_numeric(df["score"], errors="coerce")
    
    # We apply zfill(6) to be safe for KR stocks.
    def _norm(x):
        s = str(x).strip()
        if s.isdigit():
            return s.zfill(6)
        return s
    df["symbol"] = df["symbol"].apply(_norm)
    
    df = df.dropna(subset=["score"])
    df["date"] = df["ts"].dt.strftime("%Y-%m-%d")
    return df.sort_values(["ts", "rank"])

def regime_from_z(z: float, thr: float = 1.0) -> str:
    if z > thr:
        return "INFLOW"
    if z < -thr:
        return "OUTFLOW"
    return "NEUTRAL"

def simulate_ts_switching(
    tape: pd.DataFrame,
    flow_map: dict[str, float],
    hold_symbol: str,
    top_n: int,
    gap: float,
    weight: float,
    clip_z: float,
    min_hold_min: int,
    max_switches_per_day: int,
    regime_thr: float,
) -> pd.DataFrame:
    # 상태
    cur = hold_symbol
    last_switch_ts = None
    switches_today = 0
    cur_day = None

    rows = []

    for ts, g in tape.groupby("ts", sort=True):
        day = ts.strftime("%Y-%m-%d")
        if cur_day != day:
            cur_day = day
            switches_today = 0

        z = float(flow_map.get(day, 0.0))
        reg = regime_from_z(z, regime_thr)
        boost = float(np.clip(z, -clip_z, clip_z) * weight)
        eff_gap = float(gap + boost)

        # 현재 보유 종목 점수(없으면 스위칭 금지로 처리)
        cur_row = g[g["symbol"] == cur]
        
        # NOTE: if multiple rows for same symbol, take max score
        if cur_row.empty:
            hold_score = np.nan
            blocked = "HOLD_SCORE_MISSING"
        else:
            hold_score = float(cur_row["score"].max())
            blocked = None

        # 경쟁자: rank 1~top_n 중 보유종목 제외 최고
        cand = g[g["rank"] <= top_n].copy()
        cand = cand[cand["symbol"] != cur]
        
        best_symbol = None
        best_score = np.nan
        
        if not cand.empty:
            best = cand.sort_values("score", ascending=False).iloc[0]
            best_symbol = str(best["symbol"])
            best_score = float(best["score"])
        
        if blocked is None and best_symbol is None:
            blocked = "NO_CANDIDATE"

        # 제약: min_hold / cap
        if blocked is None:
            if last_switch_ts is not None and min_hold_min > 0:
                if (ts - last_switch_ts).total_seconds() < (min_hold_min * 60):
                    blocked = "MIN_HOLD"
            if blocked is None and switches_today >= max_switches_per_day:
                blocked = "DAILY_CAP"

        # 스위칭 판정
        do_switch = 0
        want_switch = False
        
        if blocked is None and best_symbol is not None:
            want_switch = (best_score > hold_score + eff_gap)
            if want_switch:
                do_switch = 1
                cur = best_symbol
                last_switch_ts = ts
                switches_today += 1

        # --- [Brake Observability Logic START] ---
        # Spec-aligned fields (15 columns)

        # 0) Basic
        bar_tf = "1m"
        side = "LONG" # Side is always LONG for this Long-Only strategy

        # 1) Signal / MSS proxy
        signal = float(z)
        mss_score = float(abs(z))

        # 2) Engine Mode (from MSS proxy)
        turbo_threshold = 1.5 
        engine_mode = "TURBO" if (mss_score >= turbo_threshold) else "NORMAL"

        # 3) Exposure & Cap (Separated from weight)
        exposure_target = 1.5 if engine_mode == "TURBO" else 1.0
        cap_max = 1.0 # Rename local var to avoid conflict with 'cap' arg if any
        exposure_applied = min(exposure_target, cap_max)
        cap_hit = (exposure_target > exposure_applied)
        cap_value = cap_max

        # 4) min_hold_left / cooldown_left
        min_hold_left_min = 0
        if last_switch_ts is not None and min_hold_min > 0:
            elapsed_min = (ts - last_switch_ts).total_seconds() / 60.0
            min_hold_left_min = int(max(0, np.ceil(min_hold_min - elapsed_min)))

        cooldown_left_min = 0 # TODO: Implement Cooldown logic

        # 5) gate_code standardization
        gate_code = "OK"
        if blocked == "MIN_HOLD":
            gate_code = "MIN_HOLD"
        elif blocked == "DAILY_CAP":
            gate_code = "DAILY_STOP"
        elif blocked == "HOLD_SCORE_MISSING":
            gate_code = "MSS_BLOCK"
        elif blocked == "NO_CANDIDATE":
            gate_code = "MSS_BLOCK" 
        else:
             # blocked=None but want_switch=False means "Conditions not met" (Gap, Score etc)
             if (blocked is None) and (best_symbol is not None) and (not want_switch):
                 gate_code = "MSS_BLOCK" # Grouping logic failures as MSS/Signal Block

        gate_detail = (
            f"blocked={blocked}; want_switch={want_switch}; "
            f"hold={hold_score:.4f} best={best_score:.4f} eff_gap={eff_gap:.4f}; "
            f"min_hold_left={min_hold_left_min}; cooldown_left={cooldown_left_min}; "
            f"cap_hit={cap_hit} target={exposure_target:.2f} applied={exposure_applied:.2f}"
        )
        
        # 6) brake_event
        brake_event = (gate_code != "OK") or cap_hit
        # --- [Brake Observability Logic END] ---

        rows.append({
            # --- Spec 15 ---
            "ts": ts,
            "symbol": cur,
            "bar_tf": bar_tf,
            "side": side,
            "engine_mode": engine_mode,
            "mss_score": mss_score,
            "signal": signal,
            "exposure_target": exposure_target,
            "exposure_applied": exposure_applied,
            "cap_hit": cap_hit,
            "cap_value": cap_value,
            "min_hold_left_min": min_hold_left_min,
            "cooldown_left_min": cooldown_left_min,
            "gate_code": gate_code,
            "gate_detail": gate_detail,

            # --- Existing fields (for debugging/compatibility) ---
            "date": day, "regime": reg, "z": z,
            "hold_score": hold_score,
            "best_symbol": best_symbol, "best_score": best_score,
            "gap": gap, "boost": boost, "eff_gap": eff_gap,
            "switch": do_switch,
            "blocked_reason": blocked if (blocked is not None) else ("" if want_switch else "SCORE_DIFF_LOW"),
            "brake_event": brake_event,
        })

    if rows:
        out = pd.DataFrame(rows)
    else:
        cols = [
            "ts", "symbol", "bar_tf", "side", "engine_mode", "mss_score", "signal",
            "exposure_target", "exposure_applied", "cap_hit", "cap_value",
            "min_hold_left_min", "cooldown_left_min", "gate_code", "gate_detail",
            "date", "regime", "z", "hold_score", "best_symbol", "best_score",
            "gap", "boost", "eff_gap", "switch", "blocked_reason", "brake_event"
        ]
        out = pd.DataFrame(columns=cols)
    return out

def summarize_run(log_df: pd.DataFrame) -> dict:
    total_ts = int(len(log_df))
    total_sw = int(log_df["switch"].sum()) if "switch" in log_df.columns else 0
    switch_rate = float(total_sw / total_ts) if total_ts else 0.0
    miss_hold = int((log_df["blocked_reason"] == "HOLD_SCORE_MISSING").sum()) if "blocked_reason" in log_df.columns else 0
    
    cap_hit_rate = float(log_df["cap_hit"].mean()) if "cap_hit" in log_df.columns and total_ts else 0.0

    cap_clip_amount = 0.0
    if {"cap_hit","exposure_target","exposure_applied"}.issubset(log_df.columns):
        hit = log_df[log_df["cap_hit"] == True]
        if len(hit):
            cap_clip_amount = float((hit["exposure_target"] - hit["exposure_applied"]).mean())

    # Turbo "미진입"은 이 스크립트에서는 'turbo 구간에서 switch가 막힌 비율'로 정의(현실적인 해석)
    turbo_trade_miss_rate = 0.0
    turbo_gate_stats = {}
    if {"mss_score","gate_code"}.issubset(log_df.columns):
        turbo_threshold = 1.5  # TODO: args와 동일하게 맞추기
        turbo = log_df[log_df["mss_score"] >= turbo_threshold]
        if len(turbo):
            turbo_trade_miss_rate = float((turbo["gate_code"] != "OK").mean())
            turbo_gate_stats = {k: int(v) for k, v in turbo["gate_code"].value_counts().to_dict().items()}

    gate_stats = {}
    if "gate_code" in log_df.columns:
        gate_stats = {k: int(v) for k, v in log_df["gate_code"].value_counts().to_dict().items()}

    return {
        "total_ts": total_ts,
        "total_switches": total_sw,
        "switch_rate": switch_rate,
        "hold_score_missing": miss_hold,
        "cap_hit_rate": cap_hit_rate,
        "cap_clip_amount": cap_clip_amount,
        "turbo_trade_miss_rate": turbo_trade_miss_rate,
        "gate_stats": gate_stats,
        "turbo_gate_stats": turbo_gate_stats,
        "days": int(log_df["date"].nunique()) if "date" in log_df.columns else 0,
    }

def regime_summary(log_df: pd.DataFrame) -> pd.DataFrame:
    g = log_df.groupby("regime", dropna=False)
    out = g.agg(ts_count=("ts", "count"), switches=("switch", "sum")).reset_index()
    out["switch_rate"] = out["switches"] / out["ts_count"]
    return out

def compare_flips(baseline: pd.DataFrame, boosted: pd.DataFrame) -> pd.DataFrame:
    b0 = baseline[["ts", "switch"]].rename(columns={"switch": "switch_b0"})
    b1 = boosted[["ts", "switch"]].rename(columns={"switch": "switch_b1"})
    m = pd.merge(b0, b1, on="ts", how="inner")
    m["flip"] = (m["switch_b0"] != m["switch_b1"]).astype(int)
    return m

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw_opt10059_csv", required=True)
    ap.add_argument("--tape_csv", required=True)
    ap.add_argument("--out_dir", required=True)

    ap.add_argument("--hold_symbol", default="005930")
    ap.add_argument("--top_n", type=int, default=3)
    ap.add_argument("--win", type=int, default=20)
    ap.add_argument("--signal", default="외국인투자자_ratio_z20",
                    help="flow_metrics column to use as z (e.g., 외국인투자자_ratio_z20, 연기금등_ratio_z20)")
    ap.add_argument("--gap_list", default="1.5,2.0,2.5")
    ap.add_argument("--weight_list", default="0,0.5,1,2,3")
    ap.add_argument("--min_hold_list", default="0,10,60")
    ap.add_argument("--cap_list", default="6,12,999")
    ap.add_argument("--clip_z", type=float, default=2.0)
    ap.add_argument("--regime_thr", type=float, default=1.0)

    args = ap.parse_args()

    out_dir = ensure_dir(Path(args.out_dir))
    ensure_dir(out_dir / "runs")

    raw_df = load_opt10059_csv(Path(args.raw_opt10059_csv))

    # metrics 생성
    investor_cols = ["개인투자자","외국인투자자","기관계","금융투자","투신","연기금등"]
    metrics = build_flow_metrics(raw_df, investor_cols, win=args.win)
    metrics_path = out_dir / "flow_metrics_built.csv"
    metrics.to_csv(metrics_path, index=False, encoding="utf-8-sig")

    if args.signal not in metrics.columns:
        raise ValueError(f"signal not found in built metrics: {args.signal}\navailable: {list(metrics.columns)}")

    # date -> z map (signal)
    flow_map = dict(zip(metrics["date"].dt.strftime("%Y-%m-%d"), pd.to_numeric(metrics[args.signal], errors="coerce").fillna(0.0)))

    tape = load_tape(Path(args.tape_csv))

    gap_list = [float(x.strip()) for x in args.gap_list.split(",") if x.strip()]
    w_list = [float(x.strip()) for x in args.weight_list.split(",") if x.strip()]
    hold_list = [int(x.strip()) for x in args.min_hold_list.split(",") if x.strip()]
    cap_list = [int(x.strip()) for x in args.cap_list.split(",") if x.strip()]

    # Baseline 고정: weight=0, gap=2.0, min_hold=0, cap=999
    base_gap = 2.0 if 2.0 in gap_list else (gap_list[0] if gap_list else 2.0)
    baseline = simulate_ts_switching(
        tape=tape,
        flow_map=flow_map,
        hold_symbol=args.hold_symbol,
        top_n=args.top_n,
        gap=base_gap,
        weight=0.0,
        clip_z=args.clip_z,
        min_hold_min=0,
        max_switches_per_day=999,
        regime_thr=args.regime_thr,
    )
    baseline_dir = ensure_dir(out_dir / "runs" / "baseline_w0")
    baseline.to_csv(baseline_dir / "switch_log_ts.csv", index=False, encoding="utf-8-sig")
    regime_summary(baseline).to_csv(baseline_dir / "regime_summary.csv", index=False, encoding="utf-8-sig")
    
    # Baseline Obs
    obs_dir = ensure_dir(baseline_dir / "obs")
    if "gate_code" in baseline.columns and "cap_hit" in baseline.columns:
        brake_events = baseline[(baseline["gate_code"] != "OK") | (baseline["cap_hit"] == True)].copy()
        brake_events.to_csv(obs_dir / "brake_events_baseline.csv", index=False, encoding="utf-8-sig")

    bkpi = summarize_run(baseline)
    with (baseline_dir / "summary.json").open("w", encoding="utf-8") as f:
        json.dump({"params": {"gap": base_gap, "weight": 0.0}, "kpi": bkpi, "ts": iso_now()}, f, ensure_ascii=False, indent=2)

    # Grid
    grid_rows = []
    for gap in gap_list:
        for w in w_list:
            for mh in hold_list:
                for cap in cap_list:
                    run_name = f"g{gap}_w{w}_mh{mh}_cap{cap}"
                    run_dir = ensure_dir(out_dir / "runs" / run_name)
                    log = simulate_ts_switching(
                        tape=tape,
                        flow_map=flow_map,
                        hold_symbol=args.hold_symbol,
                        top_n=args.top_n,
                        gap=gap,
                        weight=w,
                        clip_z=args.clip_z,
                        min_hold_min=mh,
                        max_switches_per_day=cap,
                        regime_thr=args.regime_thr,
                    )
                    log.to_csv(run_dir / "switch_log_ts.csv", index=False, encoding="utf-8-sig")
                    rs = regime_summary(log)
                    rs.to_csv(run_dir / "regime_summary.csv", index=False, encoding="utf-8-sig")

                    kpi = summarize_run(log)

                    # flips vs baseline
                    flips = compare_flips(baseline, log)
                    flip_cnt = int(flips["flip"].sum())
                    flips.to_csv(run_dir / "flips_vs_baseline.csv", index=False, encoding="utf-8-sig")

                    # 3) brake_events.csv
                    obs_dir = ensure_dir(run_dir / "obs")
                    if "gate_code" in log.columns and "cap_hit" in log.columns:
                        brake_events = log[(log["gate_code"] != "OK") | (log["cap_hit"] == True)].copy()
                        brake_events.to_csv(obs_dir / f"brake_events_{run_name}.csv", index=False, encoding="utf-8-sig")

                    row = {
                        "run": run_name,
                        "gap": gap, "weight": w, "min_hold_min": mh, "cap": cap,
                        "total_ts": kpi["total_ts"],
                        "switches": kpi["total_switches"],
                        "switch_rate": kpi["switch_rate"],
                        "flip_cnt": flip_cnt,
                        "hold_score_missing": kpi["hold_score_missing"],
                        "cap_hit_rate": kpi["cap_hit_rate"],
                        "cap_clip_amt": kpi["cap_clip_amount"],
                        "turbo_miss": kpi["turbo_trade_miss_rate"],
                    }
                    # regime 별 switch_rate
                    for _, r in rs.iterrows():
                        reg = r["regime"]
                        row[f"{reg}_rate"] = float(r["switch_rate"])
                        row[f"{reg}_switches"] = int(r["switches"])
                        row[f"{reg}_ts"] = int(r["ts_count"])
                    grid_rows.append(row)

                    with (run_dir / "summary.json").open("w", encoding="utf-8") as f:
                        json.dump({"params": {
                            "gap": gap, "weight": w, "min_hold_min": mh, "cap": cap,
                            "hold_symbol": args.hold_symbol, "top_n": args.top_n,
                            "signal": args.signal, "clip_z": args.clip_z, "regime_thr": args.regime_thr
                        }, "kpi": kpi, "ts": iso_now()}, f, ensure_ascii=False, indent=2)

    grid = pd.DataFrame(grid_rows)
    grid_path = out_dir / "grid_results.csv"
    grid.to_csv(grid_path, index=False, encoding="utf-8-sig")

    # 보고서(MD) 생성
    rep = []
    rep.append(f"# Phase25 Nightly Report\n- ts: {iso_now()}\n")
    rep.append(f"## Inputs\n- raw_opt10059_csv: {Path(args.raw_opt10059_csv).as_posix()}\n- tape_csv: {Path(args.tape_csv).as_posix()}\n- signal: {args.signal}\n")
    rep.append(f"## Built Metrics\n- {metrics_path.as_posix()}\n")
    rep.append("## Baseline (w=0)\n")
    
    # Baseline Stat Formatting
    # bkpi is already computed above
    rep.append("### KPIs")
    rep.append(f"- Switch Rate: {bkpi['switch_rate']:.4f}")
    rep.append(f"- Cap Hit Rate: {bkpi['cap_hit_rate']:.4f}")
    rep.append(f"- Cap Clip Amount: {bkpi['cap_clip_amount']:.4f}")
    rep.append(f"- Turbo Trade Miss Rate: {bkpi['turbo_trade_miss_rate']:.4f}")
    rep.append(f"- Total Switches: {bkpi['total_switches']}")
    
    rep.append("\n### Brake Gate Stats")
    rep.append("| Gate Code | Count |")
    rep.append("|---|---|")
    for k, v in bkpi['gate_stats'].items():
        rep.append(f"| {k} | {v} |")
    
    if bkpi.get('turbo_gate_stats'):
        rep.append("\n### Turbo Miss Top Causes")
        rep.append("| Gate Code | Count |")
        rep.append("|---|---|")
        # Top 3
        sorted_turbo = sorted(bkpi['turbo_gate_stats'].items(), key=lambda x: x[1], reverse=True)[:3]
        for k, v in sorted_turbo:
             rep.append(f"| {k} | {v} |")

    rep.append("\n")
    rep.append((baseline_dir / "summary.json").read_text(encoding="utf-8") + "\n")
    
    rep.append("## Grid (Top 20 by lowest switch_rate)\n")

    show = grid.sort_values(["switch_rate","flip_cnt"], ascending=[True, False]).head(20)
    rep.append(show.to_markdown(index=False))
    rep.append("\n\n## Notes\n- switch_rate만 낮추는 튜닝은 ‘수익’과 무관할 수 있습니다. 반드시 Regret/PnL 결합 리포트를 다음 단계에서 붙이세요.\n- hold_score_missing이 크면 tape에 보유종목 점수 누락이 있는 것입니다(테이프 생성기 수정 대상).\n")

    report_path = out_dir / "report.md"
    report_path.write_text("\n".join(rep), encoding="utf-8")

    print(f"[OK] saved:\n- {report_path.as_posix()}\n- {grid_path.as_posix()}\n- {metrics_path.as_posix()}")

if __name__ == "__main__":
    main()
