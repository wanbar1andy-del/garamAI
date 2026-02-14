# scripts/phase24/switching_from_tape_ts.py
# -*- coding: utf-8 -*-
import argparse
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

import numpy as np
import pandas as pd


def now_local_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def write_status(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def _find_col(df: pd.DataFrame, candidates) -> Optional[str]:
    cols = {c.lower(): c for c in df.columns}
    for cand in candidates:
        if cand.lower() in cols:
            return cols[cand.lower()]
    return None


def load_flow_map(flow_csv: Path, flow_col: str = None) -> Dict[str, float]:
    """
    flow_metrics.csv: date(YYYY-mm-dd) + z_score (or flow_col)
    """
    df = pd.read_csv(flow_csv, encoding="utf-8-sig")
    date_col = _find_col(df, ["date", "일자"])
    
    z_col = None
    if flow_col:
        # User specified column
        if flow_col in df.columns:
            z_col = flow_col
        else:
            raise ValueError(f"[FLOW] specified column '{flow_col}' not found. cols={list(df.columns)}")
    else:
        # Auto-detect
        z_col = _find_col(df, ["z_score", "zscore", "z"])

    if date_col is None or z_col is None:
        raise ValueError(f"[FLOW] required columns missing. got={list(df.columns)}")

    if date_col.lower() == "일자":
        df["__date"] = pd.to_datetime(df[date_col].astype(str), format="%Y%m%d", errors="coerce")
    else:
        df["__date"] = pd.to_datetime(df[date_col], errors="coerce")

    df["__date"] = df["__date"].dt.strftime("%Y-%m-%d")
    df["__z"] = pd.to_numeric(df[z_col], errors="coerce").fillna(0.0)

    df = df.dropna(subset=["__date"]).sort_values("__date")
    return dict(zip(df["__date"], df["__z"]))


def load_tape(tape_csv: Path) -> pd.DataFrame:
    """
    decision_tape.csv expected columns:
      - ts (or datetime/date)
      - rank
      - symbol
      - score
    """
    df = pd.read_csv(tape_csv, encoding="utf-8-sig")

    ts_col = _find_col(df, ["ts", "datetime", "date", "체결시간"])
    rank_col = _find_col(df, ["rank", "순위"])
    sym_col = _find_col(df, ["symbol", "종목코드", "code"])
    score_col = _find_col(df, ["score", "점수", "pred", "model_score"])

    missing = []
    if ts_col is None: missing.append("ts")
    if rank_col is None: missing.append("rank")
    if sym_col is None: missing.append("symbol")
    if score_col is None: missing.append("score")
    if missing:
        raise ValueError(f"[TAPE] missing columns: {missing} | got={list(df.columns)}")

    df = df.rename(columns={
        ts_col: "ts",
        rank_col: "rank",
        sym_col: "symbol",
        score_col: "score",
    })

    df["ts"] = pd.to_datetime(df["ts"], errors="coerce").dt.tz_localize(None)
    df["rank"] = pd.to_numeric(df["rank"], errors="coerce")
    df["symbol"] = df["symbol"].astype(str).str.strip()
    df["score"] = pd.to_numeric(df["score"], errors="coerce")

    df = df.dropna(subset=["ts", "rank", "symbol", "score"])
    df = df[(df["symbol"] != "") & (df["symbol"].str.lower() != "nan")]
    df = df.sort_values(["ts", "rank"]).reset_index(drop=True)

    df["date"] = df["ts"].dt.strftime("%Y-%m-%d")
    return df


def regime_label(z: float, thr: float = 1.0) -> str:
    if z > thr:
        return "INFLOW"
    if z < -thr:
        return "OUTFLOW"
    return "NEUTRAL"


@dataclass
class Params:
    hold_symbol: str
    top_n: int
    gap: float
    weight: float
    clip_z: float
    min_hold_min: int
    max_switches_per_day: int
    regime_thr: float
    status_json: Optional[Path]
    status_every: int
    flow_col: Optional[str] = None


def simulate_ts_switching(df_tape: pd.DataFrame, flow_map: Dict[str, float], out_dir: Path, p: Params) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
    """
    TS 단위 스위칭 시뮬레이터 (SSOT 계약)
    - 현재 보유: hold_symbol에서 시작
    - 후보: rank<=top_n 중 최고 score
    - 조건: best_score - current_score > effective_gap
      effective_gap = gap + clip(z, -clip_z, clip_z) * weight
    - 운영 제약:
      min_hold_min, max_switches_per_day
    """

    out_dir.mkdir(parents=True, exist_ok=True)

    current_symbol: str = ""
    last_switch_ts: Optional[pd.Timestamp] = None
    cooldown_until_ts: Optional[pd.Timestamp] = None  # TODO: cooldown 정책 도입 시 사용
    switches_today: int = 0
    current_date: Optional[pd.Timestamp] = None

    total_ts = df_tape["ts"].nunique()
    done_ts = 0

    rows = []

    if p.status_json:
        write_status(p.status_json, {
            "step": "START",
            "heartbeat_at": now_local_iso(),
            "job": {
                "tape_csv": "(in-memory)",
                "flow_csv": "(in-memory)",
                "hold_symbol": p.hold_symbol,
                "gap": p.gap,
            },
            "progress": {"total_ts": 0, "done_ts": 0, "note": "Starting simulation"}
        })

    rows = []
    
    # Group by TS
    groups = df_tape.groupby("ts", sort=True)
    total_ts = len(groups)
    done_ts = 0

    try:
        for ts, g in groups:
            done_ts += 1
            d = ts.strftime("%Y-%m-%d")

            if current_date != d:
                current_date = d
                switches_today = 0

            # z-score & regime (from flow_map)
            if p.flow_col:
                d_str = ts.strftime("%Y-%m-%d")
                z = flow_map.get(d_str, 0.0)
                regime = get_regime(z, p.regime_thr)
            else:
                z = 0.0
                regime = "NEUTRAL"
                
            # Hold Score
            if current_symbol == "":
                current_score = float(-np.inf)
                cur_note = "NO_POS"
            else:
                cur_mask = (g["symbol"] == current_symbol)
                if cur_mask.any():
                    current_score = float(g.loc[cur_mask, "score"].max())
                else:
                    # Tape에서 보유종목 점수 누락 -> 강제 매도 or Low Score 취급
                    # 운영상 중요: 데이터 누락인가, 상폐인가? -> 일단 -inf로 간주하여 교체 유도
                    current_score = float(-np.inf)

            # Gap Boost
            hold_boost = 0.0
            if regime == "INFLOW":
                hold_boost = abs(p.clip_z) * p.weight # Max boost
            elif regime == "OUTFLOW":
                hold_boost = -abs(p.clip_z) * p.weight # Max penalty (reduce gap) => easier to switch? No.
                # Wait, formula: eff_gap = gap + clip(z)*weight
                # If weight > 0:
                #   Inflow(z>0) -> eff_gap increases (Harder to switch, 'Boost' holding)
                #   Outflow(z<0) -> eff_gap decreases (Easier to switch)
            
            # Calculate eff_gap accurately based on current z
            gap_val = p.gap # Base gap
            if p.weight != 0:
                 clipped_z = max(-p.clip_z, min(p.clip_z, z))
                 gap_val += (clipped_z * p.weight)
            
            eff_gap = gap_val

            # 후보: rank<=top_n 중 최고 score
            cand = g[g["rank"] <= p.top_n].copy()
            if cand.empty:
                best_symbol = current_symbol
                best_score = float(-np.inf)
            else:
                cand = cand.sort_values("score", ascending=False)
                best_symbol = str(cand.iloc[0]["symbol"])
                best_score = float(cand.iloc[0]["score"])

            diff_best_minus_current = float(best_score - current_score)

            # --- [Brake Observability Logic START] ---
            # 15-column spec: ts/symbol/bar_tf/side/engine_mode/mss_score/signal/exposure_target/exposure_applied/cap_hit/cap_value/min_hold_left_min/cooldown_left_min/gate_code/gate_detail

            bar_tf = "1m"
            side = "LONG"

            # signal / MSS proxy
            signal = float(z)
            mss_score = float(abs(signal))

            # engine mode
            turbo_threshold = 1.5  # TODO: CLI/Params로 승격(권장)
            engine_mode = "TURBO" if (mss_score >= turbo_threshold) else "NORMAL"

            # exposure/cap
            exposure_target = 1.5 if engine_mode == "TURBO" else 1.0
            cap_value = 1.0
            exposure_applied = min(exposure_target, cap_value)
            cap_hit = (exposure_target > exposure_applied)

            # min_hold_left
            min_hold_left_min = 0
            if last_switch_ts is not None and p.min_hold_min > 0:
                elapsed_min = (ts - last_switch_ts).total_seconds() / 60.0
                min_hold_left_min = int(max(0, np.ceil(p.min_hold_min - elapsed_min)))

            # cooldown (미구현=0, 추후 구현)
            cooldown_left_min = 0
            if cooldown_until_ts is not None:
                left = (cooldown_until_ts - ts).total_seconds() / 60.0
                cooldown_left_min = int(max(0, np.ceil(left)))

            # gate_code 표준 ENUM만 사용
            gate_code = "OK"
            gate_reason = "OK"

            # 1) 후보 없음
            if best_score == float(-np.inf):
                gate_code = "MSS_BLOCK"
                gate_reason = "NO_CANDIDATE"
            else:
                # 2) 갭/점수차 미달
                if diff_best_minus_current <= eff_gap:
                    gate_code = "MSS_BLOCK"
                    gate_reason = "GAP_NOT_MET"
                else:
                    # 3) min_hold
                    if min_hold_left_min > 0:
                        gate_code = "MIN_HOLD"
                        gate_reason = "MIN_HOLD_ACTIVE"
                    # 4) cooldown
                    elif cooldown_left_min > 0:
                        gate_code = "COOLDOWN"
                        gate_reason = "COOLDOWN_ACTIVE"
                    # 5) daily cap
                    elif switches_today >= p.max_switches_per_day:
                        gate_code = "DAILY_STOP"
                        gate_reason = "DAILY_SWITCH_CAP"

            # CAP은 “노출” 차원의 브레이크. 스위칭과 별개지만 관측상 표기 가치가 있음
            if gate_code == "OK" and cap_hit:
                gate_code = "CAP"
                gate_reason = "EXPOSURE_CLIPPED"

            gate_detail = (
                f"reason={gate_reason}; "
                f"cur={current_symbol} best={best_symbol}; "
                f"cur_score={current_score:.4f} best_score={best_score:.4f} diff={diff_best_minus_current:.4f} eff_gap={eff_gap:.4f}; "
                f"min_hold_left={min_hold_left_min}; cooldown_left={cooldown_left_min}; sw_today={switches_today}; "
                f"cap_hit={cap_hit} target={exposure_target:.2f} applied={exposure_applied:.2f}"
            )

            brake_event = (gate_code != "OK") or cap_hit
            # --- [Brake Observability Logic END] ---

            # --- Switching Logic (single source of truth) ---
            # 스위치 조건은 gate_code==OK 이고, best가 current와 다를 때만
            switch = (gate_code == "OK") and (best_symbol != current_symbol)

            current_symbol_before = current_symbol
            if switch:
                switches_today += 1
                last_switch_ts = ts
                current_symbol = best_symbol
                # TODO: cooldown 도입 시 여기서 cooldown_until_ts 갱신
                
            rows.append({
                # --- Spec 15 ---
                "ts": ts.strftime("%Y-%m-%d %H:%M:%S"),
                "symbol": current_symbol_before,          # 결정 전 보유(권장)
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

                # --- Existing / useful ---
                "date": d,
                "regime": regime,
                "z_score": z,
                "hold_boost": hold_boost,
                "gap_base": p.gap,
                "gap_effective": eff_gap,
                "top_n": p.top_n,
                "current_symbol_before": current_symbol_before,
                "current_symbol_after": current_symbol,   # 결정 후 보유(권장)
                "current_score": current_score,
                "best_symbol": best_symbol,
                "best_score": best_score,
                "diff_best_minus_current": diff_best_minus_current,
                "switch": int(switch),
                "switches_today": switches_today,
                "brake_event": brake_event,
            })

            # status 업데이트 (운영 가시성)
            if p.status_json and (done_ts % p.status_every == 0 or done_ts == total_ts):
                write_status(p.status_json, {
                    "step": "RUNNING" if done_ts < total_ts else "DONE",
                    "heartbeat_at": now_local_iso(),
                    "progress": {
                        "total_ts": int(total_ts),
                        "done_ts": int(done_ts),
                        "current_ts": ts.strftime("%Y-%m-%d %H:%M:%S"),
                        "current_symbol": current_symbol,
                        "switches_today": int(switches_today),
                    },
                    "last_error": None,
                })

        if rows:
            df_log = pd.DataFrame(rows)
        else:
            cols = [
                "ts", "date", "symbol", "bar_tf", "side", "engine_mode", "mss_score", "signal",
                "exposure_target", "exposure_applied", "cap_hit", "cap_value",
                "min_hold_left_min", "cooldown_left_min", "gate_code", "gate_detail",
                "regime", "z_score", "hold_boost", "gap_base", "gap_effective",
                "top_n", "current_symbol_before", "current_symbol_after", "current_score", "best_symbol", "best_score",
                "diff_best_minus_current", "switch", "switches_today", "brake_event"
            ]
            df_log = pd.DataFrame(columns=cols)
        print(f"[DEBUG] df_log shape={df_log.shape}")
        if not df_log.empty:
             print(f"[DEBUG] columns={list(df_log.columns)}")
             print(df_log.head(2))
        else:
             print("[DEBUG] df_log is EMPTY!")

        # daily summary
        df_daily = df_log.groupby("date").agg(
            ts_count=("ts", "count"),
            switches=("switch", "sum"),
            inflow_count=("regime", lambda s: int((s == "INFLOW").sum())),
            outflow_count=("regime", lambda s: int((s == "OUTFLOW").sum())),
            neutral_count=("regime", lambda s: int((s == "NEUTRAL").sum())),
        ).reset_index()

        # regime summary
        df_reg = df_log.groupby("regime").agg(
            ts_count=("ts", "count"),
            switches=("switch", "sum"),
        ).reset_index()
        df_reg["switch_rate"] = df_reg["switches"] / df_reg["ts_count"].replace(0, np.nan)
        
        # [Brake KPI Calculation]
        if not df_log.empty and "cap_hit" in df_log.columns:
            cap_hit_rate = float(df_log["cap_hit"].mean())
            # gate stats
            gate_counts = df_log["gate_code"].value_counts().to_dict()
            gate_total = len(df_log)
            gate_stats = {k: int(v) for k, v in gate_counts.items()}
        else:
            cap_hit_rate = 0.0
            gate_stats = {}

        # overall summary json
        summary = {
            "params": {
                "hold_symbol": p.hold_symbol,
                "top_n": p.top_n,
                "gap": p.gap,
                "weight": p.weight,
                "clip_z": p.clip_z,
                "min_hold_min": p.min_hold_min,
                "max_switches_per_day": p.max_switches_per_day,
                "max_switches_per_day": p.max_switches_per_day,
                "regime_thr": p.regime_thr,
                "flow_col": p.flow_col,
            },
            "kpi": {
                "total_ts": int(df_log.shape[0]),
                "total_switches": int(df_log["switch"].sum()),
                "switch_rate": float(df_log["switch"].mean()) if df_log.shape[0] else 0.0,
                "days": int(df_daily.shape[0]),
            },
            "brake_kpi": {
                "cap_hit_rate": cap_hit_rate,
                "gate_stats": gate_stats
            },
            "timestamp": now_local_iso(),
        }

        return df_log, df_daily, df_reg, summary

    except Exception as e:
        if p.status_json:
            write_status(p.status_json, {
                "step": "FAILED",
                "heartbeat_at": now_local_iso(),
                "progress": {"total_ts": int(total_ts), "done_ts": int(done_ts)},
                "last_error": f"{type(e).__name__}: {e}",
            })
        raise


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tape_csv", required=True, help="decision_tape.csv (ts, rank, symbol, score)")
    ap.add_argument("--flow_metrics_csv", required=True, help="flow_metrics.csv (date, z_score)")
    ap.add_argument("--out_dir", required=True)

    ap.add_argument("--hold_symbol", default="005930")
    ap.add_argument("--top_n", type=int, default=3)
    ap.add_argument("--gap", type=float, default=2.0)
    ap.add_argument("--weight", type=float, default=2.0)
    ap.add_argument("--clip_z", type=float, default=2.0)
    ap.add_argument("--regime_thr", type=float, default=1.0)

    ap.add_argument("--min_hold_min", type=int, default=0)
    ap.add_argument("--max_switches_per_day", type=int, default=6)

    ap.add_argument("--status_json", default="")
    ap.add_argument("--status_every", type=int, default=200)  # ts 그룹 몇 번마다 상태 갱신할지
    ap.add_argument("--flow_col", default=None, help="Specific column to use as Z-score (e.g. foreigner_z20)")
    args = ap.parse_args()

    tape_csv = Path(args.tape_csv)
    flow_csv = Path(args.flow_metrics_csv)
    out_dir = Path(args.out_dir)

    if not tape_csv.exists():
        raise FileNotFoundError(f"tape_csv not found: {tape_csv.as_posix()}")
    if not flow_csv.exists():
        raise FileNotFoundError(f"flow_metrics_csv not found: {flow_csv.as_posix()}")

    status_json = Path(args.status_json) if args.status_json.strip() else None

    params = Params(
        hold_symbol=str(args.hold_symbol).strip(),
        top_n=int(args.top_n),
        gap=float(args.gap),
        weight=float(args.weight),
        clip_z=float(args.clip_z),
        min_hold_min=int(args.min_hold_min),
        max_switches_per_day=int(args.max_switches_per_day),
        regime_thr=float(args.regime_thr),
        status_json=status_json,
        status_every=max(1, int(args.status_every)),
        flow_col=args.flow_col if args.flow_col else None,
    )

    tape_df = load_tape(Path(args.tape_csv))
    print(f"[DEBUG] load_tape: {len(tape_df)} rows")
    if not tape_df.empty:
        print(tape_df.head(2))
    
    flow_map = load_flow_map(Path(args.flow_metrics_csv), flow_col=params.flow_col)

    df_log, df_daily, df_reg, summary = simulate_ts_switching(tape_df, flow_map, out_dir, params)

    out_dir.mkdir(parents=True, exist_ok=True)
    df_log.to_csv(out_dir / "switch_log_ts.csv", index=False, encoding="utf-8-sig")
    df_daily.to_csv(out_dir / "daily_summary.csv", index=False, encoding="utf-8-sig")
    df_reg.to_csv(out_dir / "regime_summary.csv", index=False, encoding="utf-8-sig")
    (out_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print("[OK] saved:")
    print(f" - { (out_dir / 'switch_log_ts.csv').as_posix() }")
    print(f" - { (out_dir / 'daily_summary.csv').as_posix() }")
    print(f" - { (out_dir / 'regime_summary.csv').as_posix() }")
    print(f" - { (out_dir / 'summary.json').as_posix() }")
    print()
    print(f"[KPI] total_ts={summary['kpi']['total_ts']} total_switches={summary['kpi']['total_switches']} switch_rate={summary['kpi']['switch_rate']:.4f}")


if __name__ == "__main__":
    main()
