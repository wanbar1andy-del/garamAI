#!/usr/bin/env python
"""
Phase 7: Golden Balance Sweep Driver
Runs penalty multiplier sweep to find optimal filter intensity.
"""
import subprocess
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

PROJECT_ROOT = Path("C:/garam/garam")
OUT_DIR = PROJECT_ROOT / "logs/phase4_sweep"
MULTIPLIERS = [0.2, 0.4, 0.5, 0.6, 0.8, 1.0]

def calc_mdd(series):
    peak = series.cummax()
    dd = (series - peak) / peak
    return dd.min()

def run_sweep():
    print("=== Phase 7: Golden Balance Sweep ===")
    print(f"Testing Penalty Multipliers: {MULTIPLIERS}")
    
    results = []
    
    for pm in MULTIPLIERS:
        print(f"\n[Sweep] Running PM={pm:.1f}...")
        cmd = [
            "python", "scripts/strategies/simulate_phase4_hero.py",
            "--mode", "PYRAMID",
            "--weight", "0.7",
            "--aesthetic",
            "--penalty_multiplier", str(pm)
        ]
        
        subprocess.run(cmd, cwd=PROJECT_ROOT, check=True)
        
        # Analyze results
        suffix = f"PYRAMID_0.7_AESTHETIC_INTELLIGENT_PM{pm:.1f}"
        eq_file = OUT_DIR / f"equity_{suffix}.csv"
        tr_file = OUT_DIR / f"trades_{suffix}.csv"
        
        if not eq_file.exists():
            print(f"[ERROR] Missing: {eq_file}")
            continue
            
        df = pd.read_csv(eq_file)
        df['date'] = pd.to_datetime(df['date'])
        
        final_eq = df['equity'].iloc[-1]
        ret = (final_eq - 100_000_000) / 100_000_000 * 100
        mdd = calc_mdd(df['equity']) * 100
        mar = ret / abs(mdd) if mdd != 0 else 0
        
        trades = pd.read_csv(tr_file) if tr_file.exists() else pd.DataFrame()
        closes = trades[trades['side'] == 'SELL'] if not trades.empty else pd.DataFrame()
        win_rate = (closes['pnl'] > 0).mean() * 100 if not closes.empty else 0
        
        results.append({
            'penalty_multiplier': pm,
            'return': ret,
            'mdd': mdd,
            'mar_ratio': mar,
            'win_rate': win_rate,
            'trades': len(trades)
        })
        
        print(f"  Return: {ret:.2f}% | MDD: {mdd:.2f}% | MAR: {mar:.2f} | WR: {win_rate:.1f}%")
    
    # Save results
    results_df = pd.DataFrame(results)
    results_df.to_csv(OUT_DIR / "Phase7_Sweep_Results.csv", index=False)
    
    # Find Golden Configuration
    # Target: Return > 5%, MDD > -7%, maximize MAR
    valid = results_df[(results_df['return'] > 5) & (results_df['mdd'] > -7)]
    
    if valid.empty:
        print("\n[WARNING] No configuration meets target (Ret > 5%, MDD > -7%)")
        print("Selecting configuration with best MAR ratio:")
        best = results_df.loc[results_df['mar_ratio'].idxmax()]
    else:
        print(f"\n[SUCCESS] {len(valid)} configurations meet target criteria")
        best = valid.loc[valid['mar_ratio'].idxmax()]
    
    print("\n=== GOLDEN CONFIGURATION ===")
    print(f"Penalty Multiplier: {best['penalty_multiplier']:.1f}")
    print(f"Return: {best['return']:.2f}%")
    print(f"MDD: {best['mdd']:.2f}%")
    print(f"MAR Ratio: {best['mar_ratio']:.2f}")
    print(f"Win Rate: {best['win_rate']:.1f}%")
    
    # Generate comparison plot
    plot_comparison(best['penalty_multiplier'], results_df)
    
    return best

def plot_comparison(best_pm, results_df):
    """Generate multi-panel comparison plot"""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # Panel 1: Return vs PM
    ax = axes[0, 0]
    ax.plot(results_df['penalty_multiplier'], results_df['return'], 'o-', linewidth=2, markersize=8)
    ax.axhline(5, color='green', linestyle='--', alpha=0.5, label='Target (5%)')
    ax.axvline(best_pm, color='red', linestyle='--', alpha=0.5, label=f'Golden ({best_pm:.1f})')
    ax.set_xlabel('Penalty Multiplier')
    ax.set_ylabel('Return (%)')
    ax.set_title('Return vs Filter Intensity')
    ax.grid(True, alpha=0.3)
    ax.legend()
    
    # Panel 2: MDD vs PM
    ax = axes[0, 1]
    ax.plot(results_df['penalty_multiplier'], results_df['mdd'], 'o-', linewidth=2, markersize=8, color='orange')
    ax.axhline(-7, color='green', linestyle='--', alpha=0.5, label='Target (-7%)')
    ax.axvline(best_pm, color='red', linestyle='--', alpha=0.5, label=f'Golden ({best_pm:.1f})')
    ax.set_xlabel('Penalty Multiplier')
    ax.set_ylabel('Max Drawdown (%)')
    ax.set_title('Risk vs Filter Intensity')
    ax.grid(True, alpha=0.3)
    ax.legend()
    
    # Panel 3: MAR Ratio vs PM
    ax = axes[1, 0]
    ax.plot(results_df['penalty_multiplier'], results_df['mar_ratio'], 'o-', linewidth=2, markersize=8, color='purple')
    ax.axvline(best_pm, color='red', linestyle='--', alpha=0.5, label=f'Golden ({best_pm:.1f})')
    ax.set_xlabel('Penalty Multiplier')
    ax.set_ylabel('MAR Ratio (Return/|MDD|)')
    ax.set_title('Risk-Adjusted Return vs Filter Intensity')
    ax.grid(True, alpha=0.3)
    ax.legend()
    
    # Panel 4: Win Rate vs PM
    ax = axes[1, 1]
    ax.plot(results_df['penalty_multiplier'], results_df['win_rate'], 'o-', linewidth=2, markersize=8, color='green')
    ax.axvline(best_pm, color='red', linestyle='--', alpha=0.5, label=f'Golden ({best_pm:.1f})')
    ax.set_xlabel('Penalty Multiplier')
    ax.set_ylabel('Win Rate (%)')
    ax.set_title('Quality vs Filter Intensity')
    ax.grid(True, alpha=0.3)
    ax.legend()
    
    plt.tight_layout()
    plt.savefig(OUT_DIR / "Phase7_Golden_Balance.png", dpi=150)
    print(f"\n[Saved] {OUT_DIR / 'Phase7_Golden_Balance.png'}")

if __name__ == "__main__":
    best = run_sweep()
    print("\n=== Phase 7 Complete ===")
