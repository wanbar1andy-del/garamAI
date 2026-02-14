from __future__ import annotations

import argparse
from pathlib import Path
from datetime import datetime
import pandas as pd

from scripts.scan_heroes_fast import scan_heroes_fast


def _parse_int_list(s: str) -> list[int]:
    # "20,25,30" -> [20,25,30]
    out = []
    for tok in s.split(","):
        tok = tok.strip()
        if tok:
            out.append(int(tok))
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--probe", default="MR_RSI_30")
    p.add_argument("--windows", default="20,25,30,35,40")
    p.add_argument("--limit", type=int, default=400)

    p.add_argument("--tail_rows", type=int, default=20000)
    p.add_argument("--fast_cache", action="store_true")
    p.add_argument("--cache_dir", default="cache/hero_scan")

    p.add_argument("--two_pass", action="store_true")
    p.add_argument("--top_k", type=int, default=50)
    p.add_argument("--tail_rows2", type=int, default=None)

    # allocate는 튜닝에선 보통 불필요하지만 옵션으로 남겨둠
    p.add_argument("--allocate", action="store_true")
    p.add_argument("--aum", type=float, default=10_000_000)
    p.add_argument("--alloc_mode", default="equal", choices=["equal", "score"])

    args = p.parse_args()

    project_root = Path(__file__).resolve().parent.parent
    cache_dir = project_root / args.cache_dir
    results_dir = project_root / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    windows = _parse_int_list(args.windows)
    rows = []

    for w in windows:
        out = scan_heroes_fast(
            project_root=project_root,
            probe=args.probe,
            window=int(w),
            limit=int(args.limit) if args.limit else None,
            tail_rows=int(args.tail_rows),
            two_pass=bool(args.two_pass),
            top_k=int(args.top_k),
            tail_rows2=args.tail_rows2,
            allocate=bool(args.allocate),
            aum=float(args.aum),
            alloc_mode=str(args.alloc_mode),
            fast_cache=bool(args.fast_cache),
            cache_dir=cache_dir,
            write_outputs=False,  # sweep는 파일 남발 방지
        )
        rows.append({
            "probe": args.probe,
            "window": int(w),
            "limit": args.limit,
            "tail_rows": args.tail_rows,
            "two_pass": int(args.two_pass),
            "top_k": args.top_k,
            "heroes": out["heroes"],
            "cache_hit": out["cache_hit"],
            "cache_miss": out["cache_miss"],
            "errors": out["errors"],
            "elapsed_sec": out["elapsed_sec"],
        })
        print(f"[SWEEP] window={w} heroes={out['heroes']} hit={out['cache_hit']} miss={out['cache_miss']} elapsed={out['elapsed_sec']}s")

    df = pd.DataFrame(rows)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = results_dir / f"tune_sweep_{args.probe}_{ts}.csv"
    df.to_csv(out_path, index=False, encoding="utf-8-sig")

    print("\n=== TUNE SWEEP OUTPUT ===")
    print(out_path)
    print("=========================")


if __name__ == "__main__":
    main()
