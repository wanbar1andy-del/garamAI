import pandas as pd
import numpy as np
from pathlib import Path
import json

def main():
    if not Path("edge_map_overall_400.csv").exists():
        print("CSV not found: edge_map_overall_400.csv")
        return

    # Load overall EdgeMap
    df_overall = pd.read_csv("edge_map_overall_400.csv")

    # 1) Tier-0 Guard: min_edge_th
    # Using lower quantile of net_expectancy distribution
    net_dist = df_overall["net_expectancy"].dropna()
    min_edge_th = float(net_dist.quantile(0.10))  # 10th percentile

    # 2) crash_mdd guard
    mdd_dist = df_overall["mdd"].dropna()
    crash_mdd_th = float(mdd_dist.quantile(0.05))  # bottom 5%

    # 3) trades_per_day guard
    tpd_dist = df_overall["trades_per_day"].dropna()
    overtrade_th = float(tpd_dist.quantile(0.90))  # top 10% threshold

    # 4) signal_noise_win_rate guard
    win_rate_dist = df_overall["win_rate"].dropna()
    signal_noise_wr = float(win_rate_dist.quantile(0.10))  # low 10%

    # 5) regime_spread_exp_net threshold
    # Use across by-regime dispersion (mean stdev)
    if Path("edge_map_by_regime_400.csv").exists():
        df_regime = pd.read_csv("edge_map_by_regime_400.csv")
        spread_disp = (
            df_regime.groupby("symbol")["net_expectancy"]
            .agg(lambda s: s.std() if len(s)>=2 else 0.0)
        )
        regime_spread_th = float(spread_disp.quantile(0.75))  # 75% percentile
    else:
        regime_spread_th = 0.0015 # Default fallback

    # Report recommendations
    params = {
        "guard_min_threshold": min_edge_th,
        "crash_mdd": crash_mdd_th,
        "overtrade_trades_per_day": overtrade_th,
        "signal_noise_win_rate": signal_noise_wr,
        "regime_spread_exp_net": regime_spread_th
    }

    print("=== Guard Parameter Recommendations ===")
    for k,v in params.items():
        print(f"{k}: {v:.6f}")

    # Save to JSON
    out_path = Path("guard_param_recommended.json")
    out_path.write_text(json.dumps(params, indent=2))
    print(f"Recommendation saved to {out_path.absolute()}")
    
    # Also save to config for persistence if needed
    Path("config/guard_param_generated.json").write_text(json.dumps(params, indent=2))

if __name__ == "__main__":
    main()
