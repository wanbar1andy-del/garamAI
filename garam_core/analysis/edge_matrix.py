from __future__ import annotations
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional

# --- 1. Regime Definitions (Micro-Regime v1) ---

REGIMES = ["TREND_UP", "TREND_DOWN", "CHOP_HIGHVOL", "CHOP_LOWVOL", "PANIC"]

def ema(s: pd.Series, span: int) -> pd.Series:
    return s.ewm(span=span, adjust=False).mean()

def true_range(high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
    prev_close = close.shift(1)
    tr1 = (high - low).abs()
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()
    return pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

def efficiency_ratio(close: pd.Series, L: int) -> pd.Series:
    net = (close - close.shift(L)).abs()
    denom = close.diff().abs().rolling(L).sum()
    er = net / denom.replace(0, np.nan)
    return er.clip(lower=0, upper=1)

def return_zscore(close: pd.Series, L: int) -> pd.Series:
    ret = np.log(close / close.shift(1))
    mu = ret.rolling(L).mean()
    sd = ret.rolling(L).std(ddof=0)
    
    # Safe Z-score: if std is very small, z is 0
    z = (ret - mu) / sd.replace(0, np.nan)
    z = z.fillna(0.0) 
    # USER RULE: std < 1e-8 -> z=0
    mask_low = sd < 1e-8
    z[mask_low] = 0.0
    return z

def micro_regime_v1(
    df: pd.DataFrame,
    lookback_bars: int = 120,
    ema_fast_span: int = 20,
    ema_slow_span: int = 120,
    slope_th: float = 0.0015,
    er_trend_th: float = 0.35,
    atr_span: int = 120,
    atr_hi_th: float = 0.004,
    atr_lo_th: float = 0.002,
    panic_z_th: float = 3.0,
) -> pd.Series:
    """
    df columns: close (required), high/low (recommended)
    returns: pd.Series of regime labels (string)
    """
    # Enforce time-series order (Oldest to Newest)
    df = df.sort_index(ascending=True)
    
    if "close" not in df.columns:
        raise ValueError("df must contain 'close'")
    close = df["close"].astype(float)

    # high/low fallback
    if "high" in df.columns and "low" in df.columns:
        high = df["high"].astype(float)
        low = df["low"].astype(float)
    else:
        high = close
        low = close

    ema_fast = ema(close, ema_fast_span)
    ema_slow = ema(close, ema_slow_span)
    slope = (ema_fast - ema_slow) / ema_slow.replace(0, np.nan)

    er = efficiency_ratio(close, lookback_bars)

    tr = true_range(high, low, close)
    atr = ema(tr, atr_span)
    atr_pct = atr / close.replace(0, np.nan)

    z = return_zscore(close, lookback_bars)
    panic = z.abs() >= panic_z_th

    trend_up = slope > slope_th
    trend_down = slope < -slope_th
    trend_ok = er >= er_trend_th

    regime = pd.Series(index=df.index, dtype="object")

    # priority 1: PANIC
    regime.loc[panic] = "PANIC"

    # priority 2: trend regimes
    mask_up = (~panic) & trend_up & trend_ok
    mask_dn = (~panic) & trend_down & trend_ok
    regime.loc[mask_up] = "TREND_UP"
    regime.loc[mask_dn] = "TREND_DOWN"

    # priority 3: chop regimes
    remain = regime.isna()
    chop_hi = remain & (atr_pct >= atr_hi_th)
    chop_lo = remain & (atr_pct < atr_hi_th)
    regime.loc[chop_hi] = "CHOP_HIGHVOL"
    regime.loc[chop_lo] = "CHOP_LOWVOL"

    # fill any remaining (edge NaNs in early bars)
    regime = regime.fillna("CHOP_LOWVOL")

    return regime


# --- 2. Net Expectancy / by_regime Aggregation ---

def expectancy_metrics(returns_net: np.ndarray, returns_gross: np.ndarray, costs: np.ndarray) -> dict:
    trades = int(len(returns_net))
    if trades == 0:
        return {
            "trades": 0, "win_rate": 0.0,
            "avg_win": 0.0, "avg_loss": 0.0,
            "cost_per_trade_avg": 0.0,
            "expectancy_gross": 0.0, "expectancy_net": 0.0,
            "gross_pnl_total": 0.0, "net_pnl_total": 0.0, "cost_total": 0.0,
            "sqn_score": 0.0 # Added Key for compatibility with report_writer
        }
    wins = returns_gross[returns_gross > 0]
    losses = returns_gross[returns_gross <= 0]
    win_rate = float((returns_gross > 0).mean())
    avg_win = float(wins.mean()) if len(wins) else 0.0
    avg_loss = float(abs(losses.mean())) if len(losses) else 0.0  # positive magnitude

    cost_avg = float(np.mean(costs)) if len(costs) else 0.0

    expectancy_gross = win_rate * avg_win - (1.0 - win_rate) * avg_loss
    expectancy_net = expectancy_gross - cost_avg
    
    # SQN Calculation (based on net returns)
    # SQN = sqrt(N) * (mean / std)
    # Safe SQN: guard against std close to 0
    std_net = np.std(returns_net)
    if std_net < 1e-6:
        sqn = 0.0
    else:
        sqn = (np.sqrt(trades) * (np.mean(returns_net) / std_net))

    return {
        "trades": trades,
        "win_rate": win_rate,
        "avg_win": avg_win,
        "avg_loss": avg_loss,
        "cost_per_trade_avg": cost_avg,
        "expectancy_gross": float(expectancy_gross),
        "expectancy_net": float(expectancy_net),
        "gross_pnl_total": float(np.sum(returns_gross)),
        "net_pnl_total": float(np.sum(returns_net)),
        "cost_total": float(np.sum(costs)),
        "sqn_score": float(sqn)
    }

def attach_regime_to_trades(trades_df: pd.DataFrame, bar_regime: pd.Series) -> pd.DataFrame:
    """
    trades_df must have entry_time (datetime-like index or column).
    bar_regime: index aligned with bar timestamps (Assumed KST aware or naive-KST).
    """
    if "entry_time" not in trades_df.columns:
        raise ValueError("trades_df must contain entry_time")
        
    t = trades_df.copy()
    
    # Normalize Entry Time to KST
    # 1. Force datetime
    t['entry_time'] = pd.to_datetime(t['entry_time'])
    
    # 2. Localize/Convert to match Bar Data (KST)
    # Rules:
    # - If trade is naive -> assume UTC (Replay default) -> Convert to KST
    # - If trade is tz-aware -> Convert to KST
    # - If bar is naive -> assume KST (Loader default) -> Localize to KST for matching?
    #   User instruction: "minute_df.index = pd.to_datetime(minute_df.index).tz_localize('Asia/Seoul')"
    #   Better to handle bar_regime normalization OUTSIDE or assume it is normalized.
    #   BUT user gave specific snippet for THIS function or caller.
    #   Let's implement the matching logic here based on bar_regime's index.
    
    # Check bar index tz
    bar_tz = bar_regime.index.tz
    
    # Align Trade Time
    if t['entry_time'].dt.tz is None:
        # Naive -> Assume UTC (standard Replay) -> Convert to KST ('Asia/Seoul')
        # Wait, if Replay returns Naive UTC, we must localize UTC then convert
        t['entry_time_k'] = t['entry_time'].dt.tz_localize("UTC").dt.tz_convert("Asia/Seoul")
    else:
        # Aware -> Convert to Asia/Seoul
        t['entry_time_k'] = t['entry_time'].dt.tz_convert("Asia/Seoul")

    # Align Bar Index (if naive, assume map is KST)
    # We can't easily mod bar_regime index here without re-indexing.
    # If bar_regime index is naive, we assume it is KST.
    # If bar_regime index is aware, we match properly.
    
    # Enforce monotonic increasing index for ffill
    bar_regime = bar_regime.sort_index()

    # User Patch pattern:
    # Reindex using floor('T') to match minute bars
    
    # Prepare mapping index
    map_index = t['entry_time_k']
    if bar_tz is None:
        # If bars are naive, remove tz from trade times (after converting to KST wall time)
        map_index = map_index.dt.tz_localize(None)
    
    # nearest backward match (entry_time <= bar_time)
    # reindex with method='ffill' works if bar_regime index is sorted
    regime = bar_regime.reindex(map_index.dt.floor("T"), method="ffill")
    
    t["regime"] = regime.values
    t["regime"] = t["regime"].fillna("UNCERTAIN")
    
    # Cleanup temp col
    if 'entry_time_k' in t.columns:
        del t['entry_time_k']
        
    return t

def build_by_regime(trades_df: pd.DataFrame, bar_regime: pd.Series) -> dict:
    """
    Returns dictionary keyed by regime name containing metrics.
    Also injects 'bars' count per regime for reference.
    """
    out = {}
    
    # Count bars
    bar_counts = bar_regime.value_counts().to_dict()
    
    # Group trades
    # Make sure we use the same regime keys
    for reg in REGIMES + ["UNCERTAIN"]:
        out[reg] = {
            "bars": int(bar_counts.get(reg, 0)),
            "trades": 0,
            "expectancy_net": 0.0,
            # Initialize other keys to 0/N/A or rely on metrics valid check
            # but let's default to empty structural dict
            **expectancy_metrics(np.array([]), np.array([]), np.array([])),
            "tags": []
        }

    # Populate with actual data
    if "regime" in trades_df:
        for reg, g in trades_df.groupby("regime"):
            net = g["net_return"].to_numpy(dtype=float)
            gross = g["gross_return"].to_numpy(dtype=float)
            cost = g["cost_return"].to_numpy(dtype=float)
            
            metrics = expectancy_metrics(net, gross, cost)
            
            # Merge with default structure (preserving 'bars')
            out[str(reg)].update(metrics)
            
    return out

def rolling_degradation(net_returns: pd.Series, window_trades: int = 200) -> dict:
    """
    트레이드 순서 기준으로 rolling expectancy_net의 '초기80% vs 마지막20%' 붕괴 측정
    """
    if len(net_returns) < max(50, window_trades):
        return {
            "rolling_expectancy_net_p50_first80": 0.0, # changed from None for strict float schema
            "rolling_expectancy_net_p50_last20": 0.0,
            "drop_ratio": 0.0,
            "flag_structural_break": False
        }
    roll = net_returns.rolling(window_trades).mean()
    n = len(roll.dropna())
    if n == 0:
        return {
            "rolling_expectancy_net_p50_first80": 0.0,
            "rolling_expectancy_net_p50_last20": 0.0,
            "drop_ratio": 0.0,
            "flag_structural_break": False
        }
    roll = roll.dropna().reset_index(drop=True)
    cut = int(n * 0.8)
    first80 = float(roll.iloc[:cut].median()) if cut > 0 else 0.0
    last20 = float(roll.iloc[cut:].median()) if cut < n else 0.0
    
    if first80 == 0:
        if last20 == 0:
             drop_ratio = 0.0
        else:
             drop_ratio = 1.0 # arbitrary large change if base is 0
    else:
        drop_ratio = (last20 - first80) / abs(first80)
        
    flag = drop_ratio < -0.5  # 마지막 20%에서 중위 기대값이 50% 이상 악화
    return {
        "rolling_expectancy_net_p50_first80": first80,
        "rolling_expectancy_net_p50_last20": last20,
        "drop_ratio": float(drop_ratio),
        "flag_structural_break": bool(flag)
    }


# --- 3. Collapse Tags ---

def collapse_tags(overall: dict, by_regime: dict, degradation: dict, thresholds: dict) -> List[str]:
    tags = []

    # CRASH_COLLAPSE
    mdd = overall.get("mdd")
    if mdd is not None and mdd <= thresholds.get("crash_mdd", -0.40):
        tags.append("CRASH_COLLAPSE")

    exp_net = overall.get("expectancy_net", 0.0)
    exp_gross = overall.get("expectancy_gross", 0.0)
    min_edge_th = thresholds.get("guard_min_threshold", 0.0005)

    # COST_DOMINATED: Positive Gross Logic (Edge exists) but Negative Net (Cost kills it)
    if exp_gross > 0 and exp_net < 0:
        tags.append("COST_DOMINATED")

    # Tier-0 Guard: NEGATIVE_EDGE
    # Significant negative expectancy
    if exp_net < 0 and abs(exp_net) >= min_edge_th:
        tags.append("NEGATIVE_EDGE")

    # Tier-0 Guard: NO_EDGE
    # Expectancy is practically zero (within noise)
    if abs(exp_net) < min_edge_th:
        tags.append("NO_EDGE")

    # OVERTRADING
    tpd = overall.get("trades_per_day")
    if tpd is not None and tpd > thresholds.get("overtrade_trades_per_day", 20) and exp_net < 0:
        tags.append("OVERTRADING")

    # REGIME_MISMATCH
    exps = [v.get("expectancy_net") for v in by_regime.values() if v.get("trades", 0) >= thresholds.get("min_trades_per_regime", 30)]
    if len(exps) >= 2:
        if (max(exps) - min(exps)) >= thresholds.get("regime_spread_exp_net", 0.0015):
            tags.append("REGIME_MISMATCH")

    # SIGNAL_NOISE
    win_rate = overall.get("win_rate", 0.0)
    if win_rate < thresholds.get("signal_noise_win_rate", 0.35):
        avg_w = overall.get("avg_win", 0.0)
        avg_l = overall.get("avg_loss", 0.0)
        if avg_w < thresholds.get("signal_noise_payout_mult", 1.5) * avg_l:
            tags.append("SIGNAL_NOISE")

    # STRUCTURAL_BREAK
    if degradation.get("flag_structural_break"):
        tags.append("STRUCTURAL_BREAK")

    return tags

# --- 4. Main Analyzer Class for Convenience ---

class EdgeAnalyzer:
    def __init__(self, thresholds: Optional[Dict[str, Any]] = None):
        self.thresholds = thresholds or {
            "crash_mdd": -0.40,
            "overtrade_trades_per_day": 20,
            "min_trades_per_regime": 30,
            "regime_spread_exp_net": 0.0015,
            "signal_noise_win_rate": 0.35,
            "signal_noise_payout_mult": 1.5
        }

    def analyze(self, trades_df: pd.DataFrame, minute_df: pd.DataFrame, extra_kpis: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Full orchestration.
        trades_df columns: entry_time, gross_return, cost_return, net_return (calculated if missing?)
        """
        # 1. Calc Regime
        regimes = micro_regime_v1(minute_df)
        
        # 2. Attach Regime
        if trades_df.empty:
            return {}
            
        t_df = attach_regime_to_trades(trades_df, regimes)
        
        # 3. Overall Metrics
        net = t_df["net_return"].to_numpy(dtype=float)
        gross = t_df["gross_return"].to_numpy(dtype=float)
        costs = t_df["cost_return"].to_numpy(dtype=float)
        
        overall = expectancy_metrics(net, gross, costs)
        
        # Inject TPD and MDD into overall for tag checks
        if extra_kpis:
            overall.update(extra_kpis) # e.g. mdd, trades_per_day
            
        # 4. By Regime
        by_regime = build_by_regime(t_df, regimes)
        
        # 5. Degradation
        deg = rolling_degradation(t_df["net_return"])
        
        # 6. Tags
        tags = collapse_tags(overall, by_regime, deg, self.thresholds)
        
        return {
            "thresholds": self.thresholds,
            "overall": overall,
            "by_regime": by_regime,
            "degradation": deg,
            "collapse_tags": tags
        }
