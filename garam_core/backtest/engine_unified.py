# garam_core/backtest/engine_unified.py
import pandas as pd
import numpy as np
from garam_core.strategy.base import BaseStrategy


def run_backtest_unified(
    strategy: BaseStrategy,
    df: pd.DataFrame,
    cost_per_trade: float = 0.0031,  # roundtrip cost (e.g., 31bp)
) -> dict:
    """
    Unified engine:
    - Convention: Signal at T implies desired position starting T+1.
      -> position[t] = signal[t-1]
    - Return[t] is from close[t-1] -> close[t]
      -> pnl contribution uses position[t] * market_ret[t]
    - Cost model (consistent everywhere):
      cost_bar[t] = abs(position[t] - position[t-1]) * (cost_per_trade/2)
      (entry half + exit half; flip becomes full cost)
    """

    df = df.copy()
    if "close" not in df.columns:
        raise ValueError("DataFrame must include 'close' column.")

    # 1) Signals & Positions
    signals = strategy.generate_signals(df).fillna(0)
    # Ensure signals are in {-1,0,1}
    signals = signals.clip(-1, 1)

    # Position[t] = Signal[t-1]
    positions = signals.shift(1).fillna(0)

    # 2) Market returns (close-to-close)
    market_ret = df["close"].pct_change().fillna(0)

    # 3) Vector PnL (gross) & Costs (bar-level)
    gross_ret = positions * market_ret

    pos_change = positions.diff().fillna(positions.iloc[0]).abs()
    cost_half = cost_per_trade / 2.0
    costs = pos_change * cost_half  # consistent rule

    net_ret = gross_ret - costs
    equity = (1.0 + net_ret).cumprod()

    # 4) Trade log (event-based, consistent with bar cost rule)
    closes = df["close"].values
    idx = df.index
    pos_arr = positions.values

    trades = []
    current_pos = 0.0
    entry_bar = None
    entry_price = None
    entry_time = None
    pending_entry_cost = 0.0  # entry side cost portion to attach to next trade

    def _close_trade(exit_bar: int, exit_price: float, exit_time, side: float, extra_cost: float):
        """Close the active trade and append to trades list."""
        nonlocal entry_price, entry_time

        if entry_price is None or entry_time is None:
            return

        gross = (exit_price - entry_price) / entry_price * side
        # Costs for this trade = entry_cost + exit_cost (some part can come from flip split)
        net = gross - extra_cost

        trades.append(
            {
                "entry_time": entry_time,
                "exit_time": exit_time,
                "side": "Long" if side > 0 else "Short",
                "entry_price": float(entry_price),
                "exit_price": float(exit_price),
                "return_gross": float(gross),
                "cost_paid": float(extra_cost),
                "pnl_net": float(net),
            }
        )

    n = len(pos_arr)
    # Start from t=1 because "execution time" for a position change at t is close[t-1]
    for t in range(1, n):
        prev_p = pos_arr[t - 1]
        p = pos_arr[t]

        if p == prev_p:
            continue

        # Position changed at bar t (effective execution at close[t-1])
        exec_bar = t - 1
        exec_price = closes[exec_bar]
        exec_time = idx[exec_bar]

        change_abs = abs(p - prev_p)
        event_cost = change_abs * cost_half  # same as vector cost at bar t

        # Case 1) Close existing trade if prev_p != 0
        if prev_p != 0:
            # If flip (prev!=0 and new!=0), split event cost half to closing, half to opening
            if p != 0:
                close_cost = event_cost * 0.5
                open_cost = event_cost * 0.5
            else:
                close_cost = event_cost
                open_cost = 0.0

            # Close trade with accumulated entry-cost (pending_entry_cost) + close_cost
            _close_trade(
                exit_bar=exec_bar,
                exit_price=exec_price,
                exit_time=exec_time,
                side=prev_p,
                extra_cost=(pending_entry_cost + close_cost),
            )

            # Reset active trade
            current_pos = 0.0
            entry_bar = None
            entry_price = None
            entry_time = None
            pending_entry_cost = 0.0

            # If flip, we will open new trade immediately and attach open_cost as entry cost
            if p != 0:
                current_pos = p
                entry_bar = exec_bar
                entry_price = exec_price
                entry_time = exec_time
                pending_entry_cost = open_cost

        # Case 2) Open new trade if prev_p == 0 and p != 0
        elif prev_p == 0 and p != 0:
            current_pos = p
            entry_bar = exec_bar
            entry_price = exec_price
            entry_time = exec_time
            # event_cost here is entry half cost
            pending_entry_cost = event_cost

        # If prev_p == 0 and p == 0 can't happen here (no change)
        # If prev_p != 0 and p == 0 was handled in close

    # Close any open trade at end-of-series at last close
    if current_pos != 0 and entry_price is not None:
        final_price = closes[-1]
        final_time = idx[-1]
        # Exit cost at end is "virtual" only if we decide to force close.
        # To match equity curve behavior, we SHOULD force close and charge exit half cost.
        end_exit_cost = abs(0 - current_pos) * cost_half  # = cost_half
        _close_trade(
            exit_bar=n - 1,
            exit_price=final_price,
            exit_time=final_time,
            side=current_pos,
            extra_cost=(pending_entry_cost + end_exit_cost),
        )

    df_trades = pd.DataFrame(trades)

    # 5) Metrics
    total_ret = float(equity.iloc[-1] - 1.0)

    running_max = equity.cummax()
    drawdown = (equity - running_max) / running_max
    max_drawdown = float(drawdown.min())

    if len(df_trades) > 0:
        win_mask = df_trades["pnl_net"] > 0
        total_count = int(len(df_trades))
        win_rate = float(win_mask.mean())

        gross_win = float(df_trades.loc[win_mask, "pnl_net"].sum())
        gross_loss = float(df_trades.loc[~win_mask, "pnl_net"].sum())  # negative or zero
        profit_factor = float(abs(gross_win / gross_loss)) if gross_loss < 0 else np.inf

        avg_win = float(df_trades.loc[win_mask, "pnl_net"].mean()) if win_mask.any() else 0.0
        avg_loss = float(df_trades.loc[~win_mask, "pnl_net"].mean()) if (~win_mask).any() else 0.0
        avg_loss_abs = float(abs(avg_loss))
        win_loss_ratio = float(avg_win / avg_loss_abs) if avg_loss_abs > 0 else np.inf

        cost_paid_total = float(df_trades["cost_paid"].sum())
    else:
        total_count = 0
        win_rate = 0.0
        profit_factor = 0.0
        avg_win = 0.0
        avg_loss = 0.0
        avg_loss_abs = 0.0
        win_loss_ratio = 0.0
        cost_paid_total = 0.0

    return {
        "strategy": strategy.NAME,
        "roi": total_ret,
        "max_drawdown": max_drawdown,
        "trades": total_count,
        "win_rate": win_rate,
        "profit_factor": profit_factor,
        "avg_win": avg_win,
        "avg_loss": avg_loss,
        "avg_loss_abs": avg_loss_abs,
        "win_loss_ratio": win_loss_ratio,
        "cost_paid_total": cost_paid_total,
        "equity_curve": equity,
        "signals": signals,
        "positions": positions,
        "gross_ret": gross_ret,
        "costs": costs,
        "net_ret": net_ret,
        "trade_log": df_trades,
    }
