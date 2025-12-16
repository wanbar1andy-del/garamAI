# garam_core/live/runner.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Any
import pandas as pd
import numpy as np
from datetime import datetime

from garam_core.live.spec import LiveSpec
from garam_core.live.interfaces import DataFeed, ExecutionGateway, PortfolioStore
from garam_core.live.state import LiveAccountState
from garam_core.strategy.registry import discover_strategies
from garam_core.research.pulse.load_data import enhance_features

def compute_score(df: pd.DataFrame, lookback_ev: int = 30, vol_lookback: int = 30) -> float:
    # Simplified score for live (last point)
    close = df["close"]
    if len(close) < lookback_ev:
        return 0.0
    
    # Efficient calculation for just the tail? 
    # Or just calc rolling for whole df (simpler code)
    r1_abs = close.pct_change().abs()
    pulse_amp = r1_abs.rolling(lookback_ev).mean().iloc[-1]
    
    vol_spike = 1.0
    if "volume" in df.columns:
        vol_ma = df["volume"].rolling(vol_lookback).mean().iloc[-1]
        curr_vol = df["volume"].iloc[-1]
        if vol_ma > 0:
            vol_spike = curr_vol / vol_ma
            
    return float(pulse_amp * vol_spike)


@dataclass
class LiveRunner:
    spec: LiveSpec
    feed: DataFeed
    gateway: ExecutionGateway
    store: PortfolioStore

    strategy_name: str = "regime_switch"
    lookback_ev: int = 30
    vol_lookback: int = 30

    _dfs: Dict[str, pd.DataFrame] = field(default_factory=dict)
    _state: LiveAccountState = None
    _strategy_cls: Any = None

    def _init_strategy_cls(self):
        strategies = discover_strategies()
        for s in strategies:
            if getattr(s, "NAME", "") == self.strategy_name:
                self._strategy_cls = s
                return
        raise RuntimeError(f"Strategy {self.strategy_name} not found")

    def _init_state(self):
        self._state = LiveAccountState(
             equity=self.spec.base_equity,
             peak_equity=self.spec.base_equity
        )

    def _build_strategy(self, symbol: str):
        # Support symbol-specific patches
        try:
            return self._strategy_cls(symbol=symbol)
        except TypeError:
            return self._strategy_cls()

    def _risk_check(self) -> bool:
        if abs(self._state.mdd) >= self.spec.max_mdd:
            print(f"[RISK] MDD Breach: {self._state.mdd:.2%}")
            return False
        # Daily loss check requires tracking separate Start-of-Day equity. 
        # Skipping simple implementation for now, assuming base_equity is fixed reference.
        if self._state.consecutive_losses >= self.spec.max_consecutive_loss:
            print(f"[RISK] Consec Loss Breach: {self._state.consecutive_losses}")
            return False
        return True

    def run(self):
        self._init_strategy_cls()
        self._init_state()

        self.feed.subscribe(self.spec.symbols)
        for sym in self.spec.symbols:
            self._dfs[sym] = pd.DataFrame()

        print(f"[LIVE] Started. Strategy={self.strategy_name}, Symbols={len(self.spec.symbols)}")

        while True:
            # Block until next bar
            bar_dict = self.feed.get_next_bar()
            if not bar_dict:
                print("[LIVE] Stream ended.")
                break

            ts = datetime.now()
            prices = {}

            # 1. Update Data
            for sym, bar in bar_dict.items():
                # bar is Series
                df = self._dfs[sym]
                row = bar.to_frame().T
                row.index = pd.to_datetime([row.name] if row.name else [ts])
                df = pd.concat([df, row])
                df = enhance_features(df) # Add tech indicators
                self._dfs[sym] = df
                prices[sym] = float(bar["close"])

            # 2. Update Account
            cash = self.gateway.get_cash()
            curr_pos = self.gateway.get_positions()
            self._state.positions = curr_pos
            self._state.update_mark_to_market(prices, cash)
            
            # Log Bar State
            self.store.record_bar(
                ts=ts, 
                equity=self._state.equity, 
                positions=curr_pos, 
                meta={"mdd": self._state.mdd, "prices": prices}
            )

            # 3. Risk Gate
            if not self._risk_check():
                print("[LIVE] Risk Triggered. Halting.")
                break

            # 4. Strategy & Scores
            signals = {}
            scores = {}
            for sym in self.spec.symbols:
                df = self._dfs[sym]
                if len(df) < 50: continue # warmup

                strat = self._build_strategy(sym)
                sig_s = strat.generate_signals(df).fillna(0)
                if len(sig_s) > 0:
                    signals[sym] = float(sig_s.iloc[-1])
                    scores[sym] = compute_score(df, self.lookback_ev, self.vol_lookback)

            # 5. Top-K Selection
            candidates = [(sym, signals[sym], scores[sym]) for sym in signals if signals[sym] != 0]
            candidates.sort(key=lambda x: x[2], reverse=True)
            
            selected = [c[0] for c in candidates[:self.spec.topk]]
            
            # 6. Target Weights
            weights = {}
            if selected:
                # Mode: Equal
                w = 1.0 / len(selected) # allocated among selected
                # Note: This implies 100% equity invested in selected. 
                # Be careful with cash buffer.
                for sym in selected:
                    direction = np.sign(signals[sym]) # 1 or -1
                    weights[sym] = w * direction
            
            # 7. Execution (Diff)
            # Target Value per symbol
            equity = self._state.equity
            tgt_val = {sym: weights.get(sym, 0.0) * equity for sym in self.spec.symbols}
            
            for sym in self.spec.symbols:
                price = prices.get(sym)
                if not price: continue
                
                cur_qty = curr_pos.get(sym, 0.0)
                tgt_qty = tgt_val[sym] / price
                
                delta = int(np.round(tgt_qty - cur_qty))
                if delta == 0: continue
                
                side = "BUY" if delta > 0 else "SELL"
                qty = abs(delta)
                
                res = self.gateway.send_order(sym, side, qty, price)
                if res:
                    self.store.record_trade(
                        ts=ts, symbol=sym, side=side, qty=qty, price=price, 
                        meta={"target_w": weights.get(sym,0)}
                    )
                    # Approx PnL feedback loop would go here (or via gateway callbacks)
    
        print("[LIVE] Finished Run.")
