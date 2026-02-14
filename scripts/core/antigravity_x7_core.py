from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional, Tuple, Dict, Any, Union, List
from datetime import datetime
from collections import defaultdict, deque

import pandas as pd


# ----------------------------
# Enums / Data Models (X-7f)
# ----------------------------

class StrategyMode(Enum):
    SCALP = "SCALP"   # X-7 (Bear/Neutral)
    SWING = "SWING"   # X-8 (Bull)


class Stage(Enum):
    CANDIDATE = auto()   # 후보(옵션)
    CONFIRMED = auto()   # +1.2% 이상 등 '확정'
    TURBO = auto()       # confirmed & score high => 몰빵 구간


class SignalType(Enum):
    X7_KR_OPEN = "X7_KR_OPEN"   # 시가 공략
    X7_STRUCTURE = "X7_STRUCTURE" # 구조적 돌파
    X8_TREND = "X8_TREND"       # 추세 추종 (Hero Swing)


class ExitReason(Enum):
    NONE = "NONE"
    STRUCT_BREAK = "STRUCT_BREAK"       # 구조 붕괴(2연속)
    PROFIT_TARGET = "PROFIT_TARGET"     # 익절 목표 도달
    TIME_STOP = "TIME_STOP"             # X-7g: 시간 기반 손절
    FAIL_THRUST = "FAIL_THRUST"         # 추진 실패
    QUALITY_DECAY = "QUALITY_DECAY"     # 품질 붕괴
    STALL_EXIT = "STALL_EXIT"           # 확정 정체
    EARLY_GIVEBACK = "EARLY_GIVEBACK"   # 빠른 이익 잠금
    HARD_STOP = "HARD_STOP"             # 단계별 손절
    GIVEBACK = "GIVEBACK"               # MFE 이후 되밀림 청산
    DEAD_MONEY = "DEAD_MONEY"           # 시간 효율 0
    EOD = "EOD"                         # 종가 청산(리서치 모드)


@dataclass
class Candidate:
    ticker: str
    ts: Union[datetime, pd.Timestamp]
    px: float
    score: float
    # Structure signals (engine should compute these)
    above_vwap: bool = True
    above_ema20: bool = True


@dataclass
class Position:
    """
    [X-7f P0] signal_px vs avg_px 분리
    - signal_px: Stage anchor (절대 변하지 않음) -> MFE/Confirmed 판정
    - avg_px: Cost basis (피라미딩 시 갱신) -> 손익/스탑 계산
    """
    ticker: str
    entry_ts: Union[datetime, pd.Timestamp]

    # --- Stage anchor (절대 변하지 않음)
    signal_px: float
    signal_high_px: float

    # --- Cost basis (피라미딩 시 갱신)
    avg_px: float
    qty: int

    # --- Dynamic state
    last_ts: Union[datetime, pd.Timestamp]
    last_px: float
    low_px: float

    # --- Analytics / State
    score_entry: float
    stage: Stage = Stage.CANDIDATE

    # --- Sizing
    weight: float = 0.06
    max_weight: float = 0.06

    # --- Trackers
    last_add_ts: Optional[Union[datetime, pd.Timestamp]] = None
    last_stage_change_ts: Optional[Union[datetime, pd.Timestamp]] = None
    giveback_armed: bool = False
    breakeven_armed: bool = False  # X-7g: break-even stop
    
    # [X-8] Signal Type Tracking
    signal_type: SignalType = SignalType.X7_STRUCTURE


@dataclass
class ExitDecision:
    exit: bool
    reason: ExitReason
    detail: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SwitchDecision:
    decision: str  # "HOLD" or "SWITCH"
    ev_inc: float
    ev_cand: float
    ev_diff: float
    cost: float
    margin: float
    reason_code: str


# ----------------------------
# Config (Phase X-7f)
# ----------------------------

@dataclass
class EngineConfig:
    # Stage thresholds
    confirm_mfe: float = 0.012          # +1.2% => CONFIRMED
    turbo_score: float = 10.0           # >=10 => TURBO 가능 (시작선, 몰빵선 아님)
    turbo_score_2: float = 15.0         # >=15 => TURBO++ 
    turbo_score_3: float = 20.0         # >=20 => 거의 올인
    turbo_score_allin: float = 25.0     # >=25 => 올인

    # Patience (초반 털기 방지)
    patience_min: int = 10

    # Hard stops (단계별)
    hard_stop_cand: float = -0.016
    hard_stop_conf: float = -0.025
    hard_stop_emergency: float = -0.030

    # Struct break (연속 N분)
    struct_break_n: int = 2

    # Giveback
    giveback_arm_mfe: float = 0.018
    giveback_drop: float = 0.009
    giveback_drop_turbo: float = 0.007

    # Dead money
    dead_money_min: int = 20
    dead_money_mfe: float = 0.003

    # Switching economics
    cost_switch: float = 0.0035
    margin_normal: float = 0.0010
    margin_confirmed: float = 0.0060

    # Guarded switching
    persist_window: int = 3
    persist_need: int = 2
    switch_persist_score: float = 10.0
    kill_confirmed_min_score: float = 15.0

    # Entry gate (X-7i: Liquidity + Volatility)
    min_entry_score: float = 8.0        # X-7g Baseline
    min_entry_eu: float = 0.020         # X-7g Baseline
    entry_persist_score: float = 10.0   # X-7g Baseline
    entry_persist_need: int = 2         # X-7g Baseline
    min_daily_turnover: float = 3_000_000_000.0  # X-7i: Min 3B KRW Daily Turnover
    min_daily_volatility: float = 0.015          # X-7j: Min 1.5% Daily Range

    # Lifecycle
    max_roundtrips_per_day: int = 12
    reentry_cooldown_min: int = 3
    reentry_min_score: float = 7.0

    # Sizing (Probe-Base-Turbo) [X-7i: Conservative Baseline]
    probe_weight: float = 0.06      # Revert to X-7i
    confirmed_weight: float = 0.20  # Revert to X-7i
    turbo_weight: float = 0.60      # Revert to X-7i
    turbo_weight_2: float = 0.80
    turbo_weight_3: float = 0.95

    # [X-8] Hero Swing Params
    mode: StrategyMode = StrategyMode.SCALP  # Default
    trend_ma_fast: int = 5
    trend_ma_slow: int = 20
    trailing_stop_atr: float = 3.0  # Wide stop for Heroes
    min_entry_score_trend: float = 5.0 # Lower threshold for trend

    pyramid_step: float = 0.20
    pyramid_cooldown_min: int = 2

    # Early-Add (X-7f: disabled by default)
    enable_early_add: bool = False
    early_add_min_score: float = 15.0
    early_add_min_pnl: float = 0.006
    early_add_target: float = 0.20

    # ===== X-7f: Regime Gate (open 30m) =====
    regime_window_min: int = 30
    regime_flat_rate: float = 0.10      # <10% => FLAT
    regime_probe_rate: float = 0.20     # <20% => PROBE_ONLY
    regime_hero_score: float = 10.0

    # ===== X-7f: Fast Exit Layers =====
    thrust_deadline_min: int = 12
    thrust_mfe_min: float = 0.004
    thrust_score_floor: float = 4.0
    thrust_persist_need: int = 2

    decay_need_min: int = 3
    decay_score_floor: float = 3.0
    decay_window_min: int = 6

    stall_min: int = 35
    stall_progress_mfe: float = 0.018
    stall_score_floor: float = 6.0

    early_giveback_arm: float = 0.010
    early_giveback_drop: float = 0.004

    # ===== X-7f: Tail Turbo Thresholds (P10 기반) =====
    turbo_p10_1: float = 0.03   # 60%
    turbo_p10_2: float = 0.06   # 80%
    turbo_p10_3: float = 0.10   # 95%

    # ===== X-7g: Profit Target Exits =====
    profit_target_cand: float = 0.008   # +0.8% for CANDIDATE
    profit_target_conf: float = 0.015   # +1.5% for CONFIRMED
    profit_target_turbo: float = 0.025  # +2.5% for TURBO

    # ===== X-7g: Time-based Candidate Stop =====
    candidate_max_hold_no_profit: int = 60   # 60 mins with no profit = exit
    candidate_profit_threshold: float = 0.002  # Must be +0.2% by then

    # ===== X-7g: Elite Signal (score>=20) =====
    elite_score_threshold: float = 20.0
    elite_patience_min: int = 20         # Wider patience for elite
    elite_hard_stop: float = -0.025      # Wider stop for elite
    elite_profit_target: float = 0.030   # Higher target for elite

    # ===== X-7g: Break-even Stop =====
    breakeven_arm_pnl: float = 0.005     # Arm break-even at +0.5%

    # ===== X-7g: Giveback (tighter) =====
    giveback_arm_mfe_tight: float = 0.008  # Arm at +0.8% (was 1.8%)


# ----------------------------
# Score Calibration (X-7f: EU + P10)
# ----------------------------

@dataclass
class ScoreCalibration:
    """
    X-7f: EU_total (mean) + P10_move (tail) 같이 관리
    - P10은 "tail move 기준치" (상위 10% 구간의 MFE)
    """
    eu_low: float = 0.015
    eu_mid: float = 0.020
    eu_high: float = 0.030

    # P10(move) - hero_lib 캘리브레이션으로 대체 가능
    p10_low: float = 0.020
    p10_mid: float = 0.035
    p10_high: float = 0.060
    confirmed_tail_boost: float = 1.15

    def eu_total(self, score: float) -> float:
        if score >= 10.0: return self.eu_high
        if score >= 5.0:  return self.eu_mid
        return self.eu_low

    def p10_move(self, score: float, confirmed: bool) -> float:
        if score >= 10.0: base = self.p10_high
        elif score >= 5.0: base = self.p10_mid
        else: base = self.p10_low
        return base * (self.confirmed_tail_boost if confirmed else 1.0)

    def eu_remaining(self, eu_total: float, current_mfe: float) -> float:
        return max(0.0, eu_total - max(0.0, current_mfe))


def score_eu_estimate(score: float, calib: ScoreCalibration, cfg: EngineConfig) -> Tuple[float, bool]:
    eu_total = calib.eu_total(score)
    ok = (score >= cfg.min_entry_score) and (eu_total >= cfg.min_entry_eu)
    return eu_total, ok


# ----------------------------
# Helpers (X-7f: signal/avg 분리)
# ----------------------------

def _hold_min(entry_ts: Union[datetime, pd.Timestamp], now_ts: Union[datetime, pd.Timestamp]) -> float:
    return (now_ts - entry_ts).total_seconds() / 60.0


# [X-7f P0] Cost Basis Helpers
def apply_fill_add(pos: Position, add_qty: int, fill_px: float) -> None:
    """
    피라미딩 원가 버그(P0) 해결:
    - avg_px를 가중평균으로 업데이트
    - signal_px는 고정 (stage anchor)
    """
    if add_qty <= 0:
        return
    new_qty = pos.qty + add_qty
    pos.avg_px = (pos.avg_px * pos.qty + fill_px * add_qty) / new_qty
    pos.qty = new_qty


def pnl_from_avg(pos: Position, px: float) -> float:
    """손익/스탑은 avg_px 기준."""
    return (px / pos.avg_px) - 1.0


def mfe_from_signal(pos: Position) -> float:
    """스테이지/확정 판정은 signal_px 기준."""
    return (pos.signal_high_px / pos.signal_px) - 1.0


def _drawdown_from_peak(high_px: float, px: float) -> float:
    if high_px <= 0:
        return 0.0
    return max(0.0, (high_px - px) / high_px)


# ----------------------------
# Stage classification (signal 기준)
# ----------------------------

def classify_stage(pos: Position, cand_now: Candidate, cfg: EngineConfig) -> Stage:
    mfe = mfe_from_signal(pos)
    if mfe >= cfg.confirm_mfe:
        # X-7f: turbo는 sizing에서 P10으로 결정
        return Stage.CONFIRMED
    return Stage.CANDIDATE


# ----------------------------
# Sizing: Tail-based Turbo (X-7f)
# ----------------------------

def target_weight_for(pos: Position, cand_now: Candidate, cfg: EngineConfig, 
                      calib: ScoreCalibration, regime_ok: bool = True) -> float:
    """
    X-7f: score>=10은 turbo '시작선'일 뿐.
    몰빵은 P10 기준으로만.
    """
    if pos.stage == Stage.CANDIDATE:
        return cfg.probe_weight
    
    # CONFIRMED/TURBO
    if not regime_ok:
        return cfg.confirmed_weight  # 레짐이 안 좋으면 확대 금지
    
    score = cand_now.score
    confirmed = (pos.stage in (Stage.CONFIRMED, Stage.TURBO))
    p10 = calib.p10_move(score, confirmed)
    
    # All-in (95%)
    if score >= cfg.turbo_score_allin and p10 >= cfg.turbo_p10_3:
        return cfg.turbo_weight_3
    # Turbo+ (80%)
    if score >= cfg.turbo_score_3 and p10 >= cfg.turbo_p10_2:
        return cfg.turbo_weight_2
    # Turbo (60%)
    if score >= cfg.turbo_score_2 and p10 >= cfg.turbo_p10_1:
        return cfg.turbo_weight
    
    return cfg.confirmed_weight


def should_pyramid(pos: Position, cand_now: Candidate, now_ts: Union[datetime, pd.Timestamp], 
                   cfg: EngineConfig, calib: ScoreCalibration, regime_ok: bool = True) -> Tuple[bool, float, str]:
    tgt = target_weight_for(pos, cand_now, cfg, calib, regime_ok)
    
    if tgt <= pos.weight + 1e-9:
        return False, pos.weight, "NO_TARGET_UP"

    if pos.last_add_ts is not None:
        since = _hold_min(pos.last_add_ts, now_ts)
        if since < cfg.pyramid_cooldown_min:
            return False, pos.weight, "PYRAMID_COOLDOWN"

    new_w = min(tgt, pos.weight + cfg.pyramid_step)
    return True, new_w, "PYRAMID_ADD"


# ----------------------------
# Memory classes
# ----------------------------

class TopSignalMemory:
    def __init__(self, window: int = 3):
        self.window = window
        self._scores: Dict[str, deque] = defaultdict(lambda: deque(maxlen=self.window))

    def update(self, ticker: str, score: float) -> None:
        self._scores[ticker].append(float(score))

    def persistent(self, ticker: str, threshold: float, need: int) -> bool:
        dq = self._scores.get(ticker)
        if not dq:
            return False
        cnt = sum(1 for s in dq if s >= threshold)
        return cnt >= need

    def last_score(self, ticker: str) -> float:
        dq = self._scores.get(ticker)
        if not dq:
            return 0.0
        return float(dq[-1])


class StructBreakCounter:
    def __init__(self):
        self._cnt: Dict[str, int] = defaultdict(int)

    def update(self, ticker: str, broken_now: bool) -> None:
        if broken_now:
            self._cnt[ticker] += 1
        else:
            self._cnt[ticker] = 0

    def is_broken(self, ticker: str, n: int) -> bool:
        return self._cnt.get(ticker, 0) >= n


# ----------------------------
# Regime Gate (X-7f)
# ----------------------------

class RegimeGate:
    """개장 30분 히어로 데이 판정"""
    def __init__(self):
        self.total = 0
        self.hero = 0
        self.finalized = False
        self.mode = "PROBE_ONLY"

    def update(self, hero_present: bool):
        if self.finalized:
            return
        self.total += 1
        if hero_present:
            self.hero += 1

    def finalize(self) -> str:
        """X-7g: Relaxed thresholds to allow more trading"""
        if self.finalized:
            return self.mode
        self.finalized = True
        rate = (self.hero / self.total) if self.total > 0 else 0.0
        # X-7g: Relaxed thresholds (was 10%/20%)
        if rate < 0.05:
            self.mode = "FLAT"
        elif rate < 0.10:
            self.mode = "PROBE_ONLY"
        else:
            self.mode = "NORMAL"
        return self.mode

    def is_regime_ok(self) -> bool:
        return self.mode == "NORMAL"


# ----------------------------
# EV Switching (Guarded)
# ----------------------------

def ev_incumbent_remaining(pos: Position, inc_now: Candidate, calib: ScoreCalibration, cfg: EngineConfig) -> float:
    eu_total = calib.eu_total(inc_now.score)
    mfe_now = mfe_from_signal(pos)
    rem = calib.eu_remaining(eu_total, mfe_now)

    struct_penalty = 1.0
    if (not inc_now.above_vwap) and (not inc_now.above_ema20):
        struct_penalty = 0.65

    if pos.stage == Stage.TURBO:
        mult = 1.30
    elif pos.stage == Stage.CONFIRMED:
        mult = 1.15
    else:
        mult = 1.00

    return rem * mult * struct_penalty


def ev_candidate_option(new: Candidate, calib: ScoreCalibration) -> float:
    eu_total = calib.eu_total(new.score)
    return eu_total * 0.37


def candidate_gate(c: Candidate, calib: ScoreCalibration, cfg: EngineConfig) -> Tuple[bool, str, float]:
    eu_total, ok = score_eu_estimate(c.score, calib, cfg)
    if not ok:
        return False, "LOW_QUALITY", eu_total
    return True, "OK", eu_total


def should_switch_ev_guarded(
    inc: Position,
    inc_now: Candidate,
    new: Candidate,
    sigmem: TopSignalMemory,
    calib: ScoreCalibration,
    cfg: EngineConfig,
) -> SwitchDecision:
    ok_gate, _, _ = candidate_gate(new, calib, cfg)
    if not ok_gate:
        return SwitchDecision("HOLD", 0.0, 0.0, 0.0, cfg.cost_switch, 0.0, "NEW_FAIL_GATE")

    persistent = sigmem.persistent(new.ticker, threshold=cfg.switch_persist_score, need=cfg.persist_need)
    if not persistent:
        ev_inc = ev_incumbent_remaining(inc, inc_now, calib, cfg)
        ev_new = ev_candidate_option(new, calib)
        return SwitchDecision("HOLD", ev_inc, ev_new, ev_new - ev_inc, cfg.cost_switch,
                              cfg.margin_confirmed if inc.stage != Stage.CANDIDATE else cfg.margin_normal,
                              "NEW_NO_PERSIST")

    if inc.stage in (Stage.CONFIRMED, Stage.TURBO):
        if new.score < cfg.kill_confirmed_min_score:
            ev_inc = ev_incumbent_remaining(inc, inc_now, calib, cfg)
            ev_new = ev_candidate_option(new, calib)
            return SwitchDecision("HOLD", ev_inc, ev_new, ev_new - ev_inc, cfg.cost_switch,
                                  cfg.margin_confirmed, "NOT_MONSTER_TO_KILL_CONF")

    ev_inc = ev_incumbent_remaining(inc, inc_now, calib, cfg)
    ev_new = ev_candidate_option(new, calib)

    cost = cfg.cost_switch
    margin = cfg.margin_confirmed if inc.stage in (Stage.CONFIRMED, Stage.TURBO) else cfg.margin_normal
    diff = ev_new - ev_inc
    thresh = cost + margin

    if diff > thresh:
        rc = "KILL_CONFIRMED" if margin == cfg.margin_confirmed else "UPGRADE_CAND"
        return SwitchDecision("SWITCH", ev_inc, ev_new, diff, cost, margin, rc)

    return SwitchDecision("HOLD", ev_inc, ev_new, diff, cost, margin, "NO_EDGE")


# ----------------------------
# Re-entry / lifecycle
# ----------------------------

def can_reenter(
    last_exit_ts: Optional[Union[datetime, pd.Timestamp]],
    roundtrips_today: int,
    cand: Candidate,
    cfg: EngineConfig
) -> Tuple[bool, str]:
    if roundtrips_today >= cfg.max_roundtrips_per_day:
        return False, "MAX_ROUNDTRIPS"

    if cand.score < cfg.reentry_min_score:
        return False, "REENTRY_LOW_SCORE"

    if last_exit_ts is None:
        return True, "OK_FIRST"

    mins = _hold_min(last_exit_ts, cand.ts)
    if mins < cfg.reentry_cooldown_min:
        return False, "REENTRY_COOLDOWN"

    return True, "OK_REENTER"


# ------------------------------
# X-8 Trend Logic (New)
# ------------------------------
def should_enter_trend(
    cand: Candidate,
    cfg: EngineConfig,
    history_df: pd.DataFrame
) -> Optional[float]:
    """
    X-8 Trend Entry Logic:
    1. Liquidity: > 10B KRW Turnover (Blue Chips only)
    2. Trend: Price > MA20 > MA60 (Perfect Alignment)
    3. Momentum: MA5 > MA20 (Short-term Strength)
    Returns: Score (Higher is better) or None
    """
    # 1. Liquidity Check (Strict for Swing)
    if cand.turnover < 10_000_000_000:
        return None

    # Need history for MA calculation
    if len(history_df) < 60:
        return None

    closes = history_df['close'].values
    # Append current close for realtime check
    closes = np.append(closes, cand.px) 
    
    ma5 = closes[-5:].mean()
    ma20 = closes[-20:].mean()
    ma60 = closes[-60:].mean()

    # 2. Alignment Check
    # Price > MA20 > MA60
    if not (cand.px > ma20 and ma20 > ma60):
        return None
    
    # 3. Momentum Check (MA5 > MA20)
    if ma5 <= ma20:
        return None

    # Score based on trend strength (Gradient)
    score = 10.0 + (ma5 / ma20 - 1.0) * 100.0
    return score

def should_exit_trend(
    pos: Position,
    cand: Candidate,
    cfg: EngineConfig
) -> ExitDecision:
    """
    X-8 Trend Exit Logic:
    1. Trailing Stop: Exit if Price < Highest High - (ATR * 3.0)
       (Simplified: Use fixed % drop for speed if ATR not avail, but we try dynamic)
    2. MA Breakdown: Exit if Close < MA20 (Trend Broken)
    3. No Take Profit! (Let winners run)
    """
    # Dynamic Trailing Stop (Approximation)
    # We use mfe to track highest high since entry.
    # We use a loose stop of 5% from peak if ATR unavailable
    
    # Calculate Drawdown from Peak
    peak = pos.signal_high_px
    drop_pct = (peak - cand.px) / peak
    
    # 1. Trailing Stop (Fixed % for robustness vs ATR complexity in this snippet)
    # 5% Trailing Stop for Swing
    if drop_pct >= 0.05:
         return ExitDecision(True, ExitReason.GIVEBACK, {"mode": "TREND_TRAIL", "drop": drop_pct})

    # 2. Hard Stop (Initial Risk)
    pnl = pnl_from_avg(pos, cand.px)
    if pnl <= -0.03: # 3% Hard Stop
        return ExitDecision(True, ExitReason.HARD_STOP, {"mode": "TREND_STOP", "pnl": pnl})

    return ExitDecision(False, ExitReason.NONE)


# ----------------------------
# Fast Exit Layers (X-7f)
# ----------------------------

def should_exit_fast(
    pos: Position,
    cand_now: Candidate,
    cfg: EngineConfig,
    sigmem: TopSignalMemory,
) -> Optional[ExitDecision]:
    """
    X-7f 빠른 탈출 레이어:
    - FAIL_THRUST: 12분에 +0.4% MFE도 못 줬고 score도 약하면 폐기
    - QUALITY_DECAY: score<3이 3분 연속이면 후보 폐기
    - STALL_EXIT: confirmed인데 35분 넘게 끌고 MFE<1.8% + score<6
    - EARLY_GIVEBACK: non-turbo 작은 이익이라도 잠금
    """
    hold = _hold_min(pos.entry_ts, cand_now.ts)
    pnl = pnl_from_avg(pos, cand_now.px)
    mfe = mfe_from_signal(pos)

    # FAIL_THRUST
    if pos.stage == Stage.CANDIDATE and hold >= cfg.thrust_deadline_min:
        dq = sigmem._scores.get(pos.ticker)
        if dq is not None:
            low_cnt = sum(1 for s in dq if s < cfg.thrust_score_floor)
            if mfe < cfg.thrust_mfe_min and low_cnt >= cfg.thrust_persist_need:
                return ExitDecision(True, ExitReason.FAIL_THRUST, {"hold": hold, "mfe": mfe, "pnl": pnl})

    # QUALITY_DECAY
    if pos.stage == Stage.CANDIDATE and hold >= cfg.decay_window_min:
        dq = sigmem._scores.get(pos.ticker)
        if dq is not None and len(dq) >= cfg.decay_need_min:
            tail = list(dq)[-cfg.decay_need_min:]
            if all(s < cfg.decay_score_floor for s in tail) and mfe < cfg.confirm_mfe:
                return ExitDecision(True, ExitReason.QUALITY_DECAY, {"hold": hold, "tail": tail, "mfe": mfe})

    # STALL_EXIT
    if pos.stage == Stage.CONFIRMED and hold >= cfg.stall_min:
        if mfe < cfg.stall_progress_mfe and cand_now.score < cfg.stall_score_floor:
            return ExitDecision(True, ExitReason.STALL_EXIT, {"hold": hold, "mfe": mfe, "score": cand_now.score})

    # EARLY_GIVEBACK
    if pos.stage != Stage.TURBO and mfe >= cfg.early_giveback_arm:
        drop = _drawdown_from_peak(pos.signal_high_px, cand_now.px)
        if drop >= cfg.early_giveback_drop:
            return ExitDecision(True, ExitReason.EARLY_GIVEBACK, {"mfe": mfe, "drop": drop, "pnl": pnl})

    return None


# ----------------------------
# Exit layer (X-7g: Profit Target + Time Stop + Break-even)
# ----------------------------

def is_elite_signal(score: float, cfg: EngineConfig) -> bool:
    """X-7g: Check if signal is elite (>=20)"""
    return score >= cfg.elite_score_threshold


def should_exit(
    pos: Position,
    cand_now: Candidate,
    cfg: EngineConfig,
    sigmem: TopSignalMemory,
    sbc: Optional[StructBreakCounter] = None
) -> ExitDecision:
    """
    X-7g Exit Logic (Restored):
    - Full Exits only (No Partials)
    - Profit Targets: +0.8% (Cand), +1.5% (Conf), +2.5% (Turbo), +3.0% (Elite)
    - Time Stop: 60m with < 0.2% profit
    - Auto Break-even: Arm at +0.5%, Stop at 0.0%
    """
    now_ts = cand_now.ts
    hold = _hold_min(pos.entry_ts, now_ts)
    pnl = pnl_from_avg(pos, cand_now.px)
    mfe = mfe_from_signal(pos)
    elite = is_elite_signal(pos.score_entry, cfg)

    # 1. STRUCT_BREAK (Priority 1)
    if sbc is not None and sbc.is_broken(pos.ticker, cfg.struct_break_n):
        return ExitDecision(True, ExitReason.STRUCT_BREAK, {"pnl": pnl, "hold_min": hold})

    # 2. PROFIT TARGET (Global Priority 2)
    if pos.stage == Stage.CANDIDATE:
        target = cfg.profit_target_cand # +0.8%
        if pnl >= target:
            return ExitDecision(True, ExitReason.PROFIT_TARGET, {"pnl": pnl, "target": target})
            
    elif pos.stage == Stage.CONFIRMED:
        target = cfg.profit_target_conf # +1.5%
        if pnl >= target:
            return ExitDecision(True, ExitReason.PROFIT_TARGET, {"pnl": pnl, "target": target})
            
    elif pos.stage == Stage.TURBO:
        # Elite vs Normal Turbo
        if elite:
             target = cfg.elite_profit_target # +3.0%
             if pnl >= target:
                 return ExitDecision(True, ExitReason.PROFIT_TARGET, {"pnl": pnl, "mode": "ELITE", "target": target})
        else:
             target = cfg.profit_target_turbo # +2.5%
             if pnl >= target:
                 return ExitDecision(True, ExitReason.PROFIT_TARGET, {"pnl": pnl, "target": target})

    # 3. TIME_STOP
    if pos.stage == Stage.CANDIDATE:
        if hold >= cfg.candidate_max_hold_no_profit and pnl < cfg.candidate_profit_threshold:
            return ExitDecision(True, ExitReason.TIME_STOP, {"pnl": pnl, "hold_min": hold})

    # 4. FAST EXIT LAYERS
    fast = should_exit_fast(pos, cand_now, cfg, sigmem)
    if fast is not None:
        return fast

    # 5. Break-even stop (Early Arm)
    if pnl >= cfg.breakeven_arm_pnl:
        pos.breakeven_armed = True
    if pos.breakeven_armed and pnl <= 0.0:
        return ExitDecision(True, ExitReason.HARD_STOP, {"mode": "BREAKEVEN", "pnl": pnl})

    # 6. Stage-based Hard Stop
    patience = cfg.elite_patience_min if elite else cfg.patience_min
    hard_stop = cfg.elite_hard_stop if elite and pos.stage != Stage.CANDIDATE else (
        cfg.hard_stop_cand if pos.stage == Stage.CANDIDATE else cfg.hard_stop_conf
    )
    
    if hold >= patience:
        if pnl <= hard_stop:
            return ExitDecision(True, ExitReason.HARD_STOP, {"mode": pos.stage.name, "pnl": pnl, "hold_min": hold})

    # 7. Giveback
    arm_mfe = cfg.giveback_arm_mfe_tight if pos.stage != Stage.TURBO else cfg.giveback_arm_mfe
    if mfe >= arm_mfe:
        pos.giveback_armed = True

    if pos.giveback_armed:
        drop = _drawdown_from_peak(pos.signal_high_px, cand_now.px)
        gb = cfg.giveback_drop_turbo if pos.stage == Stage.TURBO else cfg.giveback_drop
        if drop >= gb:
            return ExitDecision(True, ExitReason.GIVEBACK, {"mfe": mfe, "drop": drop, "pnl": pnl})

    # 8. Dead Money
    if hold >= cfg.dead_money_min and mfe < cfg.dead_money_mfe:
        return ExitDecision(True, ExitReason.DEAD_MONEY, {"mfe": mfe, "hold_min": hold, "pnl": pnl})

    return ExitDecision(False, ExitReason.NONE)


# ----------------------------
# Switch ledger row (SAVS Table C)
# ----------------------------

def build_switch_ledger_row(
    ts: Union[datetime, pd.Timestamp],
    inc: Position,
    inc_now: Candidate,
    new: Candidate,
    sd: SwitchDecision
) -> Dict[str, Any]:
    return {
        "ts": ts,
        "incumbent_ticker": inc.ticker,
        "incumbent_stage": inc.stage.name,
        "incumbent_score_now": float(inc_now.score),
        "incumbent_ev": float(sd.ev_inc),
        "candidate_ticker": new.ticker,
        "candidate_score": float(new.score),
        "candidate_ev": float(sd.ev_cand),
        "ev_diff": float(sd.ev_diff),
        "cost_switch": float(sd.cost),
        "margin_used": float(sd.margin),
        "decision": sd.decision,
        "reason_code": sd.reason_code,
    }
