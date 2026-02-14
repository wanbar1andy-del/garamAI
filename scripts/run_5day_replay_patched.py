
import pandas as pd
import glob
import os
import backtrader as bt
import datetime as dt


class IntradayHeroStrategyPatched(bt.Strategy):
    """
    Reliability Patch v1
    - No look-ahead: compare against prev bar indicator values
    - No over-allocation: allow at most 1 new entry per 'next()' across all datas
    - Explicit EOD behavior
    - Optional: trade only within market hours
    """
    params = (
        ("warmup", 30),                # minimum bars before trading per symbol
        ("breakout_lookback", 30),      # Highest window
        ("vol_ma_period", 20),          # Volume MA window
        ("vol_mult", 3.0),              # volume trigger multiplier
        ("trail_stop", 0.01),           # hard stop from entry price (simple)
        ("take_profit", 0.05),          # TP (5% default; test 0.10 etc.)
        ("entry_cash_frac", 0.10),      # per-entry budget fraction of TOTAL equity (not raw cash)
        ("max_new_entries_per_bar", 1), # critical: prevent multi-fill over-allocation
        ("no_entry_after", dt.time(14, 30)),
        ("force_exit_at", dt.time(15, 0)),
        ("market_open", dt.time(9, 0)),
        ("market_close", dt.time(15, 30)),
        ("enforce_market_hours", True),
        ("debug", False),
    )

    def __init__(self):
        self.inds = {}
        for d in self.datas:
            self.inds[d] = {
                "vol_ma": bt.indicators.SMA(d.volume, period=self.p.vol_ma_period),
                "high_roll": bt.indicators.Highest(d.high, period=self.p.breakout_lookback),
            }

        self.equity_log = []
        self._entered_this_bar = 0

    def log(self, msg):
        if self.p.debug:
            print(msg)

    def next(self):
        # Reset per-bar entry counter
        self._entered_this_bar = 0

        # Equity logging
        self.equity_log.append({
            "ts": self.datas[0].datetime.datetime(0),
            "Total_Equity": float(self.broker.getvalue()),
        })

        now_time = self.datas[0].datetime.time(0)

        # Optional: enforce trading window
        if self.p.enforce_market_hours:
            if not (self.p.market_open <= now_time <= self.p.market_close):
                return

        # EOD forced liquidation: liquidate all positions at/after force_exit_at
        if now_time >= self.p.force_exit_at:
            for d in self.datas:
                pos = self.getposition(d).size
                if pos != 0:
                    self.close(data=d)
            return

        # Iterate datas and apply exits first, then entries
        # (Exit-first prevents "buy then immediately sell" anomalies.)
        for d in self.datas:
            if len(d) < self.p.warmup:
                continue

            pos = self.getposition(d).size
            if pos > 0:
                entry_price = self.getposition(d).price

                # Simple stop / TP using current close
                if d.close[0] < entry_price * (1 - self.p.trail_stop):
                    self.close(data=d)
                elif d.close[0] >= entry_price * (1 + self.p.take_profit):
                    self.close(data=d)

        # Entries (budgeted + throttled)
        if now_time >= self.p.no_entry_after:
            return

        # Hard throttle: at most N new entries per bar across all symbols
        for d in self.datas:
            if self._entered_this_bar >= self.p.max_new_entries_per_bar:
                break

            if len(d) < self.p.warmup:
                continue

            pos = self.getposition(d).size
            if pos != 0:
                continue

            # ===== No Look-ahead Fix =====
            # Use previous bar's indicator values for threshold comparisons.
            # If indicator not ready (nan/0), skip.
            prev_vol_ma = self.inds[d]["vol_ma"][-1]
            prev_high = self.inds[d]["high_roll"][-1]

            if prev_vol_ma is None or prev_high is None:
                continue
            if prev_vol_ma <= 0 or prev_high <= 0:
                continue

            vol_cond = d.volume[0] > prev_vol_ma * self.p.vol_mult
            price_cond = d.close[0] >= prev_high

            if vol_cond and price_cond:
                # Sizing: fraction of TOTAL equity (more stable than raw cash in multi-order situations)
                total_equity = float(self.broker.getvalue())
                budget = total_equity * self.p.entry_cash_frac

                # Ensure we don't exceed available cash
                cash = float(self.broker.getcash())
                budget = min(budget, cash)

                size = int(budget / float(d.close[0]))
                if size > 0:
                    self.buy(data=d, size=size)
                    self._entered_this_bar += 1
                    self.log(f"[BUY] {d._name} size={size} px={d.close[0]} ts={d.datetime.datetime(0)}")


def load_day_data_as_feeds(data_dir: str, date_str: str):
    """
    Loads all CSVs in data_dir, filters to date_str (YYYY-MM-DD),
    returns list of bt.feeds.PandasData
    """
    target_date = pd.to_datetime(date_str).date()
    feeds = []

    files = glob.glob(os.path.join(data_dir, "*.csv"))
    for f in files:
        sym = os.path.basename(f).replace(".csv", "")
        try:
            df = pd.read_csv(f)
            if "ts" not in df.columns:
                continue
            df["ts"] = pd.to_datetime(df["ts"])

            day_df = df[df["ts"].dt.date == target_date].copy()
            if len(day_df) < 30:
                continue

            # sort + de-dup timestamps (reliability hygiene)
            day_df.sort_values("ts", inplace=True)
            day_df.drop_duplicates(subset=["ts"], keep="last", inplace=True)

            # basic sanity: required columns
            required = {"open", "high", "low", "close", "volume"}
            if not required.issubset(set(day_df.columns)):
                continue

            day_df.set_index("ts", inplace=True)

            data = bt.feeds.PandasData(
                dataname=day_df,
                open="open", high="high", low="low", close="close", volume="volume",
                openinterest=None,
                timeframe=bt.TimeFrame.Minutes,
                compression=1,
            )
            data._name = sym
            feeds.append(data)

        except Exception:
            continue

    return feeds


def run_5day_replay_patched():
    dates = ["2025-12-09", "2025-12-10", "2025-12-11", "2025-12-12", "2026-01-02"]
    data_dir = "GARAM_Data/5day_replay_kst" # Updated to Normalized Data

    current_cash = 10_000_000.0
    equity_curve = []

    for date_str in dates:
        print(f"\\n--- Simulating {date_str} (Start Cash: {current_cash:,.0f} KRW) ---")

        cerebro = bt.Cerebro(stdstats=False)
        cerebro.broker.setcash(current_cash)
        cerebro.broker.setcommission(commission=0.0023)

        # NOTE: By default, Backtrader executes on next bar.
        # If you want cheat-on-close behavior, uncomment:
        # cerebro.broker.set_coc(True)

        feeds = load_day_data_as_feeds(data_dir, date_str)
        if not feeds:
            print(f"No feeds for {date_str}. Skipping.")
            continue

        for d in feeds:
            cerebro.adddata(d)

        cerebro.addstrategy(
            IntradayHeroStrategyPatched,
            warmup=30,
            breakout_lookback=30,
            vol_ma_period=20,
            vol_mult=3.0,
            trail_stop=0.01,
            take_profit=0.05,
            entry_cash_frac=0.10,
            max_new_entries_per_bar=1,   # critical anti-overallocation
            enforce_market_hours=True,
            debug=False,
        )

        results = cerebro.run()
        strat = results[0]

        current_cash = float(cerebro.broker.getvalue())
        print(f"End Equity ({date_str}): {current_cash:,.0f} KRW")

        # append this day's equity log (continuous because we set starting cash to current_cash)
        equity_curve.extend(strat.equity_log)

    print(f"\\nFinal 5-Day Equity: {current_cash:,.0f} KRW")

    out_path = "GARAM_Data/5day_equity_patched.csv"
    pd.DataFrame(equity_curve).to_csv(out_path, index=False)
    print(f"Saved {out_path}")


if __name__ == "__main__":
    run_5day_replay_patched()
