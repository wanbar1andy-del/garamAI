# scripts/alpha_tuning_fast.py

import sys, time, argparse
from pathlib import Path
import pandas as pd
import numpy as np
import json

sys.path.append(str(Path(__file__).resolve().parents[1]))

from garam_core.fastlane.feature_store import FeatureStore
from garam_core.fastlane.policy_eval import PolicyEval, PolicyParams
from garam_core.analysis.edge_decomposer import EdgeDecomposer

TOP_10 = ["005930","000660","373220","207940","005380","000270","005490","035420","006400","051910"]

def calc_buckets_from_features(fs: FeatureStore, symbols: list):
    stats = []
    for sym in symbols:
        df = fs.get_features(sym)
        if df is None: continue
        stats.append({"symbol": sym, "vol": df["vol_20"].median()})
    if not stats: return {}
    dfv = pd.DataFrame(stats).sort_values("vol")
    lc = dfv["vol"].quantile(0.33); hc = dfv["vol"].quantile(0.66)
    def b(v): return "Low" if v<=lc else ("Mid" if v<=hc else "High")
    dfv["bucket"] = dfv["vol"].apply(b)
    return dfv.set_index("symbol")["bucket"].to_dict()

def run_grid(mode: str):
    t0 = time.time()
    fs = FeatureStore(cache_dir="cache/features")
    symbols = ["005930", "000660"] if mode == "SMOKE" else TOP_10
    
    print("Warming up features...")
    for s in symbols: 
        fs.get_features(s, force_recompute=True) 

    buckets = calc_buckets_from_features(fs, symbols)

    base = dict(
        abs_momentum_floor=0.002, cost_floor=0.0025,
        max_hold_bars=120, fixed_hold=False,
        use_vol_scaled_cooldown=False, cooldown_bars=30,
        fee=0.00015, slippage=0.0005, tax=0.0020
    )
    
    # Base for V1 (Quick Hold)
    base_v1 = base.copy()
    base_v1["max_hold_bars"] = 40

    # Phase 20 Grid (RSI/BB - Filter OFF + Hold/Stop variants)
    experiments = [
        # 1. Pure Indicators (Filter OFF)
        ("P19_Z_2.0", PolicyParams(strategy_type="MEAN_REVERSION", mr_mode="Z", mr_z_entry=-2.0, mr_z_exit=0.0, use_ma_filter=False, **base)),
        
        ("RSI_30_50", PolicyParams(strategy_type="MEAN_REVERSION", mr_mode="RSI", mr_rsi_entry=30, mr_rsi_exit=50, use_ma_filter=False, **base)),
        ("RSI_25_45", PolicyParams(strategy_type="MEAN_REVERSION", mr_mode="RSI", mr_rsi_entry=25, mr_rsi_exit=45, use_ma_filter=False, **base)),
        
        ("BB_L2_MID", PolicyParams(strategy_type="MEAN_REVERSION", mr_mode="BB", mr_bb_exit_sigma_from_mid=0.0, use_ma_filter=False, **base)),
        ("BB_L2_QUICK", PolicyParams(strategy_type="MEAN_REVERSION", mr_mode="BB", mr_bb_exit_sigma_from_mid=-1.0, use_ma_filter=False, **base)),
        
        # 2. Exit/Stop Optimization (Hold 40, Stop 2%)
        # Note: Using base_v1 to avoid duplicate 'max_hold_bars' kwarg error
        ("BB_MID_EXIT_V1", PolicyParams(strategy_type="MEAN_REVERSION", mr_mode="BB", mr_bb_exit_sigma_from_mid=0.0, use_ma_filter=False, 
                                        mr_stop_loss=0.02, **base_v1)),
                                        
        ("RSI_30_EXIT_V1", PolicyParams(strategy_type="MEAN_REVERSION", mr_mode="RSI", mr_rsi_entry=30, mr_rsi_exit=50, use_ma_filter=False,
                                        mr_stop_loss=0.02, **base_v1)),
    ]

    rows = []
    print(f"\nRunning Phase 20 Re-Run ({mode})...")
    
    for exp_name, params in experiments:
        print(f"  Experiment: {exp_name}")
        for sym in symbols:
            df = fs.get_features(sym)
            if df is None: continue
            
            pe = PolicyEval(df)
            res = pe.evaluate(params)
            
            # Phase 19/20: Edge Decomposer (SSOT)
            edge = EdgeDecomposer.analyze_trades(res.get("trades_detail", []), timeframe_seconds=60)
            
            rows.append({
                "experiment": exp_name,
                "symbol": sym,
                "bucket": buckets.get(sym, "Unknown"),
                "exp_net": edge.get("expectancy_net", 0.0),
                "win_rate": edge.get("win_rate", 0.0),
                "tail": edge.get("loss_tail_ratio", 0.0),
                "trades": res["trades"]
            })

    df_res = pd.DataFrame(rows)
    print("\n[Hynix 000660 Results]")
    hynix = df_res[df_res["symbol"] == "000660"]
    print(hynix[["experiment", "exp_net", "win_rate", "tail", "trades"]].to_string(index=False))

    # Winner Logic for Hynix
    if not hynix.empty:
        winner = hynix.sort_values("exp_net", ascending=False).iloc[0]
        print(f"\nProvisional Winner: {winner['experiment']} (Exp={winner['exp_net']:.5f})")
    
    # Save
    out = Path(__file__).resolve().parents[1].parent / "results" / f"alpha_tuning_phase20_{mode}.csv"
    df_res.to_csv(out, index=False)
    print(f"Saved to {out}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", default="SMOKE", choices=["SMOKE","SCREEN","FULL"])
    args = ap.parse_args()
    run_grid(args.mode)
