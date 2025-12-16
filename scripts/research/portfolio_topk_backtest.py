# scripts/research/portfolio_topk_backtest.py
from __future__ import annotations

import sys
import argparse
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT))

# Ensure garam_core is importable
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from garam_core.strategy.registry import discover_strategies
from garam_core.research.pulse.load_data import load_minute_data, enhance_features


def _compute_score(df: pd.DataFrame, lookback_ev: int, vol_lookback: int) -> pd.Series:
    """
    최소/강력 점수:
      pulse_amp = rolling_mean(abs(1-bar return), lookback_ev)
      vol_spike = volume / rolling_mean(volume, vol_lookback)
      score = pulse_amp * vol_spike
    """
    close = df["close"]
    r1_abs = close.pct_change().abs()
    pulse_amp = r1_abs.rolling(lookback_ev).mean()

    if "volume" in df.columns:
        vol_ma = df["volume"].rolling(vol_lookback).mean()
        vol_spike = (df["volume"] / vol_ma).replace([np.inf, -np.inf], np.nan)
    else:
        vol_spike = pd.Series(1.0, index=df.index)

    score = (pulse_amp * vol_spike).fillna(0.0)
    return score


def _align_prices(dfs: Dict[str, pd.DataFrame]) -> Tuple[pd.DatetimeIndex, Dict[str, pd.Series]]:
    """
    심볼별 close를 시간축으로 outer-join 정렬.
    """
    closes = {}
    for sym, df in dfs.items():
        closes[sym] = df["close"].copy()

    idx = pd.Index(sorted(set().union(*[s.index for s in closes.values()])))
    idx = pd.DatetimeIndex(idx)

    aligned = {}
    for sym, s in closes.items():
        aligned[sym] = s.reindex(idx).ffill()  # research 용: ffill (장중 공백 최소화)
    return idx, aligned


def _align_series(index: pd.DatetimeIndex, series_map: Dict[str, pd.Series], fill_value=0.0) -> Dict[str, pd.Series]:
    out = {}
    for sym, s in series_map.items():
        out[sym] = s.reindex(index).fillna(fill_value)
    return out


def _build_topk_weights(
    signals: Dict[str, pd.Series],
    scores: Dict[str, pd.Series],
    k: int,
    mode: str = "equal",
    replace_threshold: float = 1.2,
    prev_selected: List[str] | None = None,
    t: int | None = None,
) -> Tuple[Dict[str, float], List[str]]:
    """
    t 시점에서 Top-K 선택 및 가중치 산출.
    - mode="equal": 선택된 종목 동일가중
    - mode="score": 점수 비례 가중(음수/0 제거)
    - replace_threshold: 이전 보유 대비 새 후보가 x배 이상 좋을 때만 교체(간단 히스테리시스)
    """
    candidates = []
    for sym, sig in signals.items():
        s = float(sig.iloc[t])
        if s == 0:
            continue
        sc = float(scores[sym].iloc[t])
        candidates.append((sym, s, sc))

    # 신호가 없는 경우: 공백
    if not candidates:
        return {}, []

    # 점수 기준 정렬
    candidates.sort(key=lambda x: x[2], reverse=True)

    selected = [c[0] for c in candidates[:k]]

    # 히스테리시스(선택적): 이전 선택이 있고, 교체가 불필요하게 잦으면 비용 증가
    if prev_selected:
        # 이전 선택 종목 점수 평균 vs 새 선택 평균 비교
        prev_scores = [float(scores[s].iloc[t]) for s in prev_selected if s in scores]
        new_scores = [float(scores[s].iloc[t]) for s in selected if s in scores]
        if prev_scores and new_scores:
            prev_mean = np.mean(prev_scores)
            new_mean = np.mean(new_scores)
            # 새 평균이 충분히 우월하지 않으면 유지(교체 억제)
            if prev_mean > 0 and (new_mean / prev_mean) < replace_threshold:
                selected = prev_selected

    # 가중치 산출
    weights = {}
    if mode == "equal":
        w = 1.0 / len(selected)
        for sym in selected:
            weights[sym] = w
    else:
        # score 가중: 0 이하 제거 후 정규화
        raw = np.array([max(float(scores[s].iloc[t]), 0.0) for s in selected], dtype=float)
        if raw.sum() <= 0:
            w = 1.0 / len(selected)
            for sym in selected:
                weights[sym] = w
        else:
            raw = raw / raw.sum()
            for sym, w in zip(selected, raw):
                weights[sym] = float(w)

    return weights, selected


def run_portfolio_topk(
    dfs: Dict[str, pd.DataFrame],
    strategy_name: str,
    k: int = 3,
    weight_mode: str = "equal",
    replace_threshold: float = 1.2,
    cost_per_trade: float = 0.0031,   # roundtrip
    lookback_ev: int = 30,
    vol_lookback: int = 30,
) -> Dict[str, object]:
    """
    멀티 심볼 Top-K 포트폴리오 백테스트(연구용).

    포지션 규약:
      - signal[t]는 "의도", 포지션은 signal.shift(1)로 반영 (보수적, look-ahead 방지)
      - 포트폴리오는 '선택된 종목'에만 가중치 배분하여 exposure를 구성
      - 비용: abs(weight_pos.diff()) * (cost/2) (engine_unified와 동일 규칙)
    """
    # 전략 로드
    strategies = discover_strategies()
    strat_map = {s.NAME: s for s in strategies}
    if strategy_name not in strat_map:
        raise ValueError(f"Strategy not found: {strategy_name}. Found: {list(strat_map.keys())}")

    # 심볼별 신호/점수 정렬
    sig_map = {}
    score_map = {}
    for sym, df in dfs.items():
        # Patch 호환을 위해 종목별로 전략 인스턴스 생성 (symbol 인자 전달)
        try:
            strat = strat_map[strategy_name](symbol=sym)
        except TypeError:
            strat = strat_map[strategy_name]()

        sig = strat.generate_signals(df).fillna(0).clip(-1, 1)
        sc = _compute_score(df, lookback_ev=lookback_ev, vol_lookback=vol_lookback)
        sig_map[sym] = sig
        score_map[sym] = sc

    sig_map = _align_series(idx, sig_map, fill_value=0.0)
    score_map = _align_series(idx, score_map, fill_value=0.0)

    # 포트폴리오 exposure(가중 포지션) 계산
    # pos_w[sym][t] = weight[sym] * direction(=signal at t-1)
    pos_w = {sym: pd.Series(0.0, index=idx) for sym in dfs.keys()}

    prev_selected: List[str] = []
    selected_hist = []

    for t in range(len(idx)):
        # t 시점의 선택은 "signal[t]"로 결정하되, 실제 포지션 적용은 shift(1)에서 반영됨
        weights, selected = _build_topk_weights(
            signals=sig_map,
            scores=score_map,
            k=k,
            mode=weight_mode,
            replace_threshold=replace_threshold,
            prev_selected=prev_selected,
            t=t,
        )
        selected_hist.append(selected)
        prev_selected = selected

        # direction은 signal[t]가 아니라 "signal[t]"은 의도 -> 실제 포지션은 t+1에서 적용되므로
        # 여기서는 일단 의도 weights만 기록해두고, 최종적으로 shift(1)하여 적용
        for sym in pos_w.keys():
            s = float(sig_map[sym].iloc[t])
            w = float(weights.get(sym, 0.0))
            pos_w[sym].iloc[t] = w * s

    # 실제 노출은 shift(1)
    pos_w_shift = {sym: s.shift(1).fillna(0.0) for sym, s in pos_w.items()}

    # 포트폴리오 수익률: sum_i (pos_w[i] * ret_i)
    port_gross = pd.Series(0.0, index=idx)

    for sym, close in close_map.items():
        ret = close.pct_change().fillna(0.0)
        port_gross += pos_w_shift[sym] * ret

    # 비용: 각 심볼 노출 변화량 기준 (합산)
    half = cost_per_trade / 2.0
    cost_series = pd.Series(0.0, index=idx)
    for sym, wpos in pos_w_shift.items():
        ch = wpos.diff().abs().fillna(abs(wpos.iloc[0]))
        cost_series += ch * half

    port_net = port_gross - cost_series
    equity = (1.0 + port_net).cumprod()

    # 성과 지표
    total_ret = float(equity.iloc[-1] - 1.0)
    running_max = equity.cummax()
    dd = (equity - running_max) / running_max
    mdd = float(dd.min())

    # 거래 횟수 근사치: 노출 변화 합(총 turnover)
    turnover = float(sum([pos_w_shift[sym].diff().abs().sum() for sym in pos_w_shift]))
    cost_paid_total = float(cost_series.sum())

    return {
        "strategy": strategy_name,
        "k": k,
        "weight_mode": weight_mode,
        "replace_threshold": replace_threshold,
        "roi": total_ret,
        "max_drawdown": mdd,
        "turnover": turnover,
        "cost_paid_total": cost_paid_total,
        "equity_curve": equity,
        "net_ret": port_net,
        "gross_ret": port_gross,
        "costs": cost_series,
        "selected_hist": selected_hist,  # 연구용(원하면 저장/분석)
    }


def save_outputs(res: Dict[str, object], out_dir: Path, tag: str):
    out_dir.mkdir(parents=True, exist_ok=True)

    # summary
    summary = pd.DataFrame([{
        "strategy": res["strategy"],
        "k": res["k"],
        "weight_mode": res["weight_mode"],
        "replace_threshold": res["replace_threshold"],
        "roi": res["roi"],
        "max_drawdown": res["max_drawdown"],
        "turnover": res["turnover"],
        "cost_paid_total": res["cost_paid_total"],
    }])
    csv_path = out_dir / f"portfolio_topk_summary_{tag}.csv"
    summary.to_csv(csv_path, index=False, encoding="utf-8-sig")

    # equity plot
    eq = res["equity_curve"]
    plt.figure()
    plt.plot(eq.index, eq.values)
    plt.title(f"Portfolio Top-K Equity | {tag}")
    plt.xlabel("Time")
    plt.ylabel("Equity")
    plt.tight_layout()
    fig_path = out_dir / f"portfolio_topk_equity_{tag}.png"
    plt.savefig(fig_path, dpi=150)
    plt.close()

    print(f"[OK] {csv_path}")
    print(f"[OK] {fig_path}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--universe", default="", help="Universe yaml (optional). If empty, use --symbols.")
    p.add_argument("--symbols", default="005930,000660", help="Comma symbols if universe not used.")
    p.add_argument("--data_dir", default=str(PROJECT_ROOT / "GARAM_Data/minute/kr"))

    p.add_argument("--strategy", default="regime_switch", help="Strategy NAME to drive signals.")
    p.add_argument("--k", type=int, default=3, help="Top-K selection count.")
    p.add_argument("--weight_mode", choices=["equal", "score"], default="equal")
    p.add_argument("--replace_threshold", type=float, default=1.2)

    p.add_argument("--cost_per_trade", type=float, default=0.0031)
    p.add_argument("--lookback_ev", type=int, default=30)
    p.add_argument("--vol_lookback", type=int, default=30)

    p.add_argument("--out_dir", default=str(PROJECT_ROOT / "reports" / "portfolio_topk"))
    args = p.parse_args()

    # 심볼 리스트
    symbols = [s.strip() for s in args.symbols.split(",") if s.strip()]

    # 데이터 로드
    dfs = {}
    for sym in symbols:
        try:
            df = load_minute_data(sym, args.data_dir)
            df = enhance_features(df)
            dfs[sym] = df
            print(f"[DATA] {sym}: {len(df)} bars")
        except Exception as e:
            print(f"[SKIP] {sym}: load failed: {e}")

    if len(dfs) < 2:
        raise RuntimeError("Need at least 2 symbols loaded for portfolio top-k test.")

    res = run_portfolio_topk(
        dfs=dfs,
        strategy_name=args.strategy,
        k=args.k,
        weight_mode=args.weight_mode,
        replace_threshold=args.replace_threshold,
        cost_per_trade=args.cost_per_trade,
        lookback_ev=args.lookback_ev,
        vol_lookback=args.vol_lookback,
    )

    tag = f"{args.strategy}_K{args.k}_{args.weight_mode}_rt{args.replace_threshold}"
    save_outputs(res, Path(args.out_dir), tag)


if __name__ == "__main__":
    main()
