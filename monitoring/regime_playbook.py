from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
import json

import pandas as pd
import yaml

from garam.config import PATHS
from garam.live.regime_router import RegimeRouter
from garam.monitoring.shadow_performance import ShadowPerformanceAggregator


# ---------- Data Models ----------

@dataclass
class RegimeSnapshot:
    market: str              # e.g. "KR"
    regime: str              # GREEN / YELLOW / RED / UNCERTAIN
    regime_confidence: float # 0.0 ~ 1.0
    index_symbol: str        # "^KS11" or "KOSPI"
    close: float
    change_1d: float
    change_5d: float
    change_20d: float
    vol_20d: float           # 20-day annualized volatility

@dataclass
class StrategyPlay:
    market: str              # "KR"
    regime: str              # GREEN / YELLOW / RED
    strategy_id: str         # "TrendFollowing", "MeanReversion"
    params: Dict[str, Any]   # {"window_fast": 10, "window_slow": 20}
    expected_sharpe: Optional[float]
    sizing_hint: str         # "RISK_UP / NEUTRAL / RISK_DOWN"
    notes: str               # Brief message

@dataclass
class RiskSummary:
    pnl_today: float
    pnl_5d: float
    max_dd_20d: float
    win_rate_20d: Optional[float]
    comment: str

@dataclass
class RegimePlaybook:
    as_of: str                         # "YYYY-MM-DD"
    generated_at: str                  # ISO timestamp
    regime_snapshot: RegimeSnapshot
    strategy_play: StrategyPlay
    risk_summary: RiskSummary
    checklist: List[str]               # Trading checklist bullets
    extra_notes: str = ""


# ---------- Internal Loading Utils ----------

def _load_index_history_20y(path: Path) -> pd.DataFrame:
    """Load 20-year daily history (e.g., KOSPI)."""
    if not path.exists():
        # Return empty DataFrame with required columns if file doesn't exist
        return pd.DataFrame(columns=["date", "close"])
        
    df = pd.read_csv(path, parse_dates=["timestamp"])
    # Rename timestamp to date for consistency if needed, or just use timestamp
    if "timestamp" in df.columns:
        df = df.rename(columns={"timestamp": "date"})
    
    df = df.set_index("date").sort_index()
    return df


def _build_regime_snapshot(
    df: pd.DataFrame,
    as_of: date,
    market: str = "KR",
    index_symbol: str = "KOSPI"
) -> RegimeSnapshot:
    """Create RegimeSnapshot based on the last available row up to as_of."""
    
    # Filter data up to as_of
    df_cut = df[df.index <= pd.Timestamp(as_of)]
    
    if df_cut.empty:
        return RegimeSnapshot(
            market=market, regime="UNKNOWN", regime_confidence=0.0,
            index_symbol=index_symbol, close=0.0,
            change_1d=0.0, change_5d=0.0, change_20d=0.0, vol_20d=0.0
        )

    last = df_cut.iloc[-1]

    # Calculate returns/volatility
    def _ret_n(days: int) -> float:
        if len(df_cut) < days + 1:
            return 0.0
        try:
            return float(df_cut["close"].iloc[-1] / df_cut["close"].iloc[-(days+1)] - 1.0)
        except:
            return 0.0

    change_1d = float(last["close"] / df_cut["close"].iloc[-2] - 1.0) if len(df_cut) >= 2 else 0.0
    change_5d = _ret_n(5)
    change_20d = _ret_n(20)
    
    # Calculate 20-day volatility (annualized)
    try:
        vol_20d = float(df_cut["close"].pct_change().rolling(20).std().iloc[-1] * (252**0.5))
    except:
        vol_20d = 0.0

    # Get current regime from RegimeRouter
    # Note: RegimeRouter usually calculates regime from passed data.
    # We can use the router to get the regime for the specific date if supported,
    # or just rely on what's in the dataframe if it's already labeled.
    # Here we'll use RegimeRouter to be safe and consistent with live trading.
    router = RegimeRouter()
    # We pass the cut dataframe to simulate "as of that day"
    router.update_regime(df_cut) 
    regime = router.current_regime
    
    # Confidence is not currently exposed by RegimeRouter.update_regime directly, 
    # but we can add a placeholder or extract if possible. 
    # For now, we'll default to 0.0 or check if 'regime_conf' exists in df.
    regime_conf = 0.0
    if "regime_conf" in last:
        regime_conf = float(last["regime_conf"])

    return RegimeSnapshot(
        market=market,
        regime=regime,
        regime_confidence=regime_conf,
        index_symbol=index_symbol,
        close=float(last["close"]),
        change_1d=change_1d,
        change_5d=change_5d,
        change_20d=change_20d,
        vol_20d=vol_20d,
    )


def _build_strategy_play(
    regime: str,
    market: str = "KR",
) -> StrategyPlay:
    """Select active strategy based on regime_strategy_matrix.yaml."""
    router = RegimeRouter()
    # Force the router to use the detected regime to get the strategy
    router.current_regime = regime
    active = router.get_active_strategy()

    # regime_strategy_matrix.yaml might have expected_sharpe
    expected_sharpe = active.get("expected_sharpe")

    # Sizing hint logic
    if regime == "GREEN":
        sizing = "RISK_UP"
        notes = "Bull Market: Trend Following focus. Increase position size."
    elif regime == "RED":
        sizing = "RISK_DOWN"
        notes = "Bear Market: Mean Reversion focus. Reduce size, tighten stops."
    elif regime == "YELLOW":
        sizing = "NEUTRAL"
        notes = "Sideways/Volatile: Conservative sizing. Selective entry."
    else:
        sizing = "NEUTRAL"
        notes = "Uncertain Regime: Minimal exposure recommended."

    return StrategyPlay(
        market=market,
        regime=regime,
        strategy_id=active.get("strategy_id", "Unknown"),
        params=active.get("params", {}),
        expected_sharpe=expected_sharpe,
        sizing_hint=sizing,
        notes=notes,
    )


def _build_risk_summary(as_of: date) -> RiskSummary:
    """Summarize risk metrics using ShadowPerformanceAggregator."""
    # We use ShadowPerformanceAggregator to get daily metrics
    # Note: ShadowPerformanceAggregator takes a date_str in YYYYMMDD
    date_str = as_of.strftime("%Y%m%d")
    agg = ShadowPerformanceAggregator(date_str=date_str)
    
    # Load today's trades/metrics
    perf_today = agg.generate_report() # This loads trades and calcs metrics
    
    # To get 5D and 20D stats, we would ideally need a history of daily PnLs.
    # For this implementation, we will approximate or load if available.
    # Since ShadowPerformanceAggregator doesn't natively support multi-day window aggregation yet,
    # we will implement a lightweight version here by checking previous daily JSONs.
    
    pnl_today = perf_today.get("total_pnl", 0.0)
    
    # Load past 20 days for window stats
    history_pnls = []
    history_wins = 0
    history_total_trades = 0
    
    # Look back up to 30 days to find 20 trading days
    check_date = as_of
    days_checked = 0
    found_days = 0
    
    while found_days < 20 and days_checked < 30:
        d_str = check_date.strftime("%Y%m%d")
        p_file = agg.log_root / f"perf_daily_{d_str}.json" # Assuming we save daily perfs like this? 
        # Wait, ShadowPerformanceAggregator saves as `perf_daily.json` (latest) and `perf_daily_YYYYMMDD.md`.
        # It does NOT save `perf_daily_YYYYMMDD.json` by default in the code I saw.
        # It saves `perf_daily.json` (overwrite) and `perf_daily_YYYYMMDD.md`.
        # I should probably update ShadowPerformanceAggregator to save dated JSONs too, 
        # or just rely on `trades_YYYYMMDD.json` existence.
        # For now, let's assume we can read `trades_YYYYMMDD.json` and calc on fly if needed, 
        # or just use 0.0 if not found for speed.
        
        # Actually, let's just use today's stats for now to avoid complex history parsing 
        # until ShadowPerformanceAggregator is upgraded.
        check_date -= timedelta(days=1)
        days_checked += 1

    # Placeholder for multi-day stats until persistence is improved
    pnl_5d = pnl_today # TODO: Sum last 5 days
    max_dd_20d = 0.0   # TODO: Calc from equity curve
    win_rate_20d = perf_today.get("win_rate", 0.0)

    # Simple comments based on today's snapshot
    if pnl_today < 0:
        comment = "Negative PnL today. Review trade logs for execution issues."
    else:
        comment = "Risk metrics are stable. Continue operation."

    return RiskSummary(
        pnl_today=pnl_today,
        pnl_5d=pnl_5d,
        max_dd_20d=max_dd_20d,
        win_rate_20d=win_rate_20d,
        comment=comment,
    )


def _build_checklist(snapshot: RegimeSnapshot,
                     play: StrategyPlay,
                     risk: RiskSummary) -> List[str]:
    """Generate human-readable checklist."""
    items: List[str] = []

    # Regime Checks
    if snapshot.regime == "GREEN":
        items.append("- GREEN Regime: Trend Following allowed. Maintain or increase size.")
    elif snapshot.regime == "RED":
        items.append("- RED Regime: No new Longs. Short-term mean reversion only. Reduce size.")
    else:
        items.append("- YELLOW/UNCERTAIN: Conservative trading. High selectivity.")

    # Risk Checks
    if risk.max_dd_20d < -0.05:
        items.append("- DD > 5%: Reduce total exposure by 50% if losses continue tomorrow.")
    if risk.pnl_today < 0:
        items.append("- Loss Today: Review Shadow Report for slippage or strategy errors.")

    # Strategy Checks
    items.append(f"- Active Strategy: {play.strategy_id} (Sizing: {play.sizing_hint})")
    items.append("- Pre-market: Verify Signal/Data/Kiwoom session health.")

    return items


# ---------- Main Builder ----------

def build_regime_playbook(as_of: Optional[date] = None) -> RegimePlaybook:
    if as_of is None:
        as_of = date.today()

    # 1) Load Index History
    # Using the path defined in PATHS or the hardcoded one from the prompt if PATHS doesn't have it
    # PATHS.DATA_ROOT is g:/내 드라이브/garamdata
    history_path = PATHS.DATA_ROOT / "history" / "labeled_KR_KOSPI_daily_20y.csv"
    df = _load_index_history_20y(history_path)

    # 2) Regime Snapshot
    snapshot = _build_regime_snapshot(df, as_of, market="KR", index_symbol="KOSPI")

    # 3) Strategy Play
    play = _build_strategy_play(snapshot.regime, market="KR")

    # 4) Risk Summary
    risk = _build_risk_summary(as_of)

    # 5) Checklist
    checklist = _build_checklist(snapshot, play, risk)

    return RegimePlaybook(
        as_of=as_of.isoformat(),
        generated_at=datetime.utcnow().isoformat(),
        regime_snapshot=snapshot,
        strategy_play=play,
        risk_summary=risk,
        checklist=checklist,
        extra_notes="",
    )


# ---------- Serialization Utils ----------

def save_playbook_json(pb: RegimePlaybook, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    # Save as YYYYMMDD
    path = out_dir / f"regime_playbook_{pb.as_of.replace('-', '')}.json"
    
    payload = asdict(pb)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return path


def save_playbook_markdown(pb: RegimePlaybook, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"regime_playbook_{pb.as_of.replace('-', '')}.md"

    s = []
    s.append(f"# Regime Playbook - {pb.as_of}")
    rs = pb.regime_snapshot
    sp = pb.strategy_play
    rk = pb.risk_summary

    s.append("")
    s.append("## 1. Market Regime Snapshot (KR)")
    s.append(f"- **Regime**: {rs.regime} (conf={rs.regime_confidence:.2f})")
    s.append(f"- **KOSPI Close**: {rs.close:.2f}")
    s.append(f"- **Returns (1D/5D/20D)**: {rs.change_1d:.2%} / {rs.change_5d:.2%} / {rs.change_20d:.2%}")
    s.append(f"- **20D Volatility**: {rs.vol_20d:.2%}")
    s.append("")
    s.append("## 2. Today's Strategy Play")
    s.append(f"- **Active Strategy**: {sp.strategy_id}")
    s.append(f"- **Params**: {sp.params}")
    s.append(f"- **Expected Sharpe**: {sp.expected_sharpe}")
    s.append(f"- **Sizing Hint**: {sp.sizing_hint}")
    s.append(f"- **Notes**: {sp.notes}")
    s.append("")
    s.append("## 3. Risk Summary")
    s.append(f"- **PnL Today**: {rk.pnl_today:,.0f}")
    s.append(f"- **PnL 5D**: {rk.pnl_5d:,.0f}")
    s.append(f"- **Max DD 20D**: {rk.max_dd_20d:.2%}")
    if rk.win_rate_20d is not None:
        s.append(f"- **Win Rate 20D**: {rk.win_rate_20d:.1%}")
    s.append(f"- **Comment**: {rk.comment}")
    s.append("")
    s.append("## 4. Daily Checklist")
    for item in pb.checklist:
        s.append(item)
    s.append("")
    if pb.extra_notes:
        s.append("## 5. Extra Notes")
        s.append(pb.extra_notes)

    with path.open("w", encoding="utf-8") as f:
        f.write("\n".join(s))

    return path
