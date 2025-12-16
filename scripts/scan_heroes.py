# scripts/scan_heroes.py
"""
Phase 21-B: 히어로 스캐너 (2-Pass + --limit)
"""
import sys
import argparse
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime

sys.path.append(str(Path(__file__).resolve().parents[1]))

from garam_core.fastlane.feature_store import FeatureStore
from garam_core.fastlane.policy_eval import PolicyParams
from garam_core.analysis.hero_finder import (
    HeroFinder, HeroProbe, HeroCriteria,
    OvernightCriteriaStrict, OvernightCriteriaSoft
)


PROBES = {
    "MOM_BASE": HeroProbe(
        name="MOM_BASE",
        params=PolicyParams(
            strategy_type="MOMENTUM",
            min_momentum_k=1.0,
            abs_momentum_floor=0.002,
            cost_floor=0.0025,
            max_hold_bars=120,
            fee=0.00015,
            slippage=0.0005,
            tax=0.0020
        ),
        description="기본 모멘텀"
    ),
    "MR_RSI_30": HeroProbe(
        name="MR_RSI_30",
        params=PolicyParams(
            strategy_type="MEAN_REVERSION",
            mr_mode="RSI",
            mr_rsi_entry=30.0,
            mr_rsi_exit=50.0,
            use_ma_filter=False,
            max_hold_bars=120,
            fee=0.00015,
            slippage=0.0005,
            tax=0.0020
        ),
        description="평균회귀 RSI<30"
    ),
}


def load_universe(path: str, limit: int = None) -> list:
    if not Path(path).exists():
        raise FileNotFoundError(f"유니버스 파일 없음: {path}")
    df = pd.read_csv(path, dtype={"symbol": str})
    if "symbol" not in df.columns:
        raise ValueError("'symbol' 컬럼 필요")
    # FIX: 0-padding to 6 digits
    symbols = [str(s).strip().zfill(6) for s in df["symbol"]]
    if limit:
        symbols = symbols[:limit]
    return symbols


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--universe", default="data/universe_400.csv")
    parser.add_argument("--probe", choices=list(PROBES.keys()), default="MOM_BASE")
    parser.add_argument("--window", type=int, default=30)
    parser.add_argument("--limit", type=int, default=None, help="테스트용 종목 수 제한")
    parser.add_argument("--two_pass", action="store_true", help="2-Pass 스캔 (Top-K만 ON/Gap)")
    parser.add_argument("--top_k", type=int, default=50, help="2-Pass 시 Top-K")
    parser.add_argument("--force_recompute", action="store_true")
    parser.add_argument("--out", default=None)
    parser.add_argument("--display_n", type=int, default=10)
    parser.add_argument("--quiet", action="store_true", help="Suppress console output")
    parser.add_argument("--logfile", help="Redirect output to log file")
    parser.add_argument("--aum", type=float, default=10_000_000,
                       help="Assets under management for allocation plan (default: 10M)")
    parser.add_argument("--allocate", action="store_true",
                       help="Generate allocation plan CSV from heroes")
    
    args = parser.parse_args()
    
    # Logfile redirection
    logfile_handle = None
    original_stdout = None
    if args.logfile:
        logfile_path = Path(args.logfile)
        logfile_path.parent.mkdir(parents=True, exist_ok=True)
        logfile_handle = open(logfile_path, 'w', encoding='utf-8')
        original_stdout = sys.stdout
        sys.stdout = logfile_handle
        print(f"# Log file: {logfile_path}")
        print(f"# {datetime.now()}\n")
    
    try:
        universe = load_universe(args.universe, limit=args.limit)
        probe = PROBES[args.probe]
        criteria = HeroCriteria()
        overnight_strict = OvernightCriteriaStrict()
        overnight_soft = OvernightCriteriaSoft()
        
        fs = FeatureStore(cache_dir="cache/features")
        finder = HeroFinder(fs)
        
        print(f"{'='*60}")
        print(f"  Phase 21-B: 히어로 스캔")
        print(f"  Probe: {probe.name} (Tax: {probe.params.tax:.4f}, Fee: {probe.params.fee:.5f})")
        print(f"{'='*60}")
        print(f"유니버스: {len(universe)}개")
        if args.limit:
            print(f"제한: 첫 {args.limit}개 (테스트 모드)")
        if args.two_pass:
            print(f"2-Pass: Top-{args.top_k}만 Overnight/Gap 계산")
        print(f"{'='*60}\n")
        
        results = finder.scan(
            universe=universe,
            probe=probe,
            criteria=criteria,
            overnight_strict=overnight_strict,
            overnight_soft=overnight_soft,
            window_days=args.window,
            force_recompute_features=args.force_recompute,
            two_pass=args.two_pass,
            top_k=args.top_k,
        )
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_dir = Path(args.out) if args.out else Path("results")
        out_dir.mkdir(exist_ok=True, parents=True)
        
        # Full CSV
        df_full = pd.DataFrame([r.to_dict() for r in results])
        path_full = out_dir / f"hero_scan_{args.probe}_{timestamp}.csv"
        df_full.to_csv(path_full, index=False)
        print(f"\n[출력] 전체: {path_full}")
        
        # Phase 21-C: Allocation Plan
        if args.allocate:
            try:
                from garam_core.analysis.capital_policy import CapitalPolicy
                
                heroes_only = [r for r in results if r.is_hero]
                policy = CapitalPolicy()
                allocation = policy.plan(aum=args.aum, heroes=heroes_only)
                
                alloc_path = out_dir / f"allocation_{args.probe}_{timestamp}.csv"
                allocation.to_csv(alloc_path, index=False)
                
                print(f"\n[Allocation Plan]")
                print(f"  AUM: {args.aum:,.0f}")
                print(f"  Heroes: {len(heroes_only)}")
                print(f"  Output: {alloc_path}")
                print(f"  Summary:")
                print(allocation.groupby(['sleeve', 'tier'])['weight'].sum().to_string())
            except Exception as e:
                print(f"\n[Allocation Plan] FAILED: {e}")
        
        # Heroes
        heroes = [r for r in results if r.is_hero]
        if heroes:
            print(f"\n히어로: {len(heroes)}개")
            print(pd.DataFrame([{
                "종목": r.symbol,
                "기대값": f"{r.expectancy_net:.4f}",
                "승률": f"{r.win_rate:.3f}",
                "ON등급": r.overnight_tier,
            } for r in heroes[:args.display_n]]).to_string(index=False))
        else:
            print(f"\n히어로 없음 (NO HERO = NO TRADE)")
        
        # STRICT
        strict = [r for r in results if r.overnight_tier == "STRICT"]
        if strict:
            strict.sort(key=lambda x: x.overnight_score, reverse=True)
            print(f"\nON-STRICT: {len(strict)}개")
            print(pd.DataFrame([{
                "종목": r.symbol,
                "점수": f"{r.overnight_score:.6f}",
                "ON기대값": f"{r.overnight_expectancy_net:.4f}",
                "갭P10": f"{r.gap_p10:.4f}" if np.isfinite(r.gap_p10) else "N/A",
                "갭N": r.gap_n
            } for r in strict[:args.display_n]]).to_string(index=False))
        
        # SOFT
        soft = [r for r in results if r.overnight_tier == "SOFT"]
        if soft:
            soft.sort(key=lambda x: x.overnight_score, reverse=True)
            print(f"\nON-SOFT: {len(soft)}개 (소액 시험용)")
            print(pd.DataFrame([{
                "종목": r.symbol,
                "ON기대값": f"{r.overnight_expectancy_net:.4f}" if r.overnight_trades > 0 else "갭기준",
                "갭P10": f"{r.gap_p10:.4f}" if np.isfinite(r.gap_p10) else "N/A",
                "갭N": r.gap_n,
                "ON거래": r.overnight_trades
            } for r in soft[:args.display_n]]).to_string(index=False))
        
        print(f"\n{'='*60}")
        print(f"  완료")
        print(f"{'='*60}\n")
    
    finally:
        # Restore stdout and close logfile
        if logfile_handle:
            sys.stdout = original_stdout
            logfile_handle.close()
            if original_stdout:
                print(f"[Log saved] {args.logfile}")


if __name__ == "__main__":
    main()
