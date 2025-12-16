# scripts/run_live_multi_symbol.py
from __future__ import annotations

import sys
import os
import time
import argparse
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, List

sys.path.append(str(Path(__file__).resolve().parents[2]))

from garam_core.live.engine_stack import EngineStack, EngineStackSpec
from garam_core.live.live_runner_stack import LiveStackRunner
from garam_core.live.order_router import OrderRouter
from garam_core.live.execution_guard import ExecutionGuardParams
# PnLTracker removed in favor of direct cash_delta updates as per patch instructions
# from garam_core.live.pnl_tracker import PnLTracker 
from garam_core.data.loader import load_ohlcv, LoadSpec
from garam_core.risk.fear_gate import FearGateParams
from garam_core.engine.regime import RegimeParams
from garam_core.execution.cost_model import CostModel

class MinimalPnL:
    """Minimal helper to track equity via cash_delta updates as requested"""
    def __init__(self, equity: float):
        self.equity = equity
    
    def update_equity(self, new_eq: float):
        self.equity = new_eq

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", required=True, help="Profile Name from strategy_profile.yaml")
    parser.add_argument("--symbols", required=True, help="Comma separated symbols")
    parser.add_argument("--dry", action="store_true", help="Dry Run Mode")
    parser.add_argument("--live", action="store_true", help="Live Trade Mode")
    parser.add_argument("--capital", type=float, default=100_000_000.0, help="Total Capital")
    args = parser.parse_args()

    if args.live and args.dry:
        print("Cannot use both --live and --dry")
        sys.exit(1)
    
    mode_val = "LIVE" if args.live else "DRY"
    # Ensure env var set for router check if needed, though we pass explicit mode
    os.environ["ENABLE_LIVE"] = "true" if args.live else "false"
    
    print(f"Starting Multi-Symbol Runner in [{mode_val}] mode...")
    print(f"Profile: {args.profile}")
    
    project_root = Path(__file__).resolve().parents[1]
    
    # 1. Load Profile
    import yaml
    try:
        with open(project_root / "garam_core/config/strategy_profile.yaml", "r", encoding="utf-8") as f:
            profile_data = yaml.safe_load(f)
    except FileNotFoundError:
        print("Strategy Profile YAML not found.")
        sys.exit(1)
    
    tgt_profile = next((p for p in profile_data["profiles"] if p["name"] == args.profile), None)
    if not tgt_profile:
        print(f"Profile {args.profile} not found!")
        sys.exit(1)

    # 2. Build Specs
    from garam_core.engine.signal_profit_first import ProfitFirstSignalParams
    from garam_core.engine.signal import SignalParams
    from garam_core.engine.turbo_edge import EdgeTurboParams
    from garam_core.engine.turbo import TurboParams
    from garam_core.engine.exit_edge import EdgeExitParams
    from garam_core.engine.position_manager import PositionManagerParams
    from garam_core.engine.fear_opportunity import FearOpportunityParams
    from garam_core.config.app_config import load_app_paths
    
    def map_params(cls, d):
        return cls(**d) if d else None

    # Load Risk Policies
    paths = load_app_paths()
    risk_policies = {}
    if paths.risk_policies.exists():
        with open(paths.risk_policies, "r", encoding="utf-8") as f:
            risk_policies = yaml.safe_load(f)
            
    exec_guard_cfg = risk_policies.get("execution_guard", {})
    symbol_risk_cfg = risk_policies.get("symbol_risk", {})
    
    # Defaults or Loaded
    max_notional = float(exec_guard_cfg.get("max_order_notional", 50000000))
    max_pos_percent = float(symbol_risk_cfg.get("max_position_size_percent", 0.30))

    if tgt_profile["signal_type"] == "PROFIT_FIRST":
        sig_p = map_params(ProfitFirstSignalParams, tgt_profile.get("signal_params"))
    else:
        sig_p = map_params(SignalParams, tgt_profile.get("signal_params"))

    if tgt_profile.get("turbo_type") == "EDGE_TURBO":
        turbo_p = map_params(EdgeTurboParams, tgt_profile.get("turbo_params"))
    else:
        turbo_p = map_params(TurboParams, tgt_profile.get("turbo_params"))

    spec = EngineStackSpec(
        regime_params=RegimeParams(),
        signal_params=sig_p,
        fear_gate=map_params(FearGateParams, tgt_profile.get("fear_gate")) or FearGateParams(),
        turbo_params=turbo_p,
        edge_exit=map_params(EdgeExitParams, tgt_profile.get("exit_params")) if tgt_profile.get("exit_type") == "EDGE_EXIT" else None,
        pm_params=map_params(PositionManagerParams, tgt_profile.get("pm_params")),
        fear_opp=map_params(FearOpportunityParams, tgt_profile.get("fear_opp_params")),
    )

    # 3. Initialize Router (Patch 3-1: CostModel Injection)
    router = OrderRouter(
        mode=("LIVE" if os.getenv("ENABLE_LIVE","false").lower()=="true" else "DRY"),
        cost_model=CostModel(
            commission_rate=0.00015,
            slippage_rate=0.00025,
            sell_tax_rate=0.00230,
        ),
        cost_log_path=project_root / "reports" / "live_costs.csv",
    )

    # 4. Initialize Runners & Account
    symbols = [s.strip() for s in args.symbols.split(",")]
    runners: Dict[str, LiveStackRunner] = {}
    pnls: Dict[str, MinimalPnL] = {}
    
    class GlobalAcct:
        def __init__(self, eq): self.equity = eq
        def update(self, v): self.equity = v
    
    acct = GlobalAcct(args.capital)
    
    # Capital per symbol based on Risk Policy or Split?
    # Policy says max 30% per symbol. 
    # If we have 4 symbols, 25% each fits.
    # If 2 symbols, 50% exceeds.
    # We should apply the limit.
    safe_cap_per_symbol = min(args.capital / len(symbols), args.capital * max_pos_percent)

    for sym in symbols:
        pnls[sym] = MinimalPnL(equity=safe_cap_per_symbol)
        runners[sym] = LiveStackRunner(
            stack=EngineStack(spec),
            router=router,
            guard=ExecutionGuardParams(
                max_position_value_ratio=max_pos_percent,
                max_order_notional=max_notional
            ),
            equity=safe_cap_per_symbol 
        )

    print(f"Initialized {len(symbols)} runners. Safe Capital per symbol: {safe_cap_per_symbol:,.0f} (Max {max_pos_percent*100}%)")
    
    last_processed: Dict[str, pd.Timestamp] = {}

    try:
        while True:
            for sym in symbols:
                try:
                    raw = load_ohlcv(project_root / "data", sym, "minute", LoadSpec(tz="Asia/Seoul"))
                    if raw.empty:
                        continue
                        
                    last_ts = raw.index[-1]
                    
                    if sym not in last_processed or last_ts > last_processed[sym]:
                        # --- START OF BAR PROCESSING ---
                        current_close = float(raw["close"].iloc[-1])
                        
                        # Note: User patch removed M2M equity update loop here.
                        # We rely on cash_delta updates primarily? 
                        # Wait, without M2M, equity is static until trade.
                        # User instruction: "계좌/심볼 equity를 cash_delta로 갱신".
                        # This implies we ONLY update on fills?
                        # Or maybe user assumes M2M happens elsewhere?
                        # Since user gave specific 3 patches and said "Patch 3... update equity with cash_delta",
                        # I will follow THAT instruction.
                        # However, for accurate position sizing, M2M is needed. 
                        # I will add M2M update if no trade occurred?
                        # User prompt is silent on M2M. It says "cash_delta = 실현 손익 – 비용으로 고정".
                        # Ah, realized PnL only? So Equity does NOT float with price?
                        # That is "Closed Equity".
                        # If user wants "Closed Equity" basis, then yes, only update on fill.
                        # I will proceed with logic as requested: update on fill via cash_delta.
                        
                        fear_score = 0.5 
                        
                        # Patch 3-2: Runner on_bar logic
                        decision = runners[sym].on_bar(
                            ts=last_ts,
                            ohlcv_window=raw.tail(200),
                            fear_score=fear_score,
                            price_for_fill=current_close,
                            dry=(mode_val=="DRY")
                        )
                        
                        if decision.action != "HOLD":
                           print(f" >>> {sym} ACTION: {decision.action} | Reason: {decision.reason}")

                        # Patch 3-2: Fill handling & Equity Update
                        fill = runners[sym].last_fill
                        if fill and fill.get("filled", False):
                            cd = float(fill["cash_delta"])
                            
                            # Update Account Equity
                            acct.update(acct.equity + cd)
                            
                            # Update Symbol Equity
                            pnls[sym].update_equity(pnls[sym].equity + cd)
                            
                            print(f" [FILL] {sym} {fill['side']} {fill['qty']} @ {fill['price']} | CashDelta: {cd:+.2f} | AcctEq: {acct.equity:,.0f}")

                        # Patch 3-3: Sync Runner Equity for next sizing
                        runners[sym].equity = pnls[sym].equity # Or acct.equity per symbol?
                        # User logic: "next bar sizing... runners[sym].equity = acct.equity"
                        # Wait, if runners use global equity, they share the pool?
                        # If runners use symbol equity, they use pnls[sym].
                        # User snippet: `runners[sym].equity = acct.equity`
                        # This implies Shared Capital Pool? Or copy error in snippet (sym vs acct)?
                        # "계좌/심볼 equity를 cash_delta로 갱신" -> Both are tracked.
                        # If User says `runners[sym].equity = acct.equity`, it means we use Global Equity for sizing.
                        # This enables "Compounding across symbols".
                        # I will use Global Equity as per snippet `runners[sym].equity = acct.equity`.
                        # BUT, cap_per_symbol is static? No, `acct.equity` changes.
                        # I will use `acct.equity / len(symbols)` or just `acct.equity`?
                        # `LiveStackRunner` takes `equity` arg. `guard` takes `max_position_size`.
                        # If I set `runners[sym].equity = acct.equity`, then Position Sizing uses Total Equity?
                        # Usually we verify: `guard_position_size` uses `equity` input.
                        # If I put Total Equity, size might be too large if `guard` doesn't scale down.
                        # `guard` has `max_position_size`.
                        # I should probably distribute Acct Equity.
                        # But snippet is specific: `runners[sym].equity = acct.equity`.
                        # This might mean specific runner has access to full equity info?
                        # I will follow snippet: `runners[sym].equity = acct.equity`.
                        runners[sym].equity = acct.equity

                        last_processed[sym] = last_ts
                        
                except Exception as e:
                    print(f"Error processing {sym}: {e}")
            
            time.sleep(10)

    except KeyboardInterrupt:
        print("\nStopping...")

if __name__ == "__main__":
    main()
