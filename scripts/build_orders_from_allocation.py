from __future__ import annotations

import json
import math
from pathlib import Path
from datetime import datetime
import argparse
import pandas as pd


def _now_kst_compact() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def build_orders(
    allocation_csv: Path,
    aum: float,
    out_dir: Path,
    buffer: float = 0.99,
    dry_run: bool = False,
) -> int:
    if not allocation_csv.exists():
        raise FileNotFoundError(f"allocation csv not found: {allocation_csv}")

    df = pd.read_csv(allocation_csv)
    for c in ("symbol", "target_weight", "ref_price"):
        if c not in df.columns:
            raise ValueError(f"allocation csv missing required column: {c}")

    df["symbol"] = df["symbol"].astype(str).str.zfill(6)
    df["target_weight"] = pd.to_numeric(df["target_weight"], errors="coerce").fillna(0.0)
    df["ref_price"] = pd.to_numeric(df["ref_price"], errors="coerce").fillna(0.0)

    # Optional veto columns
    if "veto" in df.columns:
        df["veto"] = df["veto"].astype(bool)
    else:
        df["veto"] = False

    # K=0 or veto => 0 orders guaranteed, by simply filtering weight>0 & veto=False
    candidates = df[(df["target_weight"] > 0) & (~df["veto"])].copy()

    # Skip cash pseudo-symbol if present
    candidates = candidates[candidates["symbol"] != "00CASH"]

    batch = _now_kst_compact()
    out_dir.mkdir(parents=True, exist_ok=True)

    created = 0
    for _, r in candidates.iterrows():
        sym = r["symbol"]
        w = float(r["target_weight"])
        px = float(r["ref_price"])

        if px <= 0 or not math.isfinite(px):
            print(f"[SKIP] {sym}: ref_price invalid ({px})")
            continue

        capital = aum * w * buffer
        qty = int(math.floor(capital / px))

        if qty <= 0:
            print(f"[SKIP] {sym}: qty=0 (capital={capital:.0f}, px={px})")
            continue

        req = {
            "request_id": f"req_{batch}_{created+1:03d}_{sym}",
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "symbol": sym,
            "side": "BUY",
            "qty": qty,
            "ref_price": px,
            "target_weight": w,
            "aum": aum,
            "buffer": buffer,
            "notional_est": qty * px,
            "source_allocation": str(allocation_csv),
            "strategy": "CHAMPION_HERO_V21_SSOT",
        }

        if dry_run:
            print(f"[DRY] {req['request_id']} BUY {sym} qty={qty} ref={px} w={w}")
        else:
            out_path = out_dir / f"{req['request_id']}.json"
            out_path.write_text(json.dumps(req, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"[NEW] {out_path.name} BUY {sym} qty={qty} ref={px} w={w}")

        created += 1

    print(f"[DONE] Created {created} orders (dry_run={dry_run}) | out_dir={out_dir}")
    return created


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--allocation", required=True, type=str, help="CSV path (must include symbol,target_weight,ref_price)")
    p.add_argument("--aum", required=True, type=float, help="AUM (KRW)")
    p.add_argument("--out_dir", default="GARAM_Data/orders/inbox", type=str)
    p.add_argument("--buffer", default=0.99, type=float)
    p.add_argument("--dry_run", action="store_true")
    args = p.parse_args()

    build_orders(
        allocation_csv=Path(args.allocation),
        aum=args.aum,
        out_dir=Path(args.out_dir),
        buffer=args.buffer,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
