# garam_core/fastlane/policy_eval.py
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Literal
from dataclasses import dataclass

StrategyType = Literal["MOMENTUM", "MEAN_REVERSION"]
MRMode = Literal["Z", "RSI", "BB"]

@dataclass(frozen=True)
class PolicyParams:
    # Selector
    strategy_type: StrategyType = "MOMENTUM"
    
    # --- Momentum Core ---
    momentum_n: int = 20
    min_momentum_k: float = 1.0
    zscore_min: float = 0.0
    abs_momentum_floor: float = 0.002
    cost_floor: float = 0.0025
    
    # --- Mean Reversion Core (Phase 20) ---
    mr_mode: MRMode = "Z"
    
    # 1. Z-Score Mode params
    mr_z_entry: float = -1.5
    mr_z_exit: float = 0.0
    
    # 2. RSI Mode params
    mr_rsi_entry: float = 30.0
    mr_rsi_exit: float = 50.0
    
    # 3. BB Mode params
    # Entry is implied (Close < Low)
    # Exit type: "MID" (Mean) or "LOW_1S" (Low + 1sigma approx)
    # We will use simple logic: Exit > bb_mid or Exit > bb_mid - 1*std
    mr_bb_exit_sigma_from_mid: float = 0.0 # 0.0 = Mid, -1.0 = Mid - 1*Std
    
    # Safety & Filter
    mr_stop_loss: float = 0.0 
    use_ma_filter: bool = False # Regime Gate (ma_60)

    # --- Shared ---
    fixed_hold: bool = False
    max_hold_bars: int = 120
    use_vol_scaled_cooldown: bool = False
    cooldown_target_vol: float = 0.01
    cooldown_bars: int = 30
    cooldown_min: int = 30
    cooldown_max: int = 360
    
    # --- Cost Model ---
    fee: float = 0.00015
    slippage: float = 0.0005
    tax: float = 0.0020
    cost_per_trade: float = 0.0 

class PolicyEval:
    def __init__(self, df: pd.DataFrame):
        self.df = df
        
    def evaluate(self, params: PolicyParams) -> Dict[str, Any]:
        if self.df is None or self.df.empty:
            return self._empty_result()
        
        df = self.df
        
        # 1. Data Prep (Vectorized)
        try:
            close_vals = df["close"].to_numpy(dtype=float)
            
            # Timestamp (UTC)
            ts_series = pd.to_datetime(df["date"], utc=True, errors="coerce")
            ts_vals = ts_series.dt.tz_convert("UTC").dt.tz_localize(None).to_numpy(dtype="datetime64[ns]")
            
            # Momentum Features (Shared)
            mom_col = f"mom_{params.momentum_n}"
            vol_col = f"vol_{params.momentum_n}"
            if mom_col not in df.columns: mom_col = "mom_20"
            if vol_col not in df.columns: vol_col = "vol_20"
            
            mom_vals = df[mom_col].to_numpy(dtype=float)
            vol_vals = df[vol_col].to_numpy(dtype=float)
            z_vals = np.divide(mom_vals, vol_vals, out=np.zeros_like(mom_vals), where=vol_vals > 1e-12)
            
            # Phase 20 Features (MR)
            # Use 'get' to handle existing caches without new features initially safely? 
            # Ideally FeatureStore is updated. We assume it is.
            rsi_vals = df.get("rsi_14", pd.Series(np.full(len(df), 50.0))).to_numpy(dtype=float)
            bb_mid = df.get("bb_mid_20", pd.Series(close_vals)).to_numpy(dtype=float)
            bb_low = df.get("bb_low_20", pd.Series(close_vals)).to_numpy(dtype=float)
            if "bb_mid_20" in df.columns:
                 # Approximate std for flexible exit if needed
                 bb_std = (df["bb_up_20"] - bb_mid) / 2.0
                 bb_std = bb_std.to_numpy(dtype=float)
            else:
                 bb_std = np.zeros_like(close_vals)
            
            # Filter
            ma_60 = df.get("ma_60", pd.Series(close_vals)).to_numpy(dtype=float)

        except Exception as e:
            print(f"[PolicyEval] Data Prep Error: {e}")
            return self._empty_result()

        # Costs
        cost_sum = (params.fee * 2) + (params.slippage * 2) + params.tax
        if cost_sum == 0.0 and params.cost_per_trade > 0:
            cost_sum = params.cost_per_trade
            
        robust_days = max(1, len(df) / 360.0) # approx
        
        # --- Execution ---
        equity = 1.0
        trades_detail = []
        n_bars = len(close_vals)
        i = 0
        cooldown = 0
        
        # Momentum KPIs
        count_hit_raw = 0; count_hit_abs = 0; count_hit_cost = 0

        # >>> MEAN REVERSION <<<
        if params.strategy_type == "MEAN_REVERSION":
            while i < n_bars:
                if cooldown > 0:
                    cooldown -= 1
                    i += 1
                    continue
                
                # 1. Regime Gate (Trend Filter)
                # If enabled, only buy if Close > MA60 (Simple Filter)
                # Wait, User said "Entry close >= ma_60 (Block crashes)".
                # Actually for MR buying dips, usually you want to buy *pullbacks* in uptrend.
                # So Close > MA60 is correct (Trend is Up, Price dipped).
                # But if we want to catch crashes, we turn this off.
                if params.use_ma_filter:
                    if close_vals[i] < ma_60[i]:
                        i += 1
                        continue

                is_entry = False
                
                # 2. Logic MUX
                if params.mr_mode == "Z":
                    if z_vals[i] < params.mr_z_entry: is_entry = True
                elif params.mr_mode == "RSI":
                    if rsi_vals[i] < params.mr_rsi_entry: is_entry = True
                elif params.mr_mode == "BB":
                    if close_vals[i] < bb_low[i]: is_entry = True

                if is_entry:
                    entry_idx = i
                    entry_price = close_vals[i]
                    
                    exit_idx = -1
                    limit = min(n_bars, i + params.max_hold_bars + 1)
                    stop_px = entry_price * (1.0 - params.mr_stop_loss) if params.mr_stop_loss > 0 else -np.inf
                    
                    # Exit Loop
                    for j in range(i + 1, limit):
                        # Stop
                        if close_vals[j] < stop_px:
                            exit_idx = j
                            break
                        
                        # Logic Exit
                        should_exit = False
                        if params.mr_mode == "Z":
                            if z_vals[j] > params.mr_z_exit: should_exit = True
                        elif params.mr_mode == "RSI":
                            if rsi_vals[j] > params.mr_rsi_exit: should_exit = True
                        elif params.mr_mode == "BB":
                            # Target = Mid + (Sigma * Std)
                            # e.g. Sigma=0.0 -> Mid. Sigma=-1.0 -> Mid - 1*Std.
                            target = bb_mid[j] + (params.mr_bb_exit_sigma_from_mid * bb_std[j])
                            if close_vals[j] > target: should_exit = True
                            
                        if should_exit:
                            exit_idx = j
                            break
                    
                    if exit_idx == -1:
                        exit_idx = limit - 1 if limit > i + 1 else i
                        
                    # Exec
                    exit_price = close_vals[exit_idx]
                    r_gross = (exit_price - entry_price) / entry_price
                    r_net = r_gross - cost_sum
                    equity *= (1.0 + r_net)
                    
                    self._record_trade(
                        trades_detail, ts_vals, entry_idx, exit_idx, 
                        entry_price, exit_price, r_gross, r_net, cost_sum,
                        ["MR", params.mr_mode]
                    )
                    
                    cooldown = params.cooldown_bars
                    i = exit_idx + 1
                else:
                    i += 1

        # >>> MOMENTUM (Legacy) <<<
        else:
            # Same Momentum Logic as before ...
            thresh_raw = params.min_momentum_k * vol_vals
            thresh_final = np.maximum(np.maximum(thresh_raw, params.abs_momentum_floor), params.cost_floor)
            is_signal = (mom_vals >= thresh_final) & (z_vals >= params.zscore_min)
            
            while i < n_bars:
                if cooldown > 0:
                    cooldown -= 1
                    i += 1
                    continue
                if is_signal[i]:
                    entry_idx = i
                    entry_price = close_vals[i]
                    # ... (Legacy Exec) ...
                    entry_thresh = thresh_final[i]
                    if thresh_final[i] <= (thresh_raw[i]+1e-9): count_hit_raw += 1
                    
                    exit_idx = -1
                    limit = min(n_bars, i + params.max_hold_bars + 1)
                    
                    for j in range(i + 1, limit):
                        if mom_vals[j] < (entry_thresh * 0.8):
                            exit_idx = j
                            break
                    if exit_idx == -1: exit_idx = limit - 1 if limit > i+1 else i
                    
                    exit_price = close_vals[exit_idx]
                    r_gross = (exit_price - entry_price) / entry_price
                    r_net = r_gross - cost_sum
                    equity *= (1.0 + r_net)
                    
                    self._record_trade(trades_detail, ts_vals, entry_idx, exit_idx, 
                                       entry_price, exit_price, r_gross, r_net, cost_sum, ["MOMENTUM"])
                                       
                    cooldown = params.cooldown_bars
                    i = exit_idx + 1
                else:
                    i += 1

        # --- Metrics ---
        trades = len(trades_detail)
        
        if trades > 0:
            total_net = sum(t["return_net"] for t in trades_detail)
            wins = sum(1 for t in trades_detail if t["return_net"] > 0)
            expectancy_net = total_net / trades
            win_rate = wins / trades
            hit_raw_ratio = count_hit_raw / trades
        else:
            expectancy_net = 0.0
            win_rate = 0.0
            hit_raw_ratio = 0.0
            
        return {
            "total_return": equity - 1.0,
            "trades": trades,
            "tpd": trades / robust_days,
            "expectancy_net": float(expectancy_net),
            "win_rate": float(win_rate),
            "trades_detail": trades_detail,
            "hit_raw_ratio": hit_raw_ratio 
        }

    def _record_trade(self, details, ts_vals, entry, exit, ep, xp, rg, rn, cost, tags):
        entry_ts = str(ts_vals[entry]) if not pd.isna(ts_vals[entry]) else None
        exit_ts = str(ts_vals[exit]) if not pd.isna(ts_vals[exit]) else None
        details.append({
            "entry_idx": int(entry), "exit_idx": int(exit),
            "entry_ts": entry_ts, "exit_ts": exit_ts,
            "entry_price": float(ep), "exit_price": float(xp),
            "return_gross": float(rg), "return_net": float(rn),
            "total_cost": float(cost), "bars_held": int(exit - entry),
            "tags": tags
        })
    
    def _empty_result(self):
        return {"total_return": 0.0, "trades": 0, "expectancy_net": 0.0, "win_rate": 0.0, "trades_detail": []}
