"""
Phase X-5c: BPC-VWAP Reclaim Grid
- Afternoon-only breakout detection (grid option)
- Pullback wait (depth grid)
- Rebound confirmation: VWAP reclaim + EMA20 + (optional volume factor) + hold N bars
- Stop: pullback low (pb_low) based stop with buffer
- TP: +5% (intrabar high), Trailing: +2%->1%, +3%->1.2% (close-based trigger)
- One-shot: 1 trade per symbol per day

Data:
  - Input:  GARAM_Data/60day_replay_kst/*.csv
  - Output: GARAM_Data/phase_x5c_grid_summary.csv
            GARAM_Data/phase_x5c_trades_<TAG>.csv
"""

import os
import glob
import numpy as np
import pandas as pd
from enum import Enum
from datetime import time as dtime
import argparse

class State(Enum):
    IDLE = 0
    BREAKOUT_DETECTED = 1
    PULLBACK_WAIT = 2
    RECLAIM_WAIT = 3
    EXPIRED = 4


def load_all_data(data_dir="GARAM_Data/60day_replay_kst"):
    files = glob.glob(os.path.join(data_dir, "*.csv"))
    data_cache = {}

    for f in files:
        try:
            sym = os.path.basename(f).replace(".csv", "")
            df = pd.read_csv(f, parse_dates=["ts"])
            if df.empty:
                continue

            # hygiene
            df = df.sort_values("ts").drop_duplicates(subset=["ts"], keep="last").reset_index(drop=True)
            df["date"] = df["ts"].dt.date

            # keep only required columns (optional)
            keep_cols = ["ts", "open", "high", "low", "close", "volume", "date"]
            df = df[[c for c in keep_cols if c in df.columns]].copy()

            data_cache[sym] = df
        except Exception:
            continue

    print(f"Loaded {len(data_cache)} symbols from {data_dir}")
    return data_cache


def compute_day_indicators(day_df, lookback=30, vol_ma_period=20, ema_span=20):
    """
    Adds:
      - vol_ma: rolling mean(volume)
      - high_30: rolling max(high)
      - ema20: EWM(close)
      - vwap: intraday VWAP (daily reset because day_df is already one day)
    """
    df = day_df.copy()

    # rolling indicators
    df["vol_ma"] = df["volume"].rolling(vol_ma_period).mean()
    df["high_30"] = df["high"].rolling(lookback).max()

    # EMA
    df["ema20"] = df["close"].ewm(span=ema_span, adjust=False).mean()

    # VWAP (typical price)
    tp = (df["high"] + df["low"] + df["close"]) / 3.0
    pv = tp * df["volume"].astype(float)

    cum_vol = df["volume"].astype(float).cumsum()
    cum_pv = pv.cumsum()

    df["vwap"] = np.where(cum_vol > 0, cum_pv / cum_vol, np.nan)

    # fill vwap holes (rare)
    df["vwap"] = df["vwap"].fillna(df["close"])

    return df


def simulate_trade(day_df, entry_idx, entry_price, stop_price,
                   tp_pct=5.0,
                   trail_trigger_1=2.0, trail_stop_1=1.0,
                   trail_trigger_2=3.0, trail_stop_2=1.2):
    """
    Intrabar evaluation:
      - STOP: if low <= stop_price
      - TP: if high >= entry_price*(1+tp_pct)
      - TRAIL: close-based, using max_pnl (by high) and trail_level
      - else EOD close
    Returns: (exit_type, exit_price, exit_time, realized_pnl, mfe_pct, mae_pct)
    """

    target_tp_price = entry_price * (1.0 + tp_pct / 100.0)

    exit_type = "EOD"
    exit_price = float(day_df.iloc[-1]["close"])
    exit_time = day_df.iloc[-1]["ts"]

    max_pnl = 0.0
    min_pnl = 0.0
    trail_level = None

    for fidx in range(entry_idx + 1, len(day_df)):
        r = day_df.iloc[fidx]
        high_price = float(r["high"])
        low_price = float(r["low"])
        close_price = float(r["close"])

        high_pnl = (high_price / entry_price - 1.0) * 100.0
        low_pnl = (low_price / entry_price - 1.0) * 100.0
        close_pnl = (close_price / entry_price - 1.0) * 100.0

        # update MFE/MAE
        if high_pnl > max_pnl:
            max_pnl = high_pnl
        if low_pnl < min_pnl:
            min_pnl = low_pnl

        # STOP (intrabar low)
        if low_price <= stop_price:
            exit_type = "STOP"
            exit_price = float(stop_price)
            exit_time = r["ts"]
            break

        # TP (intrabar high)
        if high_price >= target_tp_price:
            exit_type = "TP"
            exit_price = float(target_tp_price)
            exit_time = r["ts"]
            break

        # trailing update
        if max_pnl >= trail_trigger_2:
            trail_level = max_pnl - trail_stop_2
        elif max_pnl >= trail_trigger_1:
            trail_level = max_pnl - trail_stop_1

        # trailing trigger by close
        if trail_level is not None and close_pnl <= trail_level:
            exit_type = "TRAIL"
            exit_price = float(entry_price * (1.0 + trail_level / 100.0))
            exit_time = r["ts"]
            break

    realized_pnl = (exit_price / entry_price - 1.0) * 100.0
    return exit_type, exit_price, exit_time, realized_pnl, max_pnl, min_pnl


def run_x5c_for_params(data_cache, dates, params):
    """
    Params:
      - no_breakout_before: time
      - pb_depth: float (e.g., 0.02)
      - hold_bars: int (VWAP reclaim consecutive bars)
      - vol_factor: float or None (volume confirm on reclaim bars)
      - vol_mult: float
      - lookback: int
      - vol_ma_period: int
      - high_update_window: int (bars after breakout to allow break_high updates)
      - max_wait_bars: int (pullback wait limit from breakout)
      - stop_buffer: float (stop below pb_low)
    """

    # unpack
    no_breakout_before = params["no_breakout_before"]
    pb_depth = params["pb_depth"]
    hold_bars = params["hold_bars"]
    vol_factor = params["vol_factor"]

    vol_mult = params.get("vol_mult", 2.0)
    lookback = params.get("lookback", 30)
    vol_ma_period = params.get("vol_ma_period", 20)
    high_update_window = params.get("high_update_window", 10)
    max_wait_bars = params.get("max_wait_bars", 60)
    stop_buffer = params.get("stop_buffer", 0.002)

    tp_pct = params.get("tp_pct", 5.0)
    trail_trigger_1 = params.get("trail_trigger_1", 2.0)
    trail_stop_1 = params.get("trail_stop_1", 1.0)
    trail_trigger_2 = params.get("trail_trigger_2", 3.0)
    trail_stop_2 = params.get("trail_stop_2", 1.2)

    trades = []
    stats = {
        "breakouts": 0,
        "pullbacks": 0,
        "reclaims": 0,
        "entries": 0,
        "expired": 0,
        "skipped_short_day": 0,
    }

    start_idx = max(lookback, vol_ma_period) + 1

    for date in dates:
        for sym, df in data_cache.items():
            day_df = df[df["date"] == date].copy()
            if len(day_df) < start_idx + 50:
                stats["skipped_short_day"] += 1
                continue

            day_df = day_df.sort_values("ts").drop_duplicates(subset=["ts"], keep="last").reset_index(drop=True)
            day_df = compute_day_indicators(day_df, lookback=lookback, vol_ma_period=vol_ma_period, ema_span=20)

            state = State.IDLE
            traded_today = False

            breakout_idx = None
            breakout_idx_orig = None
            break_high = None

            pb_low_price = None
            reclaim_count = 0

            for idx in range(start_idx, len(day_df)):
                if traded_today:
                    break

                row = day_df.iloc[idx]
                ts = row["ts"]
                t = ts.time()

                # 1) IDLE: detect breakout (afternoon-only)
                if state == State.IDLE:
                    if t < no_breakout_before:
                        continue

                    prev = day_df.iloc[idx - 1]
                    prev_vol_ma = float(prev["vol_ma"]) if not np.isnan(prev["vol_ma"]) else np.nan
                    prev_high_30 = float(prev["high_30"]) if not np.isnan(prev["high_30"]) else np.nan

                    if np.isnan(prev_vol_ma) or prev_vol_ma <= 0:
                        continue
                    if np.isnan(prev_high_30) or prev_high_30 <= 0:
                        continue

                    if float(row["volume"]) > prev_vol_ma * vol_mult and float(row["close"]) >= prev_high_30:
                        state = State.BREAKOUT_DETECTED
                        breakout_idx = idx
                        breakout_idx_orig = idx
                        break_high = float(row["high"])
                        stats["breakouts"] += 1
                        continue

                # 2) BREAKOUT_DETECTED: wait pullback, update break_high only in window
                elif state == State.BREAKOUT_DETECTED:
                    # expiry from original breakout
                    if idx - breakout_idx_orig > max_wait_bars:
                        state = State.EXPIRED
                        stats["expired"] += 1
                        continue

                    # update break_high (only early window)
                    if (idx - breakout_idx_orig) <= high_update_window:
                        if float(row["high"]) > break_high:
                            break_high = float(row["high"])

                    # pullback condition (depth)
                    pb_by_low = float(row["low"]) <= break_high * (1.0 - pb_depth)
                    pb_by_close = float(row["close"]) <= break_high * (1.0 - pb_depth)

                    if pb_by_low or pb_by_close:
                        state = State.RECLAIM_WAIT
                        pb_low_price = float(row["low"])
                        reclaim_count = 0
                        stats["pullbacks"] += 1
                        continue

                # 3) RECLAIM_WAIT: update pb_low, wait for VWAP reclaim + EMA20 + hold
                elif state == State.RECLAIM_WAIT:
                    # expiry (allow longer than pullback)
                    if idx - breakout_idx_orig > max_wait_bars * 2:
                        state = State.EXPIRED
                        stats["expired"] += 1
                        continue

                    # update pullback low
                    pb_low_price = min(pb_low_price, float(row["low"]))

                    # reclaim condition
                    # check if current vwap is valid
                    vwap = float(row["vwap"])
                    if np.isnan(vwap): vwap = float(row["close"])
                    
                    ema20 = float(row["ema20"])
                    if np.isnan(ema20): ema20 = float(row["close"])
                    
                    cond = (float(row["close"]) > vwap) and (float(row["close"]) > ema20)

                    if vol_factor is not None:
                        # volume confirmation against *current* vol_ma (already rolling)
                        vma = float(row["vol_ma"]) if not np.isnan(row["vol_ma"]) else 0.0
                        if vma > 0:
                            cond = cond and (float(row["volume"]) >= vma * float(vol_factor))
                        else:
                            cond = False

                    if cond:
                        reclaim_count += 1
                        stats["reclaims"] += 1
                    else:
                        reclaim_count = 0

                    # entry trigger after consecutive holds
                    if reclaim_count >= hold_bars:
                        # entry at next bar open
                        if idx + 1 >= len(day_df):
                            continue

                        entry_row = day_df.iloc[idx + 1]
                        entry_price = float(entry_row["open"])
                        entry_time = entry_row["ts"]
                        entry_idx = idx + 1

                        # stop based on pullback low
                        stop_price = pb_low_price * (1.0 - stop_buffer)

                        exit_type, exit_price, exit_time, realized_pnl, mfe_pct, mae_pct = simulate_trade(
                            day_df=day_df,
                            entry_idx=entry_idx,
                            entry_price=entry_price,
                            stop_price=stop_price,
                            tp_pct=tp_pct,
                            trail_trigger_1=trail_trigger_1,
                            trail_stop_1=trail_stop_1,
                            trail_trigger_2=trail_trigger_2,
                            trail_stop_2=trail_stop_2,
                        )

                        # entry vs break_high proximity (diagnostic)
                        if break_high > 0:
                            entry_vs_break_high = (entry_price / break_high - 1.0) * 100.0
                        else:
                            entry_vs_break_high = 0

                        trades.append({
                            "date": date,
                            "symbol": sym,
                            "entry_time": entry_time,
                            "entry_price": entry_price,
                            "exit_time": exit_time,
                            "exit_price": exit_price,
                            "exit_type": exit_type,
                            "realized_pnl": realized_pnl,
                            "mfe_pct": mfe_pct,
                            "mae_pct": mae_pct,
                            "break_high": break_high,
                            "pb_low": pb_low_price,
                            "stop_price": stop_price,
                            "entry_vs_break_high_pct": entry_vs_break_high,
                            "no_breakout_before": no_breakout_before.strftime("%H:%M"),
                            "pb_depth": pb_depth,
                            "hold_bars": hold_bars,
                            "vol_factor": vol_factor if vol_factor is not None else "",
                        })

                        stats["entries"] += 1
                        traded_today = True
                        break

    trades_df = pd.DataFrame(trades)
    return trades_df, stats


def summarize_result(tag, trades_df, stats):
    if trades_df.empty:
        return {
            "tag": tag,
            "trades": 0,
            "stop_rate": np.nan,
            "tp_rate": np.nan,
            "trail_rate": np.nan,
            "eod_rate": np.nan,
            "avg_pnl": np.nan,
            "win_rate": np.nan,
            "median_pnl": np.nan,
            "avg_entry_vs_break_high_pct": np.nan,
            **{f"stat_{k}": v for k, v in stats.items()},
        }

    stop_rate = (trades_df["exit_type"] == "STOP").mean() * 100.0
    tp_rate = (trades_df["exit_type"] == "TP").mean() * 100.0
    trail_rate = (trades_df["exit_type"] == "TRAIL").mean() * 100.0
    eod_rate = (trades_df["exit_type"] == "EOD").mean() * 100.0

    avg_pnl = trades_df["realized_pnl"].mean()
    median_pnl = trades_df["realized_pnl"].median()
    win_rate = (trades_df["realized_pnl"] > 0).mean() * 100.0

    avg_entry_vs_break_high = trades_df["entry_vs_break_high_pct"].mean()

    return {
        "tag": tag,
        "trades": len(trades_df),
        "stop_rate": stop_rate,
        "tp_rate": tp_rate,
        "trail_rate": trail_rate,
        "eod_rate": eod_rate,
        "avg_pnl": avg_pnl,
        "median_pnl": median_pnl,
        "win_rate": win_rate,
        "avg_entry_vs_break_high_pct": avg_entry_vs_break_high,
        **{f"stat_{k}": v for k, v in stats.items()},
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--grid", type=str, default="small", choices=["small", "large"])
    parser.add_argument("--data_dir", type=str, default="GARAM_Data/60day_replay_kst")
    args = parser.parse_args()
    
    print("=" * 80)
    print(f"PHASE X-5c: BPC-VWAP RECLAIM GRID ({args.grid.upper()})")
    print("=" * 80)

    data_cache = load_all_data(args.data_dir)

    # collect unique dates
    all_dates = set()
    for _, df in data_cache.items():
        all_dates.update(df["date"].unique())
    dates = sorted(list(all_dates))
    print(f"Total unique dates: {len(dates)}")

    # =========================
    # GRID SETTINGS
    # =========================
    
    if args.grid == "small":
        time_filters = [dtime(13, 0), dtime(13, 30), dtime(14, 0)]
        pb_depths = [0.015, 0.020, 0.025]  # 1.5%, 2.0%, 2.5%
        vol_factors = [1.10]
    else: # large
        time_filters = [dtime(12, 0), dtime(13, 0), dtime(13, 30), dtime(14, 0)]
        pb_depths = [0.012, 0.015, 0.020, 0.025]
        vol_factors = [1.00, 1.10, 1.20]

    # reclaim confirmation
    hold_bars = 2
    
    base_params = {
        "vol_mult": 2.0,
        "lookback": 30,
        "vol_ma_period": 20,
        "high_update_window": 10,
        "max_wait_bars": 60,
        "stop_buffer": 0.002,   # pb_low below 0.2% buffer

        "tp_pct": 5.0,
        "trail_trigger_1": 2.0, "trail_stop_1": 1.0,
        "trail_trigger_2": 3.0, "trail_stop_2": 1.2,
    }

    out_rows = []
    os.makedirs("GARAM_Data/phase_x5c_trades", exist_ok=True)
    
    total_combinations = len(time_filters) * len(pb_depths) * len(vol_factors)
    print(f"Running {total_combinations} combinations...")

    for tf in time_filters:
        for pb in pb_depths:
            for vf in vol_factors:
                tag = f"tf{tf.strftime('%H%M')}_pb{int(pb*1000):03d}_hold{hold_bars}_vf{int(vf*100):03d}"
                params = dict(base_params)
                params.update({
                    "no_breakout_before": tf,
                    "pb_depth": pb,
                    "hold_bars": hold_bars,
                    "vol_factor": vf,
                })

                print(f"\n--- RUN {tag} ---")
                trades_df, stats = run_x5c_for_params(data_cache, dates, params)

                # save trades
                if not trades_df.empty:
                    trades_path = f"GARAM_Data/phase_x5c_trades/{tag}_trades.csv"
                    trades_df.to_csv(trades_path, index=False)
                    # print(f"Saved trades: {trades_path}  (n={len(trades_df)})")

                row = summarize_result(tag, trades_df, stats)
                out_rows.append(row)

                # quick console summary
                print(f"Trades={row['trades']}, Stop={row['stop_rate']:.1f}%, TP={row['tp_rate']:.1f}%, "
                      f"Trail={row['trail_rate']:.1f}%, AvgPnL={row['avg_pnl']:+.3f}%, Win={row['win_rate']:.1f}%")
                # print(f"Avg Entry vs BreakHigh: {row['avg_entry_vs_break_high_pct']:+.3f}%")

    summary_df = pd.DataFrame(out_rows)
    summary_path = "GARAM_Data/phase_x5c_grid_summary.csv"
    summary_df.to_csv(summary_path, index=False)
    print("\n" + "=" * 80)
    print("GRID SUMMARY SAVED:", summary_path)
    print("=" * 80)

    # rank by avg_pnl then stop_rate (lower is better)
    if not summary_df.empty:
        ranked = summary_df.sort_values(by=["avg_pnl", "stop_rate"], ascending=[False, True])
        print("\nTOP 5 by AvgPnL desc, StopRate asc")
        print(ranked[["tag", "trades", "stop_rate", "tp_rate", "trail_rate", "avg_pnl", "win_rate"]].head(5).to_string(index=False))


if __name__ == "__main__":
    main()
