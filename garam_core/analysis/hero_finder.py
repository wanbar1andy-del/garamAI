# garam_core/analysis/hero_finder.py
"""
Phase 21-B: 히어로 탐색 엔진 (Overnight 3-Tier + Gap NaN Fix)

BUG FIX: Gap 통계 실패 시 NaN 반환 (0.0 버그 수정)
PERF: 2-pass 스캔 지원 (Top-K만 Overnight/Gap 계산)
"""
from __future__ import annotations

import warnings
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Literal, Optional

import numpy as np
import pandas as pd

from ..fastlane.feature_store import FeatureStore
from ..fastlane.policy_eval import PolicyEval, PolicyParams
from .edge_decomposer import EdgeDecomposer


@dataclass(frozen=True)
class HeroCriteria:
    """히어로 자격 요건"""
    min_trades: int = 30
    min_expectancy_net: float = 0.001
    min_win_rate: float = 0.50
    max_tail_ratio: float = 0.35
    max_tpd: float = 50.0


@dataclass(frozen=True)
class OvernightCriteriaStrict:
    """오버나잇 STRICT (주력 복리용)"""
    min_overnight_trades: int = 20
    min_overnight_expectancy: float = 0.0008
    max_overnight_tail: float = 0.30
    min_overnight_p10: float = -0.006
    max_overnight_loss: float = -0.02
    max_gap_p10: float = -0.008
    max_gap_loss: float = -0.025
    min_gap_n: int = 15  # STRICT는 최소 15일 갭 필요


@dataclass(frozen=True)
class OvernightCriteriaSoft:
    """오버나잇 SOFT (소액 시험용)"""
    min_overnight_trades: int = 5
    min_overnight_expectancy: float = 0.0
    max_overnight_tail: float = 0.45
    min_overnight_p10: float = -0.015
    max_overnight_loss: float = -0.05
    max_gap_p10: float = -0.020
    max_gap_loss: float = -0.06
    min_gap_n: int = 5  # SOFT는 최소 5일 갭 필요


@dataclass(frozen=True)
class HeroProbe:
    """탐색용 전략"""
    name: str
    params: PolicyParams
    description: str = ""


@dataclass
class HeroMetadata:
    """히어로 스캔 결과"""
    symbol: str
    probe_name: str

    # Full Session
    expectancy_net: float
    win_rate: float
    tail_ratio: float
    trades: int
    tpd: float
    total_return: float
    p10_return: float
    p90_return: float
    max_loss_trade: float

    # Open Window
    open_window_expectancy: float
    open_window_win_rate: float
    open_window_trades: int

    # Overnight Metrics
    overnight_expectancy_net: float
    overnight_win_rate: float
    overnight_tail_ratio: float
    overnight_trades: int
    overnight_p10_return: float
    overnight_max_loss: float
    overnight_score: float

    # Gap Statistics (FIX: NaN for invalid)
    gap_p10: float
    gap_max_loss: float
    gap_std: float
    gap_n: int  # 표본 수 (NEW)

    # Overnight Tier
    overnight_tier: Literal["NONE", "SOFT", "STRICT"]

    # Hero Flags
    is_hero: bool
    hero_score: float
    reason_tags: List[str]

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["reason_tags"] = ",".join(self.reason_tags)
        return d


class HeroFinder:
    """히어로 탐색 엔진 (2-Pass 지원)"""

    def __init__(self, feature_store: FeatureStore):
        self.fs = feature_store

    def scan(
        self,
        universe: List[str],
        probe: HeroProbe,
        criteria: HeroCriteria,
        overnight_strict: OvernightCriteriaStrict = None,
        overnight_soft: OvernightCriteriaSoft = None,
        window_days: int = 30,
        open_window_start: str = "09:00",
        open_window_end: str = "10:00",
        force_recompute_features: bool = False,
        two_pass: bool = False,
        top_k: int = 50,
    ) -> List[HeroMetadata]:
        """
        2-Pass 스캔:
        - Pass 1: Full Session만 계산 (가벼움)
        - Pass 2: Top-K에 대해서만 Overnight/Gap 계산 (무거움)
        """

        if overnight_strict is None:
            overnight_strict = OvernightCriteriaStrict()
        if overnight_soft is None:
            overnight_soft = OvernightCriteriaSoft()

        print("\n[HeroFinder] 히어로 스캔 시작")
        print(f"  대상: {len(universe)}개 | 프로브: {probe.name}")
        print(f"  윈도우: 최근 {window_days}일")
        if two_pass:
            print(f"  2-Pass 모드: Top-{top_k}만 Overnight/Gap 계산")

        results: List[HeroMetadata] = []

        # Pass 1: Full Session (모든 종목)
        print("\n[Pass 1] Full Session 평가...")
        for i, symbol in enumerate(universe, start=1):
            if i % 50 == 0:
                print(f"  진행: {i}/{len(universe)}")

            try:
                meta = self._evaluate_symbol_pass1(
                    symbol=symbol,
                    probe=probe,
                    criteria=criteria,
                    window_days=window_days,
                    force_recompute=force_recompute_features,
                )
                results.append(meta)
            except Exception as e:
                warnings.warn(f"[Pass1] {symbol} 실패: {e}")
                continue

        # Sort by hero_score
        results.sort(key=lambda x: x.hero_score, reverse=True)

        if not two_pass:
            # Single-pass: 모든 종목에 Overnight/Gap 계산 (기존 방식)
            print("\n[Pass 2] Overnight/Gap 평가 (전체)...")
            for i, meta in enumerate(results, start=1):
                if i % 50 == 0:
                    print(f"  진행: {i}/{len(results)}")
                try:
                    self._evaluate_overnight_gap(
                        meta, probe.params, overnight_strict, overnight_soft,
                        window_days, open_window_start, open_window_end,
                        force_recompute_features
                    )
                except Exception as e:
                    warnings.warn(f"[Pass2] {meta.symbol} 실패: {e}")
        else:
            # Two-pass: 히어로만 Top-K 선택 (FIX: 비히어로 제외)
            heroes_only = [r for r in results if r.is_hero]
            top_k_results = heroes_only[:top_k]
            print(f"\n[Pass 2] Overnight/Gap 평가 (히어로 Top-{len(top_k_results)})...")
            for i, meta in enumerate(top_k_results, start=1):
                if i % 10 == 0:
                    print(f"  진행: {i}/{len(top_k_results)}")
                try:
                    self._evaluate_overnight_gap(
                        meta, probe.params, overnight_strict, overnight_soft,
                        window_days, open_window_start, open_window_end,
                        force_recompute_features
                    )
                except Exception as e:
                    warnings.warn(f"[Pass2] {meta.symbol} 실패: {e}")

        heroes = [r for r in results if r.is_hero]
        strict = [r for r in results if r.overnight_tier == "STRICT"]
        soft = [r for r in results if r.overnight_tier == "SOFT"]
        
        print(f"\n[HeroFinder] 완료: 히어로 {len(heroes)} | ON-STRICT {len(strict)} | ON-SOFT {len(soft)}")

        return results

    def _evaluate_symbol_pass1(
        self,
        symbol: str,
        probe: HeroProbe,
        criteria: HeroCriteria,
        window_days: int,
        force_recompute: bool,
    ) -> HeroMetadata:
        """Pass 1: Full Session만 평가"""

        df_full = self.fs.get_features(symbol, force_recompute=force_recompute)
        if df_full is None or df_full.empty:
            return self._empty_hero(symbol, probe.name, reason="NO_DATA")

        # Window cutoff
        ts = pd.to_datetime(df_full["date"], errors="coerce")
        last_ts = ts.max()
        if pd.isna(last_ts):
            return self._empty_hero(symbol, probe.name, reason="BAD_TS")

        cutoff = last_ts - pd.Timedelta(days=window_days)
        df_full = df_full.loc[ts >= cutoff].copy()
        if df_full.empty:
            return self._empty_hero(symbol, probe.name, reason="NO_WINDOW")

        # Full Session
        pe_full = PolicyEval(df_full)
        res_full = pe_full.evaluate(probe.params)
        edge_full = EdgeDecomposer.analyze_trades(res_full.get("trades_detail", []), timeframe_seconds=60)

        exp_net = float(edge_full.get("expectancy_net", 0.0))
        win_rate = float(edge_full.get("win_rate", 0.0))
        tail = float(edge_full.get("loss_tail_ratio", 0.0))
        trades = int(res_full.get("trades", 0))
        tpd = float(res_full.get("tpd", 0.0))
        total_ret = float(res_full.get("total_return", 0.0))

        trades_detail = res_full.get("trades_detail", []) or []
        returns = [t.get("return_net", 0.0) for t in trades_detail] if trades_detail else []
        if returns:
            p10 = float(np.percentile(returns, 10))
            p90 = float(np.percentile(returns, 90))
            max_loss = float(np.min(returns))
        else:
            p10, p90, max_loss = 0.0, 0.0, 0.0

        is_hero = self._check_hero(exp_net, win_rate, tail, trades, tpd, criteria)
        hero_score = exp_net * win_rate * (1.0 - tail)

        tags = []
        if is_hero:
            tags.append("히어로")
        else:
            tags.append("불합격")

        if exp_net > 0.002: tags.append("고기대값")
        if win_rate > 0.60: tags.append("고승률")
        if tail < 0.25 and trades >= criteria.min_trades: tags.append("저꼬리")

        return HeroMetadata(
            symbol=symbol,
            probe_name=probe.name,
            expectancy_net=exp_net,
            win_rate=win_rate,
            tail_ratio=tail,
            trades=trades,
            tpd=tpd,
            total_return=total_ret,
            p10_return=p10,
            p90_return=p90,
            max_loss_trade=max_loss,
            open_window_expectancy=0.0,
            open_window_win_rate=0.0,
            open_window_trades=0,
            overnight_expectancy_net=0.0,
            overnight_win_rate=0.0,
            overnight_tail_ratio=0.0,
            overnight_trades=0,
            overnight_p10_return=0.0,
            overnight_max_loss=0.0,
            overnight_score=0.0,
            gap_p10=np.nan,
            gap_max_loss=np.nan,
            gap_std=np.nan,
            gap_n=0,
            overnight_tier="NONE",
            is_hero=is_hero,
            hero_score=hero_score,
            reason_tags=tags,
        )

    def _evaluate_overnight_gap(
        self,
        meta: HeroMetadata,
        probe_params: PolicyParams,  # FIX: probe params 전달
        overnight_strict: OvernightCriteriaStrict,
        overnight_soft: OvernightCriteriaSoft,
        window_days: int,
        open_window_start: str,
        open_window_end: str,
        force_recompute: bool,
    ):
        """Pass 2: Overnight/Gap 평가 (in-place 수정)"""
        
        # FIX: 히어로 아니면 Pass2 불필요
        if not meta.is_hero:
            return

        df_full = self.fs.get_features(meta.symbol, force_recompute=force_recompute)
        if df_full is None or df_full.empty:
            return

        ts = pd.to_datetime(df_full["date"], errors="coerce")
        last_ts = ts.max()
        if pd.isna(last_ts):
            return

        cutoff = last_ts - pd.Timedelta(days=window_days)
        df_full = df_full.loc[ts >= cutoff].copy()
        if df_full.empty:
            return

        # Open Window (FIX: probe_params 사용)
        df_open = self._filter_open_window(df_full, open_window_start, open_window_end)
        if not df_open.empty:
            pe_open = PolicyEval(df_open)
            res_open = pe_open.evaluate(probe_params)
            edge_open = EdgeDecomposer.analyze_trades(res_open.get("trades_detail", []), timeframe_seconds=60)
            meta.open_window_expectancy = float(edge_open.get("expectancy_net", 0.0))
            meta.open_window_win_rate = float(edge_open.get("win_rate", 0.0))
            meta.open_window_trades = int(res_open.get("trades", 0))

        # Full Session re-evaluate (FIX: probe_params 사용)
        pe_full = PolicyEval(df_full)
        res_full = pe_full.evaluate(probe_params)
        trades_detail = res_full.get("trades_detail", []) or []
        overnight_trades = self._extract_overnight_trades(trades_detail)
        
        if len(overnight_trades) > 0:
            edge_on = EdgeDecomposer.analyze_trades(overnight_trades, timeframe_seconds=60)
            meta.overnight_expectancy_net = float(edge_on.get("expectancy_net", 0.0))
            meta.overnight_win_rate = float(edge_on.get("win_rate", 0.0))
            meta.overnight_tail_ratio = float(edge_on.get("loss_tail_ratio", 0.0))
            meta.overnight_trades = len(overnight_trades)
            
            on_returns = [t.get("return_net", 0.0) for t in overnight_trades]
            meta.overnight_p10_return = float(np.percentile(on_returns, 10)) if on_returns else 0.0
            meta.overnight_max_loss = float(np.min(on_returns)) if on_returns else 0.0
            meta.overnight_score = meta.overnight_expectancy_net * meta.overnight_win_rate * (1.0 - meta.overnight_tail_ratio)

        # Gap Stats (FIX: NaN for invalid)
        gap_stats = self._calculate_gap_stats(df_full)
        meta.gap_p10 = gap_stats["gap_p10"]
        meta.gap_max_loss = gap_stats["gap_max_loss"]
        meta.gap_std = gap_stats["gap_std"]
        meta.gap_n = gap_stats["gap_n"]

        # Tier
        meta.overnight_tier = self._determine_overnight_tier(
            meta, overnight_strict, overnight_soft
        )

        # Tags update
        if meta.overnight_tier == "STRICT":
            meta.reason_tags.append("ON-STRICT")
        elif meta.overnight_tier == "SOFT":
            meta.reason_tags.append("ON-SOFT")

    def _extract_overnight_trades(self, trades_detail: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """오버나잇 거래 추출"""
        overnight = []
        for t in trades_detail:
            entry_ts_str = t.get("entry_ts")
            exit_ts_str = t.get("exit_ts")
            
            if not entry_ts_str or not exit_ts_str:
                continue
            
            try:
                entry_ts = pd.to_datetime(entry_ts_str, utc=True)
                exit_ts = pd.to_datetime(exit_ts_str, utc=True)
                
                entry_kst = entry_ts.tz_convert("Asia/Seoul")
                exit_kst = exit_ts.tz_convert("Asia/Seoul")
                
                if entry_kst.date() != exit_kst.date():
                    overnight.append(t)
            except:
                continue
        
        return overnight

    def _calculate_gap_stats(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        갭 통계 계산 (FIX: 실패 시 NaN 반환)
        """
        # FIX: Column guard
        required = {"open", "close", "date"}
        if not required.issubset(df.columns):
            return {"gap_p10": np.nan, "gap_max_loss": np.nan, "gap_std": np.nan, "gap_n": 0}
        
        try:
            df = df.copy()
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
            
            if getattr(df["date"].dt, "tz", None) is None:
                df["date"] = df["date"].dt.tz_localize("Asia/Seoul", ambiguous="infer", nonexistent="shift_forward")
            df["date"] = df["date"].dt.tz_convert("Asia/Seoul")
            
            df["day"] = df["date"].dt.date
            daily_close = df.groupby("day")["close"].last()
            daily_open = df.groupby("day")["open"].first()
            
            daily_close_shifted = daily_close.shift(1)
            gap_returns = (daily_open / daily_close_shifted - 1.0).dropna()
            
            gap_n = int(len(gap_returns))

            # FIX: 최소 표본 요구
            if gap_n >= 5:
                gap_p10 = float(np.percentile(gap_returns, 10))
                gap_max_loss = float(np.min(gap_returns))
                gap_std = float(np.std(gap_returns))
            else:
                gap_p10, gap_max_loss, gap_std = np.nan, np.nan, np.nan
                
        except Exception as e:
            warnings.warn(f"Gap 통계 실패: {e}")
            gap_p10, gap_max_loss, gap_std = np.nan, np.nan, np.nan
            gap_n = 0
        
        return {
            "gap_p10": gap_p10,
            "gap_max_loss": gap_max_loss,
            "gap_std": gap_std,
            "gap_n": gap_n
        }

    def _determine_overnight_tier(
        self,
        meta: HeroMetadata,
        strict: OvernightCriteriaStrict,
        soft: OvernightCriteriaSoft
    ) -> Literal["NONE", "SOFT", "STRICT"]:
        """Tier 판정 (FIX: NaN 체크)"""
        
        if not meta.is_hero:
            return "NONE"
        
        # FIX: NaN이면 gap 통계 신뢰 불가
        gap_valid = (
            np.isfinite(meta.gap_p10) and 
            np.isfinite(meta.gap_max_loss) and
            meta.gap_n >= soft.min_gap_n
        )
        
        # STRICT
        if meta.overnight_trades >= strict.min_overnight_trades:
            if (meta.overnight_expectancy_net >= strict.min_overnight_expectancy and
                meta.overnight_tail_ratio <= strict.max_overnight_tail and
                meta.overnight_p10_return >= strict.min_overnight_p10 and
                meta.overnight_max_loss >= strict.max_overnight_loss):
                
                # Gap 추가 체크
                if gap_valid and meta.gap_n >= strict.min_gap_n:
                    if (meta.gap_p10 >= strict.max_gap_p10 and
                        meta.gap_max_loss >= strict.max_gap_loss):
                        return "STRICT"
        
        # SOFT
        if meta.overnight_trades >= soft.min_overnight_trades:
            if (meta.overnight_expectancy_net >= soft.min_overnight_expectancy and
                meta.overnight_tail_ratio <= soft.max_overnight_tail and
                meta.overnight_p10_return >= soft.min_overnight_p10 and
                meta.overnight_max_loss >= soft.max_overnight_loss):
                
                if gap_valid:
                    if (meta.gap_p10 >= soft.max_gap_p10 and
                        meta.gap_max_loss >= soft.max_gap_loss):
                        return "SOFT"
        
        # Gap-only SOFT (표본 부족 시)
        if meta.overnight_trades < soft.min_overnight_trades:
            if gap_valid:
                if (meta.gap_p10 >= soft.max_gap_p10 and
                    meta.gap_max_loss >= soft.max_gap_loss):
                    return "SOFT"
        
        return "NONE"

    def _check_hero(self, exp: float, wr: float, tail: float, trades: int, tpd: float, crit: HeroCriteria) -> bool:
        if trades < crit.min_trades: return False
        if exp < crit.min_expectancy_net: return False
        if wr < crit.min_win_rate: return False
        if tail > crit.max_tail_ratio: return False
        if tpd > crit.max_tpd: return False
        return True

    def _filter_open_window(self, df: pd.DataFrame, start: str, end: str) -> pd.DataFrame:
        """오픈 구간 필터"""
        x = df.copy()
        dt = pd.to_datetime(x["date"], errors="coerce")
        if getattr(dt.dt, "tz", None) is None:
            dt = dt.dt.tz_localize("Asia/Seoul", ambiguous="infer", nonexistent="shift_forward")

        local = dt.dt.tz_convert("Asia/Seoul")
        t = local.dt.time

        start_time = pd.to_datetime(start).time()
        end_time = pd.to_datetime(end).time()
        mask = (t >= start_time) & (t < end_time)

        return x.loc[mask].copy()

    def _empty_hero(self, symbol: str, probe_name: str, reason: str) -> HeroMetadata:
        return HeroMetadata(
            symbol=symbol,
            probe_name=probe_name,
            expectancy_net=0.0,
            win_rate=0.0,
            tail_ratio=0.0,
            trades=0,
            tpd=0.0,
            total_return=0.0,
            p10_return=0.0,
            p90_return=0.0,
            max_loss_trade=0.0,
            open_window_expectancy=0.0,
            open_window_win_rate=0.0,
            open_window_trades=0,
            overnight_expectancy_net=0.0,
            overnight_win_rate=0.0,
            overnight_tail_ratio=0.0,
            overnight_trades=0,
            overnight_p10_return=0.0,
            overnight_max_loss=0.0,
            overnight_score=0.0,
            gap_p10=np.nan,
            gap_max_loss=np.nan,
            gap_std=np.nan,
            gap_n=0,
            overnight_tier="NONE",
            is_hero=False,
            hero_score=0.0,
            reason_tags=[reason],
        )
