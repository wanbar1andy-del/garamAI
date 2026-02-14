# -*- coding: utf-8 -*-
import argparse
from pathlib import Path

def die(msg: str, code: int = 1):
    print(f"[FAIL] {msg}")
    raise SystemExit(code)

def ok(msg: str):
    print(f"[OK] {msg}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data_dir", required=True)
    ap.add_argument("--symbol", required=True, help="e.g., 005930")
    ap.add_argument("--check_date", required=True, help="e.g., 20251230 (YYYYMMDD)")
    ap.add_argument("--max_scan_lines", type=int, default=300000, help="avoid full scan if very large")
    args = ap.parse_args()

    data_dir = Path(args.data_dir)
    sym = str(args.symbol).strip().zfill(6)
    check_date = str(args.check_date).strip()

    if not data_dir.exists():
        die(f"data_dir not found: {data_dir}")

    f = data_dir / f"{sym}.csv"
    if not f.exists():
        die(f"symbol file not found: {f}")

    # Fast scan: stream lines, stop when found
    found = False
    scanned = 0
    try:
        with f.open("r", encoding="utf-8", errors="ignore") as fp:
            for line in fp:
                scanned += 1
                # line format: YYYYMMDDHHMMSS,open,high,low,close,volume
                if line.startswith(check_date):
                    found = True
                    break
                if scanned >= args.max_scan_lines:
                    break
    except Exception as e:
        die(f"read failed: {f} ({type(e).__name__}: {e})")

    ok(f"data_dir exists: {data_dir}")
    ok(f"symbol file exists: {f}")
    ok(f"scanned lines: {scanned}")

    if not found:
        die(f"check_date not found in file (date={check_date}, symbol={sym})", code=1)

    ok(f"check_date found: {check_date} in {sym}.csv")
    print("[PASS] Integrity check completed.")
    raise SystemExit(0)

if __name__ == "__main__":
    main()
