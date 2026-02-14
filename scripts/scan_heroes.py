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

# sys.path.append(str(Path(__file__).resolve().parents[1]))  # Standard: Run via python -m scripts.scan_heroes

from garam_core.fastlane.feature_store import FeatureStore
from garam_core.fastlane.policy_eval import PolicyParams
from garam_core.analysis.hero_finder import (
    HeroFinder, HeroProbe, HeroCriteria,
    OvernightCriteriaStrict, OvernightCriteriaSoft
)

# ============================================================
# SSOT v1.2.0 SEAL PATCH (Champion Hero)
# Required columns in hero_scan CSV:
#   champion_score_norm (0~1), ref_price, veto, veto_reason
#   + optional: regime_ban
# Floor Rule: if champion_score <= 0 => champion_score_norm = 0.0
# Normalization: cross-sectional rank percentile among POSITIVE scores
# ============================================================

from typing import Iterable, Optional, Sequence, Tuple
import pandas as pd
import numpy as np

def _first_existing_col(df: pd.DataFrame, candidates: Sequence[str]) -> Optional[str]:
    for c in candidates:
        if c in df.columns:
            return c
    return None

def ensure_ssot_champion_scan_schema(df: pd.DataFrame) -> pd.DataFrame:
    """
    Make scan output CSV 'decision+orders ready' per SSOT v1.2.0.
    Enforces:
      - champion_score_norm: [0,1]
      - ref_price: non-null (<=0 becomes veto)
      - veto, veto_reason: always exists
      - (optional) regime_ban: always exists if absent -> False
    """
    if df is None or len(df) == 0:
        # Return minimal schema (still sealed)
        return pd.DataFrame(columns=[
            "symbol",
            "champion_score",
            "champion_score_norm",
            "ref_price",
            "veto",
            "veto_reason",
            "regime_ban",
            "reason_tags",
        ])

    out = df.copy()

    # --- symbol normalize ---
    if "symbol" not in out.columns:
        raise ValueError("[SSOT] scan result missing required column: symbol")
    out["symbol"] = out["symbol"].astype(str).str.zfill(6)

    # --- champion_score 확보 (raw) ---
    score_col = _first_existing_col(out, ["champion_score", "score_raw", "score", "alpha_score", "expectancy_net"])
    if score_col is None:
        out["champion_score"] = 0.0
        score_col = "champion_score"
    else:
        if score_col != "champion_score":
            out["champion_score"] = pd.to_numeric(out[score_col], errors="coerce").fillna(0.0)
        else:
            out["champion_score"] = pd.to_numeric(out["champion_score"], errors="coerce").fillna(0.0)

    # --- ref_price 확보 (스캔 시점 가격: 단일 진실) ---
    price_col = _first_existing_col(out, ["ref_price", "last", "price", "close", "cur_price", "current_price"])
    if price_col is None:
        out["ref_price"] = 0.0
    else:
        if price_col != "ref_price":
            out["ref_price"] = pd.to_numeric(out[price_col], errors="coerce").fillna(0.0)
        else:
            out["ref_price"] = pd.to_numeric(out["ref_price"], errors="coerce").fillna(0.0)

    # --- regime_ban (optional but standardized) ---
    if "regime_ban" not in out.columns:
        out["regime_ban"] = False
    out["regime_ban"] = out["regime_ban"].astype(bool)

    # --- veto 초기화 ---
    if "veto" not in out.columns:
        out["veto"] = False
    out["veto"] = out["veto"].astype(bool)

    if "veto_reason" not in out.columns:
        out["veto_reason"] = ""
    out["veto_reason"] = out["veto_reason"].fillna("").astype(str)

    if "reason_tags" not in out.columns:
        out["reason_tags"] = ""
    out["reason_tags"] = out["reason_tags"].fillna("").astype(str)

    # --- VETO triggers (SSOT v1.2.0) ---
    # Vol_Accel > 1.5
    vol_col = _first_existing_col(out, ["vol_accel", "Vol_Accel", "VOL_ACCEL"])
    if vol_col is not None:
        vol = pd.to_numeric(out[vol_col], errors="coerce").fillna(0.0)
        mask = vol > 1.5
        out.loc[mask, "veto"] = True
        out.loc[mask, "veto_reason"] = out.loc[mask, "veto_reason"].where(
            out.loc[mask, "veto_reason"].str.len() > 0,
            "Vol_Accel>1.5"
        )
        out.loc[mask & (out["veto_reason"] != "Vol_Accel>1.5"), "veto_reason"] += ";Vol_Accel>1.5"

    # ATR% > 10.0
    atr_col = _first_existing_col(out, ["atr_pct", "ATR_PCT", "ATR%"])
    if atr_col is not None:
        atrp = pd.to_numeric(out[atr_col], errors="coerce").fillna(0.0)
        mask = atrp > 10.0
        out.loc[mask, "veto"] = True
        out.loc[mask, "veto_reason"] = out.loc[mask, "veto_reason"].where(
            out.loc[mask, "veto_reason"].str.len() > 0,
            "ATR%>10"
        )
        out.loc[mask & (out["veto_reason"] != "ATR%>10"), "veto_reason"] += ";ATR%>10"

    # Ref Price invalid
    mask_price = (out["ref_price"] <= 0) | (~np.isfinite(out["ref_price"]))
    if mask_price.any():
        out.loc[mask_price, "veto"] = True
        out.loc[mask_price, "veto_reason"] = out.loc[mask_price, "veto_reason"].where(
            out.loc[mask_price, "veto_reason"].str.len() > 0,
            "RefPrice<=0"
        )
        out.loc[mask_price & (out["veto_reason"] != "RefPrice<=0"), "veto_reason"] += ";RefPrice<=0"

    # --- champion_score_norm (Floor Rule + Cross-sectional percentile) ---
    raw = pd.to_numeric(out["champion_score"], errors="coerce").fillna(0.0)

    # Floor Rule
    norm = pd.Series(0.0, index=out.index, dtype=float)
    pos_mask = raw > 0

    if pos_mask.any():
        pos = raw[pos_mask]
        n = len(pos)
        if n == 1:
            norm.loc[pos.index] = 1.0
        else:
            # rank ascending: min->1, max->n
            r = pos.rank(method="min", ascending=True)
            norm.loc[pos.index] = (r - 1.0) / (n - 1.0)

    out["champion_score_norm"] = norm.clip(0.0, 1.0)

    # --- final schema order 보장 ---
    required = [
        "symbol",
        "champion_score",
        "champion_score_norm",
        "ref_price",
        "veto",
        "veto_reason",
        "regime_ban",
        "reason_tags",
    ]
    for c in required:
        if c not in out.columns:
            # 절대 발생하면 안 되지만, 안전하게 채움
            out[c] = "" if c in ("veto_reason", "reason_tags") else 0.0

    # 타입 안정화
    out["veto"] = out["veto"].astype(bool)
    out["regime_ban"] = out["regime_ban"].astype(bool)
    out["ref_price"] = pd.to_numeric(out["ref_price"], errors="coerce").fillna(0.0)
    out["champion_score_norm"] = pd.to_numeric(out["champion_score_norm"], errors="coerce").fillna(0.0)

    return out[required + [c for c in out.columns if c not in required]]


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
    "CHAMPION_V21": HeroProbe(
        name="CHAMPION_V21",
        params=PolicyParams(
            strategy_type="MOMENTUM",
            min_momentum_k=1.2, # Strong Momentum
            abs_momentum_floor=0.005, # Significant Move
            zscore_min=1.0, # Statistical Outlier
            cost_floor=0.0025,
            max_hold_bars=60, # Shorter swing
            fee=0.00015,
            slippage=0.0005,
            tax=0.0020
        ),
        description="챔피언 전략 (ORB+Momentum)"
    ),
}


from pipeline.store.data_loader import store

def load_universe_ssot(limit: int = None) -> list:
    df = store.get_universe()
    # Robust Column Handling (symbol vs Code)
    col = "symbol" if "symbol" in df.columns else ("Code" if "Code" in df.columns else None)
    if col is None:
        raise ValueError(f"Universe missing symbol column. cols={df.columns.tolist()}")
    
    symbols = [str(s).strip().zfill(6) for s in df[col]]
    if limit:
        symbols = symbols[:limit]
    return symbols


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--universe", default="data/universe_400.csv")
    parser.add_argument("--probe", choices=list(PROBES.keys()), default="CHAMPION_V21")
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
    
    if args.universe and args.universe != "data/universe_400.csv" and not args.quiet:
         print(f"[WARN] --universe ignored (SSOT=StoreManager.get_universe). got={args.universe}")

    try:
        universe = load_universe_ssot(limit=args.limit)
        probe = PROBES[args.probe]
        
        # Adjust Criteria based on Window
        # Window=30 days -> min_trades=30 is too harsh (1 trade/day).
        # Relax to ~1 trade per 3 days (10 trades) or minimum 5.
        min_trades_dynamic = max(5, int(args.window / 3))
        
        criteria = HeroCriteria(min_trades=min_trades_dynamic)
        overnight_strict = OvernightCriteriaStrict()
        overnight_soft = OvernightCriteriaSoft()
        
        fs = FeatureStore(cache_dir="cache/features")
        finder = HeroFinder(fs)
        
        print(f"{'='*60}")
        print(f"  Phase 21-B: 히어로 스캔")
        pp = probe.params
        print(f"  Probe: {probe.name}")
        print(f"  Params: fee={pp.fee} slip={pp.slippage} tax={pp.tax} cost_floor={getattr(pp,'cost_floor',None)} "
              f"hold={pp.max_hold_bars} type={pp.strategy_type}")
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
        
        # [SSOT v1.2.0] Enforce Schema Seal
        df_full = ensure_ssot_champion_scan_schema(df_full)
        
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
                "점수(N)": f"{r.champion_score_norm:.2f} ({r.champion_score:.4f})",
                "가격": r.ref_price,
                "Veto": "O" if r.veto else "X",
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
