# garam_core/strategy/catalog/mean_reversion.py
from __future__ import annotations

import pandas as pd
import numpy as np
from garam_core.strategy.base import BaseStrategy


class MeanReversionStrategy(BaseStrategy):
    NAME = "mean_reversion"

    def __init__(
        self,
        lookback: int = 20,
        z_enter: float = 1.0,
        z_exit: float = 0.2,
        max_hold_bars: int = 15,   # <<< NEW: 최대 보유시간 (펄스 기준 핵심)
    ):
        self.lookback = lookback
        self.z_enter = z_enter
        self.z_exit = z_exit
        self.max_hold_bars = max_hold_bars

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        close = df["close"]

        ma = close.rolling(self.lookback).mean()
        std = close.rolling(self.lookback).std().replace(0, np.nan)
        z = (close - ma) / std

        signal = pd.Series(0, index=df.index, dtype="float64")

        # 기본 Mean Reversion 진입
        signal[z > self.z_enter] = -1
        signal[z < -self.z_enter] = 1

        # Z-score 정상화 구간에서는 청산
        signal[abs(z) < self.z_exit] = 0

        # -----------------------------
        # NEW: Max Hold Bars Enforcement
        # -----------------------------
        pos = 0
        hold = 0

        for i in range(len(signal)):
            s = signal.iloc[i]

            if pos == 0:
                if s != 0:
                    pos = s
                    hold = 1
                # else stay flat

            else:
                hold += 1

                # 강제 시간 청산
                if hold >= self.max_hold_bars:
                    signal.iloc[i] = 0
                    pos = 0
                    hold = 0
                else:
                    # 포지션 유지 중이면 반대 신호 무시
                    signal.iloc[i] = pos

        return signal.fillna(0).clip(-1, 1)
