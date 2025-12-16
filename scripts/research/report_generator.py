# scripts/research/report_generator.py

import pandas as pd
import sys
from pathlib import Path
import backtest_and_plot as btp # Imports sibling in same folder? 
# Need to make sure import works. If both in scripts/research, simple import works.
# Or sys.path modification in previous script handles project root.
# For importing btp, we might need it to be importable.

def summarize_equity(eq: pd.Series):
    if len(eq) == 0: return 0,0,0,0,0
    
    total_ret = eq.iloc[-1] - 1.0
    # Annualized: Assume minute data? 252 days * 390 bars = 98280 bars/yr?
    # User prompt used "252" for annualization constant.
    # If data is daily, 252 is correct. If minute, it should be much higher.
    # Prompt says "n=5분 기준", so likely intraday.
    # But uses "(eq.iloc[-1]) ** (252 / len(eq)) - 1". This implies "len(eq)" is "days" count or similar?
    # If len(eq) is minutes (e.g. 100,000), then (252 / 100000) is tiny.
    # Let's stick to user code logic exactly for "Behavioral Alignment".
    
    # User code:
    # annual_ret = (eq.iloc[-1]) ** (252 / len(eq)) - 1
    # sharpe = eq.pct_change().mean() / eq.pct_change().std() * (252 ** 0.5)
    
    # NOTE: This assumes Daily Data implicitly. If Minute data, metrics will be weird but correct per request.
    
    n = len(eq)
    annual_ret = (eq.iloc[-1]) ** (252 / n) - 1 if eq.iloc[-1] > 0 else -1.0
    
    mdd = (eq / eq.cummax() - 1).min()
    
    pct = eq.pct_change()
    if pct.std() == 0:
        sharpe = 0
    else:
        sharpe = pct.mean() / pct.std() * (252 ** 0.5)
        
    trade_count = eq.diff().abs().gt(0).sum() # Any change in equity implies trade? 
    # Logic in btp: equity holds flat when pos=0. changes when pos!=0.
    # Actually, equity changes every bar if in position?
    # "pos=0 -> pos=1 (or -1) -> hold 1 bar -> exit".
    # Equity changes only on EXIT bar.
    # So counting diff != 0 is counting Exits.
    
    return total_ret, annual_ret, mdd, sharpe, trade_count


def generate_report(csv_path):
    print(f"Analyzing {csv_path}...")
    try:
        df = pd.read_csv(csv_path, parse_dates=True, index_col=0)
        # Type alignment
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"])
            df = df.set_index("date")
    except Exception as e:
        print(f"Error: {e}")
        return

    from garam_core.engine.signals_short_term import signal_mean_reversion, signal_breakout, signal_fear_contrarian

    # Generate
    df["sig_MR"] = signal_mean_reversion(df)
    df["sig_BO"] = signal_breakout(df)
    df["sig_Fear"] = signal_fear_contrarian(df, df["fear_score"] if "fear_score" in df else pd.Series(0.5, index=df.index))

    report = []

    for sig_col, name in [("sig_MR", "MeanReversion"),
                          ("sig_BO", "Breakout"),
                          ("sig_Fear", "FearContra")]:
        eq = btp.compute_equity(df, sig_col)
        total_ret, annual_ret, mdd, sharpe, trade_count = summarize_equity(eq)
        report.append({
            "strategy": name,
            "total_return": round(total_ret, 4),
            "annualized_return": round(annual_ret, 4),
            "max_drawdown": round(mdd, 4),
            "sharpe": round(sharpe, 4),
            "trade_count": int(trade_count)
        })

    out_df = pd.DataFrame(report)
    out_path = Path("reports/strategy_report.csv")
    out_path.parent.mkdir(exist_ok=True, parents=True)
    out_df.to_csv(out_path, index=False)
    
    print("\n=== Strategy Performance Report ===")
    print(out_df.to_string())
    print(f"\nSaved to {out_path}")


if __name__ == "__main__":
    import sys
    sys.path.append(str(Path(__file__).resolve().parents[2])) # Project Root
    if len(sys.argv) < 2:
        print("Usage: python report_generator.py <csv_path>")
    else:
        generate_report(sys.argv[1])
