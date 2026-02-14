import sys
import pandas as pd
from pathlib import Path
from datetime import timedelta
import numpy as np
from itertools import groupby
import logging

# Setup Path
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent.parent
sys.path.append(str(project_root))

from garam_core.fastlane.feature_store import FeatureStore
from scripts.ops.run_replay_batch import simulate_day_intraday, pre_load_data

def _setup_logger(out_path: Path) -> logging.Logger:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("density_check")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")

    fh = logging.FileHandler(out_path, encoding="utf-8")
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(fmt)
    logger.addHandler(sh)

    return logger

def run_density_check():
    out_path = project_root / "results" / "diagnostics" / "density_report.txt"
    logger = _setup_logger(out_path)

    logger.info("=== Signal Density Diagnostics ===")
    logger.info("Target: Validate Singleton Hypothesis (2/5/0 starvation)")

    # Config (Phase 22 sealed baseline)
    entry_roc = -0.02
    entry_vol = 1.2
    exit_sl = -0.02
    exit_tp = 0.03
    time_stop = 40
    days_to_check = 10

    # Universe
    universe_path = project_root / "GARAM_Data" / "real_universe_400.csv"
    df_univ = pd.read_csv(universe_path)
    raw_codes = df_univ["Code"].astype(str).tolist()
    valid_universe = [c.zfill(6) for c in raw_codes if c.zfill(6).isdigit() and len(c.zfill(6)) == 6]
    if "475960" in valid_universe:
        valid_universe.remove("475960")

    logger.info(f"Universe: {len(valid_universe)} symbols")

    # Load data
    logger.info("Loading data (pre_load_data) ... this can take a while.")
    data_map, ma60_map = pre_load_data(valid_universe)
    loaded_syms = list(data_map.keys())
    logger.info(f"Loaded: {len(loaded_syms)} symbols (valid)")

    # Dates
    fs = FeatureStore()
    df_sample = fs.get_features("005930")
    dates = pd.to_datetime(df_sample["date"]).dt.tz_localize(None).dt.normalize().unique()
    dates = sorted(dates)
    target_dates = dates[-days_to_check:]
    logger.info(f"Checking Range: {target_dates[0].date()} ~ {target_dates[-1].date()}")

    # Aggregates
    total_cycles = 0
    singleton_cycles = 0
    double_cycles = 0
    multi_cycles = 0

    daily_rows = []

    for current_date in target_dates:
        all_candidates = []
        cand_errors = 0

        for sym in loaded_syms:
            try:
                df_all = data_map[sym]
                start_ts = current_date
                end_ts = current_date + timedelta(days=1)
                i_start = df_all["date"].searchsorted(start_ts)
                i_end = df_all["date"].searchsorted(end_ts)
                if i_start == i_end:
                    continue

                df_day = df_all.iloc[i_start:i_end].copy()

                ma60 = ma60_map.get(sym, None)
                ma60_val = 0
                if isinstance(ma60, pd.Series) and not ma60.empty:
                    if current_date in ma60.index:
                        ma60_val = ma60.loc[current_date]
                    else:
                        asof_idx = ma60.index.searchsorted(current_date)
                        ma60_val = ma60.iloc[asof_idx - 1] if asof_idx > 0 else ma60.iloc[0]

                cands = simulate_day_intraday(
                    sym, df_day, ma60_val,
                    entry_roc, entry_vol, exit_sl, exit_tp, time_stop, 0
                )
                all_candidates.extend(cands)

            except Exception:
                cand_errors += 1

        all_candidates.sort(key=lambda x: x["ts"])

        day_cycles = 0
        day_singletons = 0
        day_doubles = 0
        day_multis = 0

        for key, group in groupby(all_candidates, key=lambda x: x["ts"]):
            g_list = list(group)
            size = len(g_list)

            total_cycles += 1
            day_cycles += 1

            if size == 1:
                singleton_cycles += 1
                day_singletons += 1
            elif size == 2:
                double_cycles += 1
                day_doubles += 1
            else:
                multi_cycles += 1
                day_multis += 1

        singleton_ratio = (day_singletons / day_cycles * 100) if day_cycles > 0 else 0.0

        daily_rows.append({
            "date": str(current_date.date()),
            "candidates": len(all_candidates),
            "cycles": day_cycles,
            "singleton_cycles": day_singletons,
            "singleton_ratio_pct": singleton_ratio,
            "double_cycles": day_doubles,
            "multi_cycles": day_multis,
            "errors": cand_errors,
        })

        logger.info(
            f"{current_date.date()} | candidates={len(all_candidates)} cycles={day_cycles} "
            f"singletons={day_singletons} ({singleton_ratio:.1f}%) errors={cand_errors}"
        )

    # Summary
    singleton_ratio = (singleton_cycles / total_cycles * 100) if total_cycles > 0 else 0.0
    double_ratio = (double_cycles / total_cycles * 100) if total_cycles > 0 else 0.0

    logger.info("=== SUMMARY ===")
    logger.info(f"Total Cycles: {total_cycles}")
    logger.info(f"Singleton Cycles: {singleton_cycles} ({singleton_ratio:.1f}%)")
    logger.info(f"Double Cycles: {double_cycles} ({double_ratio:.1f}%)")
    logger.info(f"Multi Cycles: {multi_cycles}")

    df_daily = pd.DataFrame(daily_rows)
    csv_path = project_root / "results" / "diagnostics" / "density_daily.csv"
    df_daily.to_csv(csv_path, index=False, encoding="utf-8")
    logger.info(f"Saved daily stats: {csv_path}")

    if singleton_ratio > 40:
        logger.info("[CONCLUSION] CONFIRMED: High Singleton Ratio => 2/5/0 starvation risk (minmax norm collapse).")
    else:
        logger.info("[CONCLUSION] REJECTED: Singleton Ratio not dominant. Investigate other failure modes.")

if __name__ == "__main__":
    run_density_check()
