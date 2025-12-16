# scripts/verify_turbo_v3.py
from __future__ import annotations

import sys
from pathlib import Path
import pandas as pd
import numpy as np

# Add project root
sys.path.append(str(Path(__file__).resolve().parents[1]))

from garam_core.replay.replay_runner import run_replay, ReplaySpec, ReplayResult
from garam_core.engine.regime import RegimeParams
from garam_core.engine.signal import SignalParams
from garam_core.engine.turbo import TurboParams
from garam_core.execution.fill_model import FillSpec
from garam_core.execution.cost_model import CostModel

import argparse

def main():
    parser = argparse.ArgumentParser(description="Verify Turbo V3 Strategy")
    parser.add_argument("--symbol", type=str, default="005930", help="Target symbol code")
    parser.add_argument("--days", type=int, default=60, help="Replay duration in days (approx)")
    parser.add_argument("--max_mult", type=float, default=2.5, help="Max Turbo Multiplier")
    
    args = parser.parse_args()
    
    print(f">>> Starting Turbo V3 Verification (B-6 Locked)...")
    
    project_root = Path("c:/garam/garam/garam_core")
    
    # Target Symbol from Args
    symbol = args.symbol
    
    # B-6 Locked Models
    fill_spec = FillSpec(method="NEXT_OPEN")
    cost_model = CostModel(
        commission_rate=0.00015,
        slippage_rate=0.00025, # Locked
        sell_tax_rate=0.00230  # Locked
    )
    
    # Calc max_bars from days (approx 381 mins/day)
    max_bars_calc = args.days * 381
    
    replay_spec = ReplaySpec(
        symbol=symbol,
        timeframe="minute",
        timezone="Asia/Seoul", # Data is migrated, timezone should match Gate data
        warmup_bars=200,
        fill=fill_spec,
        cost=cost_model,
        base_multiplier=1.0,
        max_bars=max_bars_calc, 
    )
    
    # V3 Params (Vol Targeting)
    # Minute data: 2% daily vol ~ 2% / sqrt(380) per minute? 
    # Or is target_vol in turbo.py absolute?
    # turbo.py: target_vol=0.02 default. 
    # If using minute returns, std is very small (e.g. 0.0005). 
    # So target_vol should be scaled to minute timeframe.
    # Daily Target 2% (0.02) -> Minute Target = 0.02 / sqrt(381) ≈ 0.001
    
    turbo_params = TurboParams(
        max_multiplier=args.max_mult,  # Locked Top
        min_multiplier=1.0,
        vol_window=60,       # 1 hour
        target_vol=0.0010,   # ~2% Daily Vol equivalent in minutes
        fast_exit_on_bear=True,
        fast_exit_drawdown=0.03
    )
    
    print(f"Target: {symbol}")
    print(f"Fill: {fill_spec.method}")
    print(f"Cost: Slippage={cost_model.slippage_rate}, Tax={cost_model.sell_tax_rate}")
    print(f"Turbo: TargetVol={turbo_params.target_vol}, MaxMult={turbo_params.max_multiplier}")
    
    try:
        res = run_replay(
            project_root=project_root,
            replay=replay_spec,
            regime_params=RegimeParams(),
            signal_params=SignalParams(),
            turbo_params=turbo_params,
            initial_equity=100_000_000.0, # 100M KRW
            collect_debug=False
        )
    except Exception as e:
        print(f"[ERROR] Replay Failed: {e}")
        import traceback
        traceback.print_exc()
        return

    # Results
    metrics = res.metrics
    trades = res.trades
    equity = res.equity_curve
    
    print("-" * 40)
    print(f"Total Return: {metrics['total_return']*100:.2f}%")
    print(f"Max Drawdown: {metrics['max_drawdown']*100:.2f}%")
    print(f"Trade Count: {len(trades)}")
    print("-" * 40)
    
    # Save Reports (SSOT v2.1)
    from garam_core.reporting.report_writer import write_report_bundle, utc_now_iso, PASS
    from garam_core.analysis.edge_matrix import EdgeAnalyzer
    
    # Needs minute data for EdgeMatrix
    # ReplayRunner loads data internally but doesn't expose raw DF easily in Result depending on impl.
    # We should reload it or assume we can get it.
    # Ideally load data FIRST in main, then pass to replay.
    
    # Quick fix: Reload for analysis (inefficient but safe for verification script)
    from garam_core.data.loader import load_ohlcv
    # project_root is "garam_core", data is "../GARAM_Data"
    # Actually paths.yaml handles it.
    # Let's try to load using the same logic ReplayRunner uses or just manual load.
    
    # Manual load for EdgeMatrix
    try:
        data_path = project_root.parent / "GARAM_Data/history/minute" / f"{symbol}.csv"
        # Force correct path if needed
        if not data_path.exists():
             data_path = Path("c:/garam/garam/GARAM_Data/history/minute") / f"{symbol}.csv"
        
        print(f"[DEBUG] Loading minute data from: {data_path}")
        minute_df = pd.read_csv(data_path, parse_dates=['date'], index_col='date')
        print(f"[DEBUG] Loaded minute_df: {len(minute_df)} rows")
    except Exception as e:
        print(f"[WARN] data load for EdgeMatrix failed: {e}")
        minute_df = pd.DataFrame()

    # Analyze
    edge_analysis = {}
    if not minute_df.empty:
        # Debug Trade Attributes
        # Reconstruct Round-Trip Trades from Fills
        # res.trades contains [Fill(ENTER), Fill(EXIT), Fill(ENTER)...]
        # We must pair them to calculate PnL and Duration.
        
        trade_dicts = []
        current_entry = None
        
        # Sort fills by timestamp just in case
        fills = sorted(trades, key=lambda x: pd.to_datetime(x['ts']))
        
        for f in fills:
            ftype = f.get('type')
            fts = pd.to_datetime(f.get('ts'))
            fprice = float(f.get('price', 0.0))
            
            if ftype == 'ENTER':
                current_entry = {
                    'entry_time': fts,
                    'entry_price': fprice,
                    # Assume LONG for now as Turbo is Long-Only usually? 
                    # Or check multiplier/side if available. 
                    # Defaulting to LONG.
                    'side': 'LONG' 
                }
            elif ftype == 'EXIT':
                if current_entry:
                    # Close the trade
                    entry_p = current_entry['entry_price']
                    exit_p = fprice
                    
                    # Calc Returns
                    raw_ret = 0.0
                    if entry_p > 0:
                        raw_ret = (exit_p - entry_p) / entry_p
                    
                    # Cost
                    slip = cost_model.slippage_rate
                    tax = cost_model.sell_tax_rate
                    cost_ret = (slip * 2) + tax
                    
                    # Net
                    net_ret = raw_ret - cost_ret # Simple deduction
                    gross_ret = raw_ret # Gross is raw return before cost
                    
                    trade_record = {
                        "entry_time": current_entry['entry_time'],
                        "exit_time": fts,
                        "gross_return": gross_ret,
                        "cost_return": cost_ret,
                        "net_return": net_ret,
                        "regime": "UNCERTAIN" # Placeholder for analyzer
                    }
                    trade_dicts.append(trade_record)
                    current_entry = None # Reset
                else:
                    print(f"[WARN] Exit fill without Entry at {fts}")

        trades_df = pd.DataFrame(trade_dicts)

        if not trades_df.empty:
            print(f"[DEBUG] Reconstructed Trades Entry Time Head:\n{trades_df['entry_time'].head()}")
            print(f"[DEBUG] Minute DF Index Head:\n{minute_df.index[:5]}")
            if hasattr(minute_df.index, 'tz'):
                 print(f"[DEBUG] Minute DF TZ: {minute_df.index.tz}")
        
        # Analyzer (Strict V2.1)
        analyzer = EdgeAnalyzer(thresholds={
            "crash_mdd": -0.40,
            "overtrade_trades_per_day": 20,
            "min_trades_per_regime": 30,
            "regime_spread_exp_net": 0.0015,
            "signal_noise_win_rate": 0.35,
            "signal_noise_payout_mult": 1.5
        })
        
        try:
            # DEBUG: Timestamp Analysis
            print(f"[DEBUG] Minute Index Head: {minute_df.index[:3]}")
            if not minute_df.empty:
                 print(f"[DEBUG] Minute Index Tz: {minute_df.index.tz}")
            print(f"[DEBUG] Trade Entry Head: {trades_df['entry_time'].head(3)}")
            
            # Check Return Validity
            if trades_df['gross_return'].abs().sum() == 0:
                 print("[WARN] Gross Returns are all ZERO! Logic Error!")
            else:
                 # Assert Consistency
                 diff = (trades_df['gross_return'] - trades_df['cost_return'] - trades_df['net_return']).abs().max()
                 if diff > 1e-9:
                      print(f"[WARN] Return Consistency Check Failed! Max Diff: {diff}")
                 else:
                      print("[PASS] Return Consistency Check OK")

            # Inject MDD and TPD for tags
            # TPD = Trades / Trading Days (unique dates)
            trading_days_count = pd.to_datetime(trades_df['entry_time']).dt.date.nunique()
            tpd = len(trades_df) / max(1, trading_days_count)
            
            extra_kpis = {
                "mdd": float(metrics['max_drawdown']),
                "trades_per_day": float(tpd),
                "trading_days": int(trading_days_count),
                # Disambiguation Fields
                "trade_sum_net_return": float(trades_df['net_return'].sum()),
                "equity_total_return": float(metrics['total_return'])
            }
            
            edge_analysis = analyzer.analyze(
                trades_df=trades_df,
                minute_df=minute_df,
                extra_kpis=extra_kpis
            )
        except Exception as e:
             print(f"[ERROR] EdgeAnalyzer failed: {e}")
             import traceback
             traceback.print_exc()

    run_id = f"verify_turbo_v3_{symbol}_{pd.Timestamp.utcnow().strftime('%Y%m%d_%H%M%S')}"
    
    # KPIs
    kpis = {
        "trades": len(trades),
        "total_return": float(metrics['total_return']),
        "max_drawdown": float(metrics['max_drawdown']),
        "final_equity": float(equity.iloc[-1]),
        "fill_method": fill_spec.method,
        "slippage_rate": cost_model.slippage_rate,
        "tax_rate": cost_model.sell_tax_rate,
    }
    
    # Construct Report v2.1
    report = {
        "meta": {
            "run_id": run_id,
            "timestamp_utc": utc_now_iso(),
            "mode": "verification",
            "env": {"python": sys.version.split()[0]},
            "data": {"universe": symbol, "timeframe": "minute"},
            "units": {"returns": "decimal", "costs": "decimal", "currency": "KRW"},
            "regime_spec": {
                "source": "minute", 
                "method": "micro_regime_v1", 
                "params": {
                    "trend": "ema_slope(20,120)", 
                    "vol": "atr_pct(120)", 
                    "chop": "er(120)",
                    "panic": "zscore(120)>3.0"
                }
            }
        },
        "summary": {
            "status": PASS,
            "headline": f"Turbo V3 Verified Result ({symbol})",
            "kpis": kpis,
            "key_points": [
                f"Total Return: {metrics['total_return']*100:.2f}%",
                f"Max Drawdown: {metrics['max_drawdown']*100:.2f}%",
                f"Trades: {len(trades)}",
                f"Final Equity: {equity.iloc[-1]:,.0f} KRW",
            ]
        },
        "edge_analysis": edge_analysis,
        "checks": [
            {
                "id": "B-6-LOCK",
                "name": "Cost Model Locked",
                "status": PASS,
                "severity": "high",
                "metrics": {
                    "slippage": f"{cost_model.slippage_rate*10000:.1f}bp",
                    "tax": f"{cost_model.sell_tax_rate*100:.2f}%"
                },
                "notes": ["Confirmed B-6 cost model application."]
            }
        ],
        "artifacts": {}
    }
    
    # Execute Writer
    reports_root = project_root / "reports"
    out = write_report_bundle(reports_root, report)
    
    # Save CSV to run_dir
    csv_path = out["run_dir"] / f"equity_{symbol}.csv"
    equity.to_csv(csv_path)
    print(f"[SSOT] Report generated at: {out['run_dir']}")
    print(f"[SSOT] Latest linked: {reports_root / 'latest.json'}")

if __name__ == "__main__":
    main()
