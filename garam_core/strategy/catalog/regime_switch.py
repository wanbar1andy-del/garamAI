# garam_core/strategy/catalog/regime_switch.py
from __future__ import annotations

import pandas as pd

from garam_core.strategy.base import BaseStrategy
from garam_core.strategy.catalog.breakout import BreakoutStrategy
from garam_core.strategy.catalog.mean_reversion import MeanReversionStrategy


class RegimeSwitchStrategy(BaseStrategy):
    NAME = "regime_switch"

    def __init__(
        self,
        bull_thr: float = 0.01,
        bear_thr: float = -0.01,
        lookback: int = 60,
        ma_fast: int = 20,
        ma_slow: int = 60,
        confirm_bars: int = 10,

        # EV Gate
        lookback_ev: int = 30,
        ev_mult: float = 1.2,
        cost_per_trade: float = 0.0031,

        # Volume Pulse Filter (NEW)
        vol_lookback: int = 30,
        vol_mult: float = 1.3,     # volume / vol_ma >= 1.3이면 펄스
        use_range_filter: bool = False,
        range_lookback: int = 30,
        range_mult: float = 1.2,   # (high-low)/close >= range_ma*1.2이면 펄스
    ):
        self.bull_thr = bull_thr
        self.bear_thr = bear_thr
        self.lookback = lookback
        self.ma_fast = ma_fast
        self.ma_slow = ma_slow
        self.confirm_bars = confirm_bars

        self.lookback_ev = lookback_ev
        self.ev_mult = ev_mult
        self.cost_per_trade = cost_per_trade

        self.vol_lookback = vol_lookback
        self.vol_mult = vol_mult
        self.use_range_filter = use_range_filter
        self.range_lookback = range_lookback
        self.range_mult = range_mult

        self.breakout = BreakoutStrategy()
        self.meanrev = MeanReversionStrategy()

    def _classify_regime(self, df: pd.DataFrame) -> pd.Series:
        close = df["close"]
        ret_lb = close / close.shift(self.lookback) - 1.0

        ma_f = close.rolling(self.ma_fast).mean()
        ma_s = close.rolling(self.ma_slow).mean()
        slope = ma_f.diff()

        regime = pd.Series("range", index=df.index, dtype="object")
        bull = (ret_lb > self.bull_thr) & (ma_f > ma_s) & (slope > 0)
        bear = (ret_lb < self.bear_thr) & (ma_f < ma_s) & (slope < 0)
        regime[bull] = "bull"
        regime[bear] = "bear"
        return regime

    def _apply_hysteresis(self, raw_regime: pd.Series) -> pd.Series:
        out = raw_regime.copy()
        if raw_regime.empty:
            return out

        current = raw_regime.iloc[0]
        pending = current
        pending_count = 0

        for i in range(1, len(raw_regime)):
            r = raw_regime.iloc[i]
            if r == current:
                pending = current
                pending_count = 0
                out.iloc[i] = current
                continue

            if r != pending:
                pending = r
                pending_count = 1
            else:
                pending_count += 1

            if pending_count >= self.confirm_bars:
                current = pending
                pending = current
                pending_count = 0

            out.iloc[i] = current
        return out

    def _ev_gate(self, df: pd.DataFrame) -> pd.Series:
        # pulse amplitude proxy: mean(abs 1-bar return) over window
        r1_abs = df["close"].pct_change().abs()
        amp = r1_abs.rolling(self.lookback_ev).mean()

        entry_half_cost = self.cost_per_trade / 2.0
        gate = amp > (entry_half_cost * self.ev_mult)
        return gate.fillna(False)

    def _pulse_gate(self, df: pd.DataFrame) -> pd.Series:
        """
        NEW: Volume pulse gate (+ optional range gate)
        - volume spike: volume / MA(volume) >= vol_mult
        - optional range spike: (high-low)/close >= MA(range)*range_mult
        """
        if "volume" not in df.columns:
            # volume 없으면 gate는 False(보수). 필요시 True로 바꿀 수도 있음.
            return pd.Series(False, index=df.index)

        vol_ma = df["volume"].rolling(self.vol_lookback).mean()
        vol_gate = (df["volume"] / vol_ma) >= self.vol_mult

        if not self.use_range_filter:
            return vol_gate.fillna(False)

        # range filter (optional)
        if not {"high", "low", "close"}.issubset(df.columns):
            return vol_gate.fillna(False)

        rng = (df["high"] - df["low"]) / df["close"].replace(0, pd.NA)
        rng_ma = rng.rolling(self.range_lookback).mean()
        rng_gate = rng >= (rng_ma * self.range_mult)

        return (vol_gate & rng_gate).fillna(False)

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        if "close" not in df.columns:
            raise ValueError("DataFrame must include 'close'.")

        sig_breakout = self.breakout.generate_signals(df).fillna(0).clip(-1, 1)
        sig_meanrev = self.meanrev.generate_signals(df).fillna(0).clip(-1, 1)

        raw_regime = self._classify_regime(df)
        regime = self._apply_hysteresis(raw_regime)

        out = pd.Series(0, index=df.index, dtype="float64")

        bull_mask = (regime == "bull")
        rb_mask = ~bull_mask

        # Bull: breakout
        out[bull_mask] = sig_breakout[bull_mask]

        # Range/Bear: meanrev gated by EV + Pulse(volume/range)
        ev_gate = self._ev_gate(df)
        pulse_gate = self._pulse_gate(df)
        allow = rb_mask & ev_gate & pulse_gate

        out[allow] = sig_meanrev[allow]
        out[rb_mask & (~allow)] = 0

        return out.fillna(0).clip(-1, 1)
