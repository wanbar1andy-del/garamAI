"""
micro_regime_analysis.py

Purpose:
- Tag trades with micro-regimes (e.g., MR_UP_DRIFT, MR_PANIC_DOWN) within R3~R5.
- Calculate performance stats per micro-regime.
- Identify candidates for Champion v3 (Num Trades >= 30, PF > 1.3).
- Lock R1/R2 (Main Regimes) from modification.

Inputs:
- trades_by_regime.csv (from previous step)
- market_daily data (Proxy: 005930 or KOSPI)

Outputs:
- trades_by_regime_micro.csv
- summary_micro_regime.csv
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys
import argparse

# ----------------------------------------------------------------------
# 1. Configuration
# ----------------------------------------------------------------------

LOCKED_MAIN_REGIMES = [
    "R1_STRONG_UP",
    "R2_GRIND_UP",
]

TARGET_MAIN_REGIMES = [
    "R3_CHOP",
    "R4_DOWN",
    "R5_STRONG_DOWN",
]

MIN_TRADES = 30
MIN_PROFIT_FACTOR = 1.3

# ----------------------------------------------------------------------
# 2. Micro Regime Helper
# ----------------------------------------------------------------------

def classify_micro_regime(one_day_ret: float, five_day_ret: float, atr_pct: float) -> str:
    """
    Rule-based micro-regime classification.
    """
    # 1) Direction (5-day)
    if five_day_ret > 0.03:
        direction = "UP"
    elif five_day_ret < -0.03:
        direction = "DOWN"
    else:
        direction = "FLAT"

    # 2) Volatility (ATR%)
    if atr_pct < 0.015:
        vol = "LOWVOL"
    elif atr_pct > 0.03:
        vol = "HIGHVOL"
    else:
        vol = "MIDVOL"

    # 3) Combination
    if direction == "UP" and vol in ("LOWVOL", "MIDVOL"):
        micro = "MR_UP_DRIFT"
    elif direction == "UP" and vol == "HIGHVOL":
        micro = "MR_UP_SPIKE"
    elif direction == "DOWN" and vol == "HIGHVOL":
        micro = "MR_PANIC_DOWN"
    elif direction == "DOWN" and vol != "HIGHVOL":
        micro = "MR_GRIND_DOWN"
    elif direction == "FLAT" and vol == "LOWVOL":
        micro = "MR_FLAT_BOX"
    elif direction == "FLAT" and vol == "HIGHVOL":
        micro = "MR_FLAT_NOISY"
    else:
        micro = "MR_MISC"

    return micro

# ----------------------------------------------------------------------
# 3. Build Daily Map
# ----------------------------------------------------------------------

def build_daily_micro_regime_map(market_daily: pd.DataFrame) -> dict:
    df = market_daily.copy()
    
    # Calculate Features if not present
    if 'ret_1d' not in df.columns:
        df['ret_1d'] = df['close'].pct_change(1)
    if 'ret_5d' not in df.columns:
        df['ret_5d'] = df['close'].pct_change(5)
        
    # ATR Calculation if missing (Simple Proxy)
    if 'atr_pct' not in df.columns:
        df['tr'] = np.maximum(df['high'] - df['low'], 
                              np.maximum(abs(df['high'] - df['close'].shift(1)), 
                                         abs(df['low'] - df['close'].shift(1))))
        df['atr'] = df['tr'].rolling(14).mean()
        df['atr_pct'] = df['atr'] / df['close']
        
    micro_map = {}
    for dt, row in df.iterrows():
        date_str = dt.strftime("%Y-%m-%d")
        # Handle NaN at start
        if pd.isna(row['ret_1d']) or pd.isna(row['ret_5d']) or pd.isna(row['atr_pct']):
            micro_map[date_str] = "MR_UNKNOWN"
            continue
            
        micro = classify_micro_regime(row['ret_1d'], row['ret_5d'], row['atr_pct'])
        micro_map[date_str] = micro
        
    return micro_map

# ----------------------------------------------------------------------
# 4. Tag Trades
# ----------------------------------------------------------------------

def tag_trades_with_micro_regime(trades_path: Path, market_daily: pd.DataFrame, output_path: Path) -> pd.DataFrame:
    trades = pd.read_csv(trades_path)
    trades["entry_time"] = pd.to_datetime(trades["entry_time"])
    trades["exit_time"] = pd.to_datetime(trades["exit_time"])
    trades["entry_date_str"] = trades["entry_time"].dt.strftime("%Y-%m-%d")

    micro_map = build_daily_micro_regime_map(market_daily)
    trades["entry_micro_regime"] = trades["entry_date_str"].map(micro_map).fillna("MR_UNKNOWN")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    trades.to_csv(output_path, index=False)
    print(f"[INFO] trades_with_micro_regime saved to {output_path}")
    return trades

# ----------------------------------------------------------------------
# 5. Compute Stats & Filter
# ----------------------------------------------------------------------

def compute_group_stats(df: pd.DataFrame) -> pd.Series:
    if df.empty:
        return pd.Series({
            "num_trades": 0, "win_rate": 0.0, "total_pnl": 0.0,
            "avg_return": 0.0, "profit_factor": 0.0, "avg_holding_days": 0.0
        })

    wins = df[df["pnl"] > 0]
    losses = df[df["pnl"] <= 0]
    num_trades = len(df)
    win_rate = len(wins) / num_trades if num_trades > 0 else 0.0
    
    gross_profit = wins["pnl"].sum()
    gross_loss = abs(losses["pnl"].sum())
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else np.inf
    
    holding_days = (df["exit_time"] - df["entry_time"]).dt.total_seconds() / 86400.0
    
    return pd.Series({
        "num_trades": num_trades,
        "win_rate": win_rate,
        "total_pnl": df["pnl"].sum(),
        "avg_return": df["return_pct"].mean(),
        "profit_factor": profit_factor,
        "avg_holding_days": holding_days.mean()
    })

def summarize_micro_regimes(trades_with_micro: pd.DataFrame, output_path: Path) -> pd.DataFrame:
    group_cols = ["entry_regime", "entry_micro_regime"]
    grouped = trades_with_micro.groupby(group_cols, dropna=False)
    summary = grouped.apply(compute_group_stats).reset_index()

    summary["meets_min_trades"] = summary["num_trades"] >= MIN_TRADES
    summary["meets_pf"] = summary["profit_factor"] >= MIN_PROFIT_FACTOR
    summary["is_locked_main_regime"] = summary["entry_regime"].isin(LOCKED_MAIN_REGIMES)

    summary["is_candidate"] = (
        summary["entry_regime"].isin(TARGET_MAIN_REGIMES)
        & summary["meets_min_trades"]
        & summary["meets_pf"]
        & (~summary["is_locked_main_regime"])
    )

    summary = summary.sort_values(by=["is_candidate", "profit_factor", "num_trades"], ascending=[False, False, False])
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(output_path, index=False)
    print(f"[INFO] micro-regime summary saved to {output_path}")
    return summary

# ----------------------------------------------------------------------
# 6. Main
# ----------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--trades-file', required=True)
    parser.add_argument('--market-file', required=True) # Proxy CSV
    parser.add_argument('--output-trades', required=True)
    parser.add_argument('--output-summary', required=True)
    args = parser.parse_args()
    
    # Load Market Data (Proxy)
    market_daily = pd.read_csv(args.market_file)
    # Ensure standard columns
    if 'date' in market_daily.columns:
        market_daily['date'] = pd.to_datetime(market_daily['date'])
        market_daily.set_index('date', inplace=True)
    
    # Resample to Daily if minute data
    if len(market_daily) > 1000: # Likely minute data
        market_daily = market_daily.resample('D').agg({'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'}).dropna()
        
    trades_with_micro = tag_trades_with_micro_regime(Path(args.trades_file), market_daily, Path(args.output_trades))
    summary = summarize_micro_regimes(trades_with_micro, Path(args.output_summary))
    
    print("\n[SUMMARY HEAD]")
    print(summary.head(20).to_markdown(index=False, floatfmt=".2f"))

if __name__ == "__main__":
    main()
