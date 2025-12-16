# scripts/research/run_all.py
import sys
import argparse
from pathlib import Path
from datetime import datetime
import shutil

# Setup path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT))

# Ensure patches are loaded if active
patch_pth = PROJECT_ROOT / "patches" / "patches.pth"
if patch_pth.exists():
    try:
        patch_dir = patch_pth.read_text(encoding="utf-8").strip()
        if patch_dir and Path(patch_dir).exists():
            sys.path.insert(0, patch_dir)
            print(f"[PATCH] Active: {patch_dir}")
    except Exception as e:
        print(f"[PATCH] Error loading patch: {e}")

from garam_core.strategy.registry import discover_strategies
from garam_core.backtest.engine_unified import run_backtest_unified
from garam_core.research.pulse.load_data import load_minute_data, enhance_features

# Reporter
try:
    from scripts.research.reporter import generate_report
except ImportError:
    sys.path.append(str(Path(__file__).parent))
    from reporter import generate_report

# Universe + Gate
from scripts.research.universe_loader import load_universe_symbols
from scripts.research.gate import GateConfig, load_summary_csv, decide_accept, write_manifest

# Top-K Portfolio (optional)
from scripts.research.portfolio_topk_backtest import run_portfolio_topk, save_outputs

# Pulse EV (optional)
from scripts.research.pulse_ev_runner import pick_top_strategies, run_pulse_ev_for_results, inject_pulse_section


def _timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _copy_reports(src_reports: Path, dst_dir: Path):
    dst_dir.mkdir(parents=True, exist_ok=True)
    # fixed files
    for name in ["summary.csv", "report.md", "portfolio_equity.png", "run_manifest.json"]:
        p = src_reports / name
        if p.exists():
            shutil.copy2(p, dst_dir / name)

    # equity per symbol
    for p in src_reports.glob("equity_*.png"):
        shutil.copy2(p, dst_dir / p.name)

    # Top-K folder snapshot too (if exists)
    topk_dir = src_reports / "portfolio_topk"
    if topk_dir.exists():
        dst_topk = dst_dir / "portfolio_topk"
        dst_topk.mkdir(parents=True, exist_ok=True)
        for p in topk_dir.glob("*"):
            if p.is_file():
                shutil.copy2(p, dst_topk / p.name)
    
    # Pulse EV folder
    pulse_dir = src_reports / "pulse_hold_ev"
    if pulse_dir.exists():
        dst_pulse = dst_dir / "pulse_hold_ev"
        dst_pulse.mkdir(parents=True, exist_ok=True)
        shutil.copytree(pulse_dir, dst_pulse, dirs_exist_ok=True)

    # Pulse Surface folder
    surface_dir = src_reports / "pulse_surface"
    if surface_dir.exists():
        dst_surf = dst_dir / "pulse_surface"
        dst_surf.mkdir(parents=True, exist_ok=True)
        shutil.copytree(surface_dir, dst_surf, dirs_exist_ok=True)
    
    # Recommendations folder
    rec_dir = src_reports / "recommendations"
    if rec_dir.exists():
        dst_rec = dst_dir / "recommendations"
        dst_rec.mkdir(parents=True, exist_ok=True)
        shutil.copytree(rec_dir, dst_rec, dirs_exist_ok=True)


def run_all(
    symbols: list,
    data_dir: str,
    gate: GateConfig,
    accept_on_first: bool = True,
    # Top-K options
    run_topk: bool = False,
    portfolio_strategy: str = "regime_switch",
    k: int = 3,
    weight_mode: str = "equal",
    replace_threshold: float = 1.2,
    # Pulse EV options
    run_pulse_ev: bool = False,
    pulse_symbol: str = "",
    pulse_topn: int = 3,
    pulse_bucket: int = 5,
    # Pulse Recommend
    pulse_recommend: bool = False,
    apply_recommendations: bool = False,
    # Pulse Surface (EV/Vol Grid)
    pulse_surface: bool = False,
    surface_ev_grid: list[float] = None,
    surface_vol_grid: list[float] = None,
):
    print("=== Starting Research Loop ===")
    print(f"Symbols: {symbols}")
    
    strategies = discover_strategies()
    # strategies list contains classes
    
    all_results = []
    failed_symbols = []
    loaded_dfs = {}  # sym -> df

    # 1) Data load
    for sym in symbols:
        try:
            df = load_minute_data(sym, data_dir)
            df = enhance_features(df)
            loaded_dfs[sym] = df
            print(f"[DATA] Loaded {sym}: {len(df)} bars")
        except Exception as e:
            # print(f"Failed to load data for {sym}: {e}")
            failed_symbols.append(sym)

    # 2) Run Strategies (Initial Baseline)
    # Patches might be active here if loaded at top, applying global or previously active symbol patches.
    # Note: If we just started, patches might be empty or prev run. 
    # Usually we want baseline to use 'default' or 'current patch'.
    for sym, df in loaded_dfs.items():
        print(f"\n--- Strategy Run: {sym} ---")
        for StratClass in strategies:
            # Instantiate with symbol if supported (for patch support)
            try:
                strat = StratClass(symbol=sym)
            except TypeError:
                strat = StratClass() # fallback
            
            try:
                res = run_backtest_unified(strat, df)
                res["symbol"] = sym
                all_results.append(res)
                print(f"  {strat.NAME}: ROI {res['roi']:.2%}, Trades {res['trades']}")
            except Exception as e:
                print(f"  {strat.NAME}: Error {e}")

    reports_dir = PROJECT_ROOT / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    if not all_results:
        print("No results generated.")
        return

    # 3) Report
    generate_report(all_results, reports_dir)
    
    top_strats = []
    if (reports_dir / "summary.csv").exists():
        top_strats = pick_top_strategies(reports_dir / "summary.csv", top_n=int(pulse_topn))

    # 4) Pulse Hold-EV Analysis (Strategy-Specific)
    strat_dirs = {}
    if run_pulse_ev and top_strats:
        print("\n=== Pulse Hold-EV Analysis ===")
        # Analyze for ALL loaded symbols if pulse_symbol is not strict, 
        # or just target logic. User code suggested "Symbol-wise recommendation", 
        # so we should run it for ALL symbols to get symbol-wise data.
        
        # Logic: run_pulse_ev_runner usually takes a target symbol. 
        # We will loop over all symbols to generate full map for recommendations.
        
        out_base = reports_dir / "pulse_hold_ev"
        
        # Optimization: Only run for symbols we loaded
        for sym in loaded_dfs.keys():
            target_results = [r for r in all_results if r.get("symbol") == sym and r.get("strategy") in top_strats]
            if not target_results: continue
            
            s_dirs = run_pulse_ev_for_results(
                results=target_results,
                symbol=sym,
                df_index=loaded_dfs[sym].index,
                out_base=out_base,
                bucket=int(pulse_bucket)
            )
            strat_dirs.update(s_dirs)
        
        # Inject just one representative or all? Injecting all might be too long. 
        # Let's inject the first or user specified pulse_symbol
        disp_sym = pulse_symbol if pulse_symbol in loaded_dfs else (list(loaded_dfs.keys())[0] if loaded_dfs else "")
        if disp_sym:
            # gather dirs for this symbol
            disp_dirs = {k:v for k,v in strat_dirs.items() if f"/{disp_sym}_" in str(v).replace("\\","/")} 
            if disp_dirs:
                inject_pulse_section(reports_dir / "report.md", disp_sym, disp_dirs)

    # 5) Pulse Surface (EV/Vol Grid) Analysis
    if pulse_surface:
        print("\n=== Pulse Surface Analysis (Grid Search) ===")
        from scripts.research.pulse_surface_runner import run_surface_for_symbols, save_surface_recommendations
        from scripts.research.apply_surface_patch import make_surface_patch, activate_surface_patch

        ev_grid = surface_ev_grid or [1.0, 1.2, 1.5]
        vol_grid = surface_vol_grid or [1.1, 1.3, 1.5]

        # Use current Gate settings mostly for criteria
        surface_dir = reports_dir / "pulse_surface"
        surf_rec_map = run_surface_for_symbols(
            dfs=loaded_dfs,
            ev_mult_grid=ev_grid,
            vol_mult_grid=vol_grid,
            base_params={}, 
            max_mdd_abs=gate.max_mdd_abs,
            min_trades=gate.min_trades,
            target_winrate=0.60, # Preferred winrate
            out_dir=surface_dir,
        )

        surf_yaml = reports_dir / "recommendations" / "symbol_pulse_surface.yaml"
        save_surface_recommendations(surf_yaml, surf_rec_map)

        if apply_recommendations:
            patch = make_surface_patch(PROJECT_ROOT, surf_rec_map)
            activate_surface_patch(PROJECT_ROOT, patch)
            print(f"[SURFACE APPLY] Patch activated: {patch}")


    # 6) Recommendations & Patching (MaxHold)
    if pulse_recommend and top_strats:
        print("\n=== Symbol-wise MaxHold Recommendations ===")
        try:
            from scripts.research.pulse_recommend_symbolwise import recommend_symbolwise, write_symbolwise_recommendations
            from scripts.research.apply_symbolwise_patch import make_symbolwise_patch, activate_symbolwise_patch

            symbol_rec_map = recommend_symbolwise(
                base_dir=reports_dir / "pulse_hold_ev",
                bucket=int(pulse_bucket),
                top_strategies=top_strats
            )

            out_yaml = reports_dir / "recommendations" / "symbol_specific_max_hold.yaml"
            write_symbolwise_recommendations(out_yaml, symbol_rec_map)
            print(f"[RECOMMEND] Saved => {out_yaml}")

            if apply_recommendations and len(symbol_rec_map) > 0:
                patch_file = make_symbolwise_patch(PROJECT_ROOT, symbol_rec_map)
                activate_symbolwise_patch(PROJECT_ROOT, patch_file)
                print(f"[APPLY] Patch activated: {patch_file}")

        except Exception as e:
            print(f"[RECOMMEND] Failed: {e}")

    # 7) Top-K Portfolio Backtest (Using patched logic if applied)
    # If we applied patches above, we want to re-instantiate strategies. 
    # run_portfolio_topk does dynamic discovery, but we should make sure 
    # it passes 'symbol=' to constructor if our patch requires it.
    
    if run_topk:
        print("\n=== Running Top-K Portfolio Backtest ===")
        # We need to modify portfolio_topk_backtest to optionally pass symbol to constructor
        # or we rely on the fact that existing code calls discover_strategies()
        # and if we patched it, it handles it. 
        # BUT our patches expect __init__(self, symbol=None). 
        # The default implementation doesn't have symbol arg.
        # run_portfolio_topk code: `strat = strat_map[strategy_name]()` -> No symbol arg.
        # We should patch run_portfolio_topk.py as well to be safe, 
        # OR we can assume if the class supports it, it handles None (which our patch does).
        # Wait, the patch sets `self.max_hold_bars` based on `symbol`. 
        # If run_portfolio_topk passes None, it won't apply symbol specific logic.
        # So we MUST update `run_portfolio_topk` to run `strat = StratClass(symbol=sym)`.
        
        # Since I am rewriting run_all, I will assume portfolio_topk is already updated 
        # OR I should update it. The user prompt explicitly said: 
        # "Title: Top-K 포트폴리오 에도 각각 다른 max_hold_bars를 적용하는 확장판"
        # "Top-K 포트폴리오 실행 시 종목별 max_hold_bars 적용"
        # "Top-K 백테스트에서 strat = MeanReversionStrategy(symbol=sym) 호출"
        
        # I need to edit portfolio_topk_backtest.py to support this. I will do it in next tool calls.
        
        if len(loaded_dfs) < 2:
            print("[WARN] Less than 2 symbols, Top-K skipped.")
        else:
            try:
                res_port = run_portfolio_topk(
                    dfs=loaded_dfs,
                    strategy_name=portfolio_strategy,
                    k=int(k),
                    weight_mode=str(weight_mode),
                    replace_threshold=float(replace_threshold),
                    # cost/lookback args can be passed if needed
                )
                tag = f"{portfolio_strategy}_K{k}_{weight_mode}_rt{replace_threshold}"
                out_dir = reports_dir / "portfolio_topk"
                save_outputs(res_port, out_dir, tag)
                print("[TOPK] Completed.")
            except Exception as e:
                print(f"[TOPK] Failed: {e}")


    # 8) Archive & Gate
    run_id = _timestamp()
    runs_dir = reports_dir / "runs" / run_id
    last_dir = reports_dir / "last_run"
    
    _copy_reports(reports_dir, runs_dir)
    
    # Simple Gate Logic
    prev_summary = None
    if (last_dir / "summary.csv").exists():
        try:
             prev_summary = load_summary_csv(last_dir / "summary.csv")
        except: pass
        
    curr_summary = load_summary_csv(reports_dir / "summary.csv")
    accept, reason = decide_accept(prev_summary, curr_summary, gate)
    
    manifest = {
        "run_id": run_id,
        "created_at": datetime.now().isoformat(),
        "decision": reason,
        "accepted": accept
    }
    write_manifest(reports_dir, manifest)
    shutil.copy2(reports_dir / "run_manifest.json", runs_dir / "run_manifest.json")
    
    print(f"\n[GATE] {reason}")
    if accept or (prev_summary is None and accept_on_first):
        _copy_reports(reports_dir, last_dir)
        print(f"[DECISION] ACCEPT => Updated last_run")
    else:
        print(f"[DECISION] REJECT")
    
    print("\nCompleted.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbols", default="")
    parser.add_argument("--universe", default="")
    parser.add_argument("--data_dir", default=str(PROJECT_ROOT / "GARAM_Data/minute/kr"))
    
    parser.add_argument("--max_mdd", type=float, default=0.20)
    parser.add_argument("--min_trades", type=int, default=5)
    parser.add_argument("--improve_roi_min", type=float, default=0.0)

    parser.add_argument("--topk", action="store_true")
    parser.add_argument("--portfolio_strategy", default="regime_switch")
    parser.add_argument("--k", type=int, default=3)
    parser.add_argument("--weight_mode", default="equal")
    parser.add_argument("--replace_threshold", type=float, default=1.2)
    
    parser.add_argument("--pulse_ev", action="store_true")
    parser.add_argument("--pulse_symbol", default="")
    parser.add_argument("--pulse_topn", type=int, default=3)
    parser.add_argument("--pulse_bucket", type=int, default=5)
    
    parser.add_argument("--pulse_recommend", action="store_true")
    parser.add_argument("--apply_recommendations", action="store_true")
    
    parser.add_argument("--pulse_surface", action="store_true")
    parser.add_argument("--surface_ev_grid", default="1.0,1.2,1.5")
    parser.add_argument("--surface_vol_grid", default="1.1,1.3,1.5")

    args = parser.parse_args()

    if args.universe:
        sym_list = load_universe_symbols(args.universe)
    else:
        sym_list = [s.strip() for s in args.symbols.split(",") if s.strip()]

    gate = GateConfig(
        max_mdd_abs=float(args.max_mdd),
        min_trades=int(args.min_trades),
        improve_roi_min=float(args.improve_roi_min),
    )
    
    ev_grid = [float(x) for x in args.surface_ev_grid.split(",") if x.strip()]
    vol_grid = [float(x) for x in args.surface_vol_grid.split(",") if x.strip()]

    run_all(
        symbols=sym_list,
        data_dir=args.data_dir,
        gate=gate,
        run_topk=bool(args.topk),
        portfolio_strategy=str(args.portfolio_strategy),
        k=int(args.k),
        weight_mode=str(args.weight_mode),
        replace_threshold=float(args.replace_threshold),
        run_pulse_ev=bool(args.pulse_ev),
        pulse_symbol=str(args.pulse_symbol),
        pulse_topn=int(args.pulse_topn),
        pulse_bucket=int(args.pulse_bucket),
        pulse_recommend=bool(args.pulse_recommend),
        apply_recommendations=bool(args.apply_recommendations),
        pulse_surface=bool(args.pulse_surface),
        surface_ev_grid=ev_grid,
        surface_vol_grid=vol_grid,
    )
