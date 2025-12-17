from __future__ import annotations

import argparse
from pathlib import Path
from datetime import datetime
import pandas as pd

from pipeline._02_validate.paths import get_validate_paths
from pipeline._02_validate.minute_validate import validate_minute_csv


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--universe", default="data/universe_real_400.csv")
    p.add_argument("--limit", type=int, default=50)
    p.add_argument("--project_root", default=None)
    p.add_argument("--write_recollect", action="store_true")
    p.add_argument("--out_report", default=None)
    args = p.parse_args()

    project_root = Path(args.project_root) if args.project_root else None
    paths = get_validate_paths(project_root)

    uni = pd.read_csv(args.universe, dtype={"symbol": str})
    symbols = [str(s).strip().zfill(6) for s in uni["symbol"].tolist()][: args.limit]

    rows = []
    bad = []

    for i, sym in enumerate(symbols, 1):
        in_path = paths.minute_dir / f"{sym}.csv"
        if not in_path.exists():
            bad.append(sym)
            rows.append({"symbol": sym, "status": "FAIL", "message": "missing input csv"})
            continue

        try:
            out_path = paths.validated_minute_dir / f"{sym}.csv"
            _, res = validate_minute_csv(sym, in_path, out_path=out_path)
            rows.append(res.__dict__)
            if res.status == "FAIL":
                bad.append(sym)
        except Exception as e:
            bad.append(sym)
            rows.append({"symbol": sym, "status": "FAIL", "message": f"exception: {e}"})

        if i % 25 == 0:
            print(f"[VALIDATE] {i}/{len(symbols)} ...")

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = Path(args.out_report) if args.out_report else Path("results") / f"validate_report_{ts}.csv"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(report_path, index=False, encoding="utf-8")
    print(f"[VALIDATE] report saved: {report_path}")

    if args.write_recollect and bad:
        paths.recollect_targets.write_text("\n".join(bad) + "\n", encoding="utf-8")
        print(f"[VALIDATE] recollect_targets.txt updated: {len(bad)} symbols")


if __name__ == "__main__":
    main()
