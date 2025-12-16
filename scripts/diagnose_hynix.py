# scripts/diagnose_hynix.py
import sys
import pandas as pd
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from garam_core.fastlane.feature_store import FeatureStore
from garam_core.fastlane.policy_eval import PolicyEval, PolicyParams
from garam_core.analysis.edge_decomposer import EdgeDecomposer

def run_k_grid_diagnosis():
    print(">>> Phase 18: Hynix K-Grid Diagnosis (Breakout Test) <<<")
    
    fs = FeatureStore(cache_dir="cache/features")
    # Force rebuild cache to ensure correct schema if changed
    # fs.get_features("000660", force_recompute=True) 
    
    symbol = "000660"
    df = fs.get_features(symbol)
    if df is None: return

    pe = PolicyEval(df)
    
    # Params: Strict Cost Model
    # fee=0.015%, slip=0.05% one-way, tax=0.20%
    base_params = dict(
        momentum_n=20, 
        zscore_min=0.0,
        abs_momentum_floor=0.002, 
        cost_floor=0.0025,
        max_hold_bars=120, 
        fee=0.00015, 
        slippage=0.0005, 
        tax=0.0020
    )
    
    K_GRID = [1.0, 2.0, 3.0, 4.0]
    
    results = []
    
    for k in K_GRID:
        params = PolicyParams(min_momentum_k=k, **base_params)
        res = pe.evaluate(params)
        
        edge = EdgeDecomposer.analyze_trades(res["trades_detail"], timeframe_seconds=60)
        
        results.append({
            "K-Val": k,
            "Trades": res["trades"],
            "WinRate": edge["win_rate"],
            "Expectancy": edge["expectancy_net"],
            "TailRatio": edge["loss_tail_ratio"],
            "Return": res["total_return"]
        })
        
    df_res = pd.DataFrame(results)
    print("\n[Hynix K-Grid Comparison]")
    print(df_res.round(5).to_string(index=False))
    
    # Auto-Judge
    best = df_res.sort_values("Expectancy", ascending=False).iloc[0]
    best_exp = best["Expectancy"]
    
    print(f"\n[Diagnosis]")
    if best_exp > 0.0:
         print(f"PASS: Positive Expectancy at K={best['K-Val']} ({best_exp:.5f})")
         print("Conclusion: Hynix requires stronger breakout threshold.")
    else:
         print(f"FAIL: Expectancy still negative. Best: K={best['K-Val']} ({best_exp:.5f})")
         if best['WinRate'] < 0.3:
             print("Conclusion: Momentum Breakout FAILED. Signal is counter-predictive (Mean Reversion).")

if __name__ == "__main__":
    run_k_grid_diagnosis()
