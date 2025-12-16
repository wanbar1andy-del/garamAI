# scripts/research/backtest_and_plot.py

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parents[2]))

from garam_core.engine.signals_short_term import signal_mean_reversion, signal_breakout, signal_fear_contrarian

def compute_equity(df, sig_col):
    """
    간단한 백테스트: Long/Short 진입 후 1봉만 유지 (1-bar horizon assumption per prompt?)
    Or just standard signal backtest?
    Prompt says: "Long/Short 진입 후 1봉만 유지".
    """
    equity = [1.0]
    pos = 0
    entry_price = 0

    closes = df["close"].values
    sigs = df[sig_col].values
    
    # Vectorized might be faster but loop is explicit as per prompt
    for i in range(1, len(df)):
        # Signal from prev bar triggers entry at current bar OPEN (or CLOSE?)
        # Prompt logic: 
        # if df[sig_col][i-1] == +1 and pos == 0: pos=1, entry=close[i]
        # This implies entry at CLOSE of bar i based on signal at i-1.
        # And holding for? "1봉만 유지"?
        # Actually prompt loop logic:
        #  if pos != 0: calculation... pos=0.
        # This means we exit at the VERY NEXT bar after entry.
        # i-1 signal -> i Entry -> i+1 Exit. 
        # Let's trace loop:
        # i=1: sig[0]=1. pos=0 -> pos=1, entry=close[1].
        # i=2: pos!=0. ret = (close[2]-entry)/entry. exit. pos=0.
        # Yes, 1-bar holding period.
        
        s = sigs[i-1]
        c = closes[i]
        
        if pos != 0:
            # Exit first
            ret = (c - entry_price) / entry_price * pos
            # Transaction cost? User prompt simplistic.
            equity.append(equity[-1] * (1 + ret))
            pos = 0
            entry_price = 0
            # Can we re-enter same bar? No, simplistic.
        else:
            # Check entry
            if s == 1:
                pos = 1
                entry_price = c
                equity.append(equity[-1])
            elif s == -1:
                pos = -1
                entry_price = c
                equity.append(equity[-1])
            else:
                equity.append(equity[-1])

    return pd.Series(equity, index=df.index[: len(equity)])

def run_tests(csv_path):
    print(f"Loading {csv_path}...")
    try:
        df = pd.read_csv(csv_path, parse_dates=True, index_col=0)
        # Normalize index if needed
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"])
            df = df.set_index("date")
    except Exception as e:
        print(f"Error loading csv: {e}")
        return

    print("Generating Signals...")
    df["sig_MR"] = signal_mean_reversion(df)
    df["sig_BO"] = signal_breakout(df)
    
    # fear_score check
    if "fear_score" not in df.columns:
        print("Warning: 'fear_score' column missing. Using default 0.5.")
        df["fear_score"] = 0.5
        
    df["sig_Fear"] = signal_fear_contrarian(df, df["fear_score"])

    print("Computing Equity...")
    df["eq_MR"] = compute_equity(df, "sig_MR")
    df["eq_BO"] = compute_equity(df, "sig_BO")
    df["eq_Fear"] = compute_equity(df, "sig_Fear")

    # 플롯
    print("Plotting...")
    plt.figure(figsize=(14, 10))

    # 1. Price
    plt.subplot(411)
    plt.plot(df["close"], label="Price", color="black", alpha=0.6)
    plt.title("Price Action")
    plt.legend()
    plt.grid(True, alpha=0.3)

    # 2. Equity
    plt.subplot(412)
    plt.plot(df["eq_MR"], label="Mean Reversion")
    plt.plot(df["eq_BO"], label="Breakout")
    plt.plot(df["eq_Fear"], label="Fear Contrarian")
    plt.title("Strategy Equity Curves (1-Bar Hold)")
    plt.legend()
    plt.grid(True, alpha=0.3)

    # 3. Signals (Sparse)
    plt.subplot(413)
    plt.plot(df["sig_MR"], label="MR", alpha=0.5, marker='.', linestyle='None')
    plt.plot(df["sig_BO"], label="BO", alpha=0.5, marker='.', linestyle='None')
    plt.plot(df["sig_Fear"], label="Fear", alpha=0.5, marker='.', linestyle='None')
    plt.yticks([-1, 0, 1], ["Short", "Hold", "Long"])
    plt.title("Signals Triggered")
    plt.legend()
    plt.grid(True, alpha=0.3)

    # 4. Volatility
    plt.subplot(414)
    vol = df["close"].pct_change().rolling(20).std()
    plt.plot(vol, label="20-bar Rolling Vol", color="orange")
    plt.title("Market Volatility")
    plt.legend()
    plt.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python backtest_and_plot.py <csv_path>")
    else:
        run_tests(sys.argv[1])
