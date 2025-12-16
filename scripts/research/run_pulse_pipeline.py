# scripts/research/run_pulse_pipeline.py
import sys
import argparse
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt

# Setup path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT))

from garam_core.research.pulse.load_data import load_minute_data, enhance_features
from garam_core.research.pulse.pulse_stat import detect_pulses, pulse_stats
from garam_core.research.pulse.pulse_ev import compute_ev
from garam_core.research.pulse.regime import get_regime
from garam_core.research.pulse.label_gen import generate_labels
from garam_core.research.pulse.features_ml import make_feature_matrix
from garam_core.research.pulse.train_ml import train_ml_model
from garam_core.research.pulse.backtest_integrated import backtest_ml_pulse

def run_pipeline(symbol: str, data_dir: str):
    print(f"--- [STEP 1] Loading Data for {symbol} ---")
    try:
        df = load_minute_data(symbol, data_dir)
        df = enhance_features(df)
        print(f"Loaded {len(df)} bars. Range: {df.index[0]} ~ {df.index[-1]}")
    except Exception as e:
        print(f"Data Load Error: {e}")
        return

    print(f"\n--- [STEP 2] Pulse Stats & Pattern Detection ---")
    df = detect_pulses(df)
    stats = pulse_stats(df)
    print("Pulse Stats (Rule-Based):")
    for k, v in stats.items():
        print(f"  {k}: {v}")

    print(f"\n--- [STEP 3] EV & Cost Analysis ---")
    # Cost 0.31% roundtrip
    ev, win_rate = compute_ev(df, cost_per_trade=0.0031)
    print(f"Rule-Based Pulse EV (Net): {ev:.6f}")
    print(f"Rule-Based Pulse WinRate (Net): {win_rate:.4f}")
    
    if ev <= 0:
        print("Warning: Rule-Based Logic has Negative EV after costs.")
    
    print(f"\n--- [STEP 4] ML Model Training ---")
    # Generate Labels
    df = generate_labels(df, n_out=5, threshold=0.001)
    
    # Feature Matrix
    X = make_feature_matrix(df)
    y = df["label"]
    
    # Train
    model = train_ml_model(X, y)
    
    print(f"\n--- [STEP 5] ML Integrated Backtest ---")
    # Add regime info (optional usage, but good to have)
    df = get_regime(df)
    
    equity = backtest_ml_pulse(df, model, cost_per_trade=0.0031)
    
    final_return = equity.iloc[-1] - 1.0
    print(f"ML Strategy Total Net Return: {final_return:.4%}")
    
    # Plot
    try:
        plt.figure(figsize=(10, 6))
        plt.plot(equity, label="ML Pulse Equity (Net)")
        plt.title(f"Pulse Strategy: {symbol}")
        plt.legend()
        plt.grid(True)
        
        out_png = PROJECT_ROOT / "reports" / f"pulse_equity_{symbol}.png"
        out_png.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(out_png)
        print(f"Equity chart saved to {out_png}")
    except Exception as e:
        print(f"Plotting failed: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("symbol", help="Symbol code")
    parser.add_argument("--data_dir", default=str(PROJECT_ROOT/"GARAM_Data/minute/kr"), help="Data directory")
    args = parser.parse_args()
    
    run_pipeline(args.symbol, args.data_dir)
