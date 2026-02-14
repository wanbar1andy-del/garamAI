from __future__ import annotations

import argparse
import time
import sys
from pathlib import Path
from datetime import datetime

import pandas as pd

# Ensure importable
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from pipeline._01_ingest.paths import get_ingest_paths
from pipeline._02_validate.paths import get_validate_paths
from pipeline._02_validate.minute_validate import validate_minute_csv


def _is_valid_symbol(sym: str) -> bool:
    sym = str(sym).strip()
    return sym.isdigit() and len(sym) <= 6


def _load_universe_symbols(project_root: Path, limit: int | None) -> list[str]:
    # Use sync'd ingest universe (ensured by running sync before this)
    uni_path = project_root / "GARAM_Data" / "real_universe_400.csv"
    if not uni_path.exists():
         print(f"[WARN] Ingest universe not found at {uni_path}. Using fallback SSOT via Store.")
         from pipeline.store.data_loader import store
         df = store.get_universe()
         col = "symbol" if "symbol" in df.columns else "Code"
    else:
        df = pd.read_csv(uni_path, dtype=str)
        col = "symbol" if "symbol" in df.columns else ("Code" if "Code" in df.columns else None)
        
    if col is None:
        raise ValueError(f"[RECOLLECT] universe missing symbol column. cols={df.columns.tolist()}")

    syms = []
    for x in df[col].tolist():
        s = str(x).strip()
        if not _is_valid_symbol(s):
            # 운영에서는 이런 값이 끼면 재앙입니다. 즉시 FAIL로 다루는 게 맞습니다.
            syms.append(s)  # 그대로 기록 (리포트에 남기기 위해)
        else:
            syms.append(s.zfill(6))

    if limit:
        syms = syms[:limit]
    return syms


def _write_recollect_targets(project_root: Path, symbols: list[str]) -> Path:
    path = project_root / "recollect_targets.txt"
    # 숫자 6자리만 기록 (불량 심볼은 스킵)
    clean = [s for s in symbols if isinstance(s, str) and s.isdigit() and len(s) == 6]
    path.write_text("\n".join(clean) + ("\n" if clean else ""), encoding="utf-8")
    return path


def _kiwoom_ready(project_root: Path) -> bool:
    return (project_root / "GARAM_Data" / "kiwoom_ready.flag").exists()


def _snapshot_mtimes(minute_dir: Path, targets: list[str]) -> dict[str, float]:
    snap = {}
    for s in targets:
        f = minute_dir / f"{s}.csv"
        snap[s] = f.stat().st_mtime if f.exists() else 0.0
    return snap


def _poll_updated(minute_dir: Path, targets: list[str], prev_mtimes: dict[str, float], 
                  wait_sec: int, poll_sec: int) -> dict[str, bool]:
    deadline = time.time() + wait_sec
    done = {s: False for s in targets}

    while time.time() < deadline:
        for s in targets:
            if done[s]:
                continue
            f = minute_dir / f"{s}.csv"
            # Condition: mtime increased from snapshot
            if f.exists() and f.stat().st_mtime > prev_mtimes.get(s, 0.0):
                done[s] = True

        if all(done.values()):
            break
        time.sleep(poll_sec)

    return done


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--max_rounds", type=int, default=3)
    p.add_argument("--wait_sec", type=int, default=600, help="키움 재수집 대기(초)")
    p.add_argument("--poll_sec", type=int, default=5)
    args = p.parse_args()

    # project_root is already resolved at module level but let's be explicit
    project_root = Path(__file__).resolve().parent.parent

    ipaths = get_ingest_paths(project_root)
    vpaths = get_validate_paths(project_root)

    # Round loop
    for round_i in range(1, args.max_rounds + 1):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        print(f"\n=== Recollect Loop Round {round_i}/{args.max_rounds} @ {ts} ===")

        universe = _load_universe_symbols(project_root, args.limit)

        rows = []
        fail_syms = []

        # 1) Validate
        print(f"[VALIDATE] Checking {len(universe)} symbols...")
        for sym in universe:
            # Check validity first
            if not (isinstance(sym, str) and sym.isdigit() and len(sym) == 6):
                rows.append({"symbol": sym, "status": "FAIL", "message": "invalid symbol in universe"})
                fail_syms.append(sym)
                continue

            in_path = ipaths.minute_dir / f"{sym}.csv"
            out_path = vpaths.validated_minute_dir / f"{sym}.csv"

            if not in_path.exists():
                rows.append({"symbol": sym, "status": "FAIL", "message": "missing input csv"})
                fail_syms.append(sym)
                continue

            try:
                # Use validate module directly
                valid, res = validate_minute_csv(sym, in_path, out_path=out_path)
                rows.append(res.__dict__)
                if res.status == "FAIL":
                    fail_syms.append(sym)
            except Exception as e:
                rows.append({"symbol": sym, "status": "FAIL", "message": f"exception: {e}"})
                fail_syms.append(sym)

        rep_dir = project_root / "results"
        rep_dir.mkdir(parents=True, exist_ok=True)
        rep_path = rep_dir / f"recollect_validate_round{round_i}_{ts}.csv"
        
        # Report fix: robust status & newline
        df_rep = pd.DataFrame(rows)
        if not df_rep.empty and "status" in df_rep.columns:
             df_rep = df_rep[df_rep["status"].astype(str).str.strip() != ""]
             
        df_rep.to_csv(rep_path, index=False, encoding="utf-8", lineterminator="\n")
        print(f"[REPORT] {rep_path}")

        if not fail_syms:
            print("[OK] No FAIL. Loop complete.")
            # 정리: 남아있는 recollect_targets.txt는 비우는 게 운영적으로 안전합니다.
            _write_recollect_targets(project_root, [])
            return

        # 2) Write recollect targets
        rt_path = _write_recollect_targets(project_root, fail_syms)
        print(f"[RECOLLECT] wrote: {rt_path} symbols={len(fail_syms)}")

        # 3) Require Kiwoom ready (Check flag)
        if not _kiwoom_ready(project_root):
            print("[ACTION REQUIRED] kiwoom_ready.flag not found.")
            print(" - 키움 수집기(run_ingest_kiwoom.py)를 실행/로그인 상태로 만든 후 재실행하십시오.")
            # In a real loop we might pause or exit. Here we exit to ask user intervention.
            return

        # 4) Poll file updates
        # Only poll valid numeric symbols in fail list
        poll_targets = sorted(list(set([s for s in fail_syms if s.isdigit() and len(s) == 6])))
        
        # [Fix] Snapshot mtime before writing targets (to capture base state)
        # Actually logic demands we snapshot BEFORE the external process updates them.
        # But here external process (Kiwoom) reacts to the txt file. So snapshotting NOW is correct.
        print(f"[WAIT] Snapping mtimes for {len(poll_targets)} targets...")
        prev_mtimes = _snapshot_mtimes(ipaths.minute_dir, poll_targets)
        
        print(f"[WAIT] polling updates in {ipaths.minute_dir} for {args.wait_sec}s ...")
        done = _poll_updated(ipaths.minute_dir, poll_targets, prev_mtimes, args.wait_sec, args.poll_sec)

        not_done = [s for s, ok in done.items() if not ok]
        if not_done:
            print(f"[WARN] not updated within wait window: {len(not_done)} symbols")
            # Loop continues to next round (which will re-validate and potentially re-add them)
        else:
            print("[OK] all recollect targets updated.")

    print("\n[STOP] max_rounds reached. Check reports and investigate persistent FAIL symbols.")


if __name__ == "__main__":
    main()
