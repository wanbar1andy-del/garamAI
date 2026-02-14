
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

def calc_mdd(series):
    peak = series.cummax()
    dd = (series - peak) / peak
    return dd.min()

def analyze(suffix, label):
    eq_file = Path(f"logs/phase4_sweep/equity_{suffix}.csv")
    tr_file = Path(f"logs/phase4_sweep/trades_{suffix}.csv")
    
    if not eq_file.exists():
        print(f"File not found: {eq_file}")
        return None, None

    df = pd.read_csv(eq_file)
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)
    
    final_eq = df['equity'].iloc[-1]
    ret = (final_eq - 100_000_000) / 100_000_000 * 100
    mdd = calc_mdd(df['equity']) * 100
    
    trades = pd.DataFrame()
    win_rate = 0
    if tr_file.exists():
        trades = pd.read_csv(tr_file)
        if not trades.empty:
            closes = trades[trades['side'] == 'SELL']
            if not closes.empty:
                wins = closes[closes['pnl'] > 0]
                win_rate = len(wins) / len(closes) * 100
    
    return df['equity'], {'label': label, 'return': ret, 'mdd': mdd, 'win_rate': win_rate, 'trades': len(trades)}

def main():
    s1 = "PYRAMID_0.7_AESTHETIC"
    s2 = "PYRAMID_0.7_AESTHETIC_INTELLIGENT"
    
    eq1, stats1 = analyze(s1, "Aesthetic (Baseline)")
    eq2, stats2 = analyze(s2, "Intelligent (Phase 6)")
    
    if eq1 is None or eq2 is None:
        print("Missing data.")
        return

    # Plot
    plt.figure(figsize=(10, 6))
    plt.plot(eq1, label=f"Baseline (Ret: {stats1['return']:.1f}%)")
    plt.plot(eq2, label=f"Intelligent (Ret: {stats2['return']:.1f}%)", linestyle='--')
    plt.title("Phase 6: Aesthetic vs Intelligent Filter")
    plt.legend()
    plt.grid(True)
    plt.savefig("logs/phase4_sweep/compare_phase6.png")
    
    print("## Comparison Report")
    print("| Metric | Baseline | Intelligent |")
    print("| :--- | :--- | :--- |")
    print(f"| Return | {stats1['return']:.2f}% | {stats2['return']:.2f}% |")
    print(f"| MDD | {stats1['mdd']:.2f}% | {stats2['mdd']:.2f}% |")
    print(f"| Win Rate | {stats1['win_rate']:.1f}% | {stats2['win_rate']:.1f}% |")
    print(f"| Trades | {stats1['trades']} | {stats2['trades']} |")

if __name__ == "__main__":
    main()
