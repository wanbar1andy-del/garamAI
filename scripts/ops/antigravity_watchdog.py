# scripts/ops/antigravity_watchdog.py
import argparse
import subprocess
import time
import json
from pathlib import Path
from datetime import datetime

def now():
    return datetime.now().astimezone().isoformat(timespec="seconds")

def read_status(p: Path):
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cmd", required=True, help='실행 커맨드 전체를 따옴표로 감싸서 전달')
    ap.add_argument("--status_json", default="results/ops/status/kiwoom_flow_job.json")
    ap.add_argument("--log_dir", default="results/ops/logs")
    ap.add_argument("--heartbeat_timeout_sec", type=int, default=120)
    ap.add_argument("--max_restart", type=int, default=1)
    args = ap.parse_args()

    status_path = Path(args.status_json)
    log_dir = Path(args.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)

    restarts = 0

    while True:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_log = log_dir / f"stdout_{ts}.log"
        err_log = log_dir / f"stderr_{ts}.log"

        print(f"[WATCHDOG] start {now()}")
        print(f"[WATCHDOG] cmd={args.cmd}")
        print(f"[WATCHDOG] status_json={status_path.as_posix()} timeout={args.heartbeat_timeout_sec}s")

        with out_log.open("w", encoding="utf-8") as fo, err_log.open("w", encoding="utf-8") as fe:
            p = subprocess.Popen(args.cmd, shell=True, stdout=fo, stderr=fe)

            last_seen = time.time()
            last_hb = None
            last_mtime = status_path.stat().st_mtime if status_path.exists() else None

            while True:
                time.sleep(2)

                rc = p.poll()
                if rc is not None:
                    print(f"[WATCHDOG] exited rc={rc} at {now()}")
                    if rc == 0:
                        return
                    break

                st = read_status(status_path) or {}
                hb = st.get("heartbeat_at")
                step = st.get("step")

                # (A) 핵심: hb가 변했을 때만 last_seen 갱신
                if hb and hb != last_hb:
                    last_hb = hb
                    last_seen = time.time()

                # (B) 보조: status_json mtime이 변해도 last_seen 갱신
                if status_path.exists():
                    mt = status_path.stat().st_mtime
                    if last_mtime is None:
                        last_mtime = mt
                    elif mt != last_mtime:
                        last_mtime = mt
                        last_seen = time.time()

                # DONE/FAILED인데 프로세스가 안 죽는 이상케이스 방어
                if step in ("DONE", "FAILED"):
                    try:
                        p.terminate()
                    except Exception:
                        pass

                if time.time() - last_seen > args.heartbeat_timeout_sec:
                    print(f"[ALERT] heartbeat stalled > {args.heartbeat_timeout_sec}s. killing at {now()}")
                    try:
                        p.kill()
                    except Exception:
                        pass
                    break

        restarts += 1
        if restarts > args.max_restart:
            print(f"[ALERT] STOP. exceeded max_restart={args.max_restart} at {now()}")
            return

        print(f"[WATCHDOG] restarting... attempt={restarts}/{args.max_restart}")
        time.sleep(3)

if __name__ == "__main__":
    main()
