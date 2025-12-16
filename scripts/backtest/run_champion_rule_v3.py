"""
Champion Rule v3.0 Backtest Engine
- Multi-Champion Selection
- Challenger Exploration (Partial Swaps)
- Separation of Ranking, Selection, and Allocation
"""

import pandas as pd
import numpy as np
import yaml
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root.parent))

print(f"DEBUG: project_root = {project_root}")
print(f"DEBUG: sys.path[0] = {sys.path[0]}")
print(f"DEBUG: Checking if garam package exists: {(project_root / 'garam').exists()}")
print(f"DEBUG: Checking if garam/scoring exists: {(project_root / 'garam' / 'scoring').exists()}")


from config import PATHS
from regime.micro_regime import calculate_latest_micro_regime

class Position:
    def __init__(self, symbol, entry_price, qty, entry_time, entry_score, weight=0.0):
        self.symbol = symbol
        self.entry_price = entry_price
        self.qty = qty
        self.entry_time = entry_time
        self.entry_score = entry_score
        self.weight = weight # Target weight in portfolio
        self.exit_price = None
        self.exit_time = None
        self.exit_reason = None
        self.pnl = 0.0
        self.is_exploration = False # True if this is a "trial" position

    def update(self, current_price, current_time):
        # Calculate unrealized PnL
        return (current_price - self.entry_price) / self.entry_price

    def close(self, price, time, reason):
        self.exit_price = price
        self.exit_time = time
        self.exit_reason = reason
        self.pnl = (self.exit_price - self.entry_price) * self.qty
        return self.pnl

def apply_regime_parameters(config, regime):
    """
    Override config parameters based on the current regime.
    Uses deep merge for specific sections.
    """
    overrides = config.get('regime_overrides', {}).get(regime, {})
    if not overrides:
        return config
        
    import copy
    new_config = copy.deepcopy(config)
    
    # 1. Selection overrides
    if 'selection' not in new_config: new_config['selection'] = {}
    for k in ['gate_score', 'max_positions', 'challenger_pool_size', 'min_candidates']:
        if k in overrides:
            new_config['selection'][k] = overrides[k]
            
    # 2. Allocation overrides
    if 'allocation' not in new_config: new_config['allocation'] = {}
    for k in ['champion_budget']:
        if k in overrides:
            new_config['allocation'][k] = overrides[k]
            
    # 3. Exploration overrides
    if 'exploration' not in new_config: new_config['exploration'] = {}
    for k in ['exploration_fraction']:
        if k in overrides:
            new_config['exploration'][k] = overrides[k]
            
    return new_config

def load_config(profile_path):
    with open(profile_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def select_champions_and_challengers(scores, positions, cfg):
    """
    Multi-Alpha 환경용 Selection 로직 (게이트 실패시 Fallback 포함)

    - gate_score 이상인 종목이 너무 적으면,
      상위 min_candidates 까지는 gate_score와 무관하게 강제로 채운다.
    - R7_CRASH 처럼 max_positions=0 인 경우에는 완전 캐시 유지.
    """
    selection_cfg = cfg.get('selection', {})
    gate_score = selection_cfg.get('gate_score', -np.inf)
    max_positions = selection_cfg.get('max_positions', 0)
    challenger_pool_size = selection_cfg.get('challenger_pool_size', 10)
    min_candidates = selection_cfg.get('min_candidates', max_positions)
    
    # 완전 캐시 레짐 (예: R7_CRASH)
    if max_positions == 0:
        return [], []

    # 점수 있는 종목만 추출
    scored = []
    for sym, score in scores.items():
        if score is None:
            continue
        try:
            v = float(score)
        except (TypeError, ValueError):
            continue
        if pd.isna(v):
            continue
        scored.append((sym, v))
        
    if not scored:
        return [], []
        
    # 점수 순으로 정렬 (내림차순)
    scored.sort(key=lambda x: x[1], reverse=True)
    
    # gate_score 필터
    gated = [x for x in scored if x[1] >= gate_score]
    
    # 게이트 통과 종목이 너무 적으면 Fallback: 상위 min_candidates 까지는 강제로 포함
    if len(gated) < min_candidates:
        fallback_k = max(min_candidates, max_positions)
        gated = scored[:fallback_k]
        
    # 최종 챔피언/챌린저 풀
    champions = gated[:max_positions]
    challengers = gated[max_positions : max_positions + challenger_pool_size]
    
    return champions, challengers

def build_target_weights(champions, challengers, positions, cfg, current_equity):
    """
    Calculate target weights for Champions and Exploration trades.
    """
    target_exposure = cfg['allocation']['target_gross_exposure']
    scheme = cfg['allocation']['scheme']
    
    target_weights = {}
    
    # 1. Basic Allocation for Champions
    if not champions:
        return {}
        
    num_champions = len(champions)
    
    if scheme == 'tiered':
        # Tiered Allocation: Champion -> Co-Champion -> Challengers
        champion_budget = cfg['allocation'].get('champion_budget', 0.8)
        exploration_fraction = cfg['exploration'].get('exploration_fraction', 0.2)
        
        # Tilt Parameters
        tilt_threshold = cfg['allocation'].get('tilt_threshold', 0.10)
        tilt_fraction = cfg['allocation'].get('tilt_fraction', 0.25)
        
        # 1. Allocate to Champions
        current_exposure = 0.0
        if num_champions > 0:
            champ_total_weight = min(target_exposure * champion_budget, target_exposure)
            
            # Basic Equal Split first
            base_champ_w = champ_total_weight / num_champions
            for sym, score in champions:
                target_weights[sym] = base_champ_w
                
            # Apply Tilt if we have exactly 2 champions
            if num_champions == 2:
                c1_sym, c1_score = champions[0]
                c2_sym, c2_score = champions[1]
                
                score_diff = c1_score - c2_score
                if score_diff > tilt_threshold:
                    # Shift tilt_fraction of C2's weight to C1
                    shift_amount = target_weights[c2_sym] * tilt_fraction
                    target_weights[c1_sym] += shift_amount
                    target_weights[c2_sym] -= shift_amount
            
            current_exposure = sum(target_weights.values())

        # 2. Allocate to Challengers (Exploration)
        # Use explicit exploration_fraction, but cap at remaining exposure
        if cfg['exploration'].get('enabled', False) and challengers:
            remaining_exposure = target_exposure - current_exposure
            
            # Target for exploration is exploration_fraction * target_exposure (or just raw fraction?)
            # Let's assume exploration_fraction is % of Equity.
            target_exploration = target_exposure * exploration_fraction
            
            # Cap at remaining
            actual_exploration = min(target_exploration, remaining_exposure)
            
            if actual_exploration > 0.01:
                # Limit challengers
                max_challengers = cfg['selection'].get('challenger_pool_size', 5)
                real_challengers = challengers[:max_challengers]
                num_challengers = len(real_challengers)
                
                if num_challengers > 0:
                    challenger_w = actual_exploration / num_challengers
                    for sym, score in real_challengers:
                        target_weights[sym] = challenger_w

    elif scheme == 'equal':
        base_weight = target_exposure / num_champions
        for sym, score in champions:
            target_weights[sym] = base_weight
            
    elif scheme == 'score_proportional':
        total_score = sum(s for _, s in champions)
        if total_score > 0:
            for sym, score in champions:
                target_weights[sym] = target_exposure * (score / total_score)
        else:
             # Fallback
            base_weight = target_exposure / num_champions
            for sym, score in champions:
                target_weights[sym] = base_weight
                
    # 2. Exploration Logic (Partial Swaps)
    if cfg['exploration']['enabled']:
        # Identify Worst Champion
        if champions:
            worst_champion = min(champions, key=lambda x: x[1])
            sym_w, score_w = worst_champion
            
            # Check Challengers
            switch_threshold = cfg['exploration']['switch_threshold']
            exploration_fraction = cfg['exploration']['exploration_fraction']
            
            for sym_c, score_c in challengers:
                # Simple Advantage Calculation (Score Diff)
                # In future, add cost/risk penalty
                advantage = score_c - score_w
                
                if advantage > switch_threshold:
                    # Plan Swap: Reduce Worst Champion, Add Challenger
                    if sym_w in target_weights:
                        reduce_amt = target_weights[sym_w] * exploration_fraction
                        target_weights[sym_w] -= reduce_amt
                        target_weights[sym_c] = reduce_amt
                        # Only support 1 swap per day for simplicity in this version
                        break
                        
    return target_weights

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", required=True, help="Path to profile yaml")
    parser.add_argument("--universe-file", required=True)
    parser.add_argument("--scores-file", required=True)
    parser.add_argument("--results-dir", required=True)
    args = parser.parse_args()
    
    print(f"=== Champion Rule v3.0 Backtest ===")
    print(f"Profile: {args.profile}")
    
    cfg = load_config(args.profile)
    
    # Load Data
    print("Loading data...")
    # Force dtype=str to preserve leading zeros in symbols
    universe_df = pd.read_csv(args.universe_file, dtype={'symbol': str})
    universe_symbols = universe_df['symbol'].tolist()
    
    scores_df = pd.read_csv(args.scores_file, dtype={'symbol': str})
    scores_df['date'] = pd.to_datetime(scores_df['date'])
    
    # Pivot Scores
    score_matrix = scores_df.pivot(index='date', columns='symbol', values='score')
    
    # Load Minute Data (for execution)
    minute_dir = Path("g:/내 드라이브/garamdata/history/minute")
    minute_data = {}
    print(f"Checking minute data in: {minute_dir}")
    print(f"Universe symbols len: {len(universe_symbols)}")
    print(f"Universe symbols (first 5): {universe_symbols[:5]}")
    print(f"Universe symbols type: {[type(x) for x in universe_symbols[:5]]}")
    
    # Debug: List actual files
    actual_files = list(minute_dir.glob("*_1m.csv"))
    actual_symbols = [f.stem.split('_')[0] for f in actual_files]
    print(f"Actual files in dir: {len(actual_files)}")
    print(f"Actual symbols (first 5): {actual_symbols[:5]}")
    print(f"Actual symbols type: {[type(x) for x in actual_symbols[:5]]}")
    
    # Check intersection
    common = set(universe_symbols) & set(actual_symbols)
    print(f"Common symbols: {len(common)}")
    print(f"Common (first 5): {list(common)[:5]}")
    
    # Print differences
    diff = set(universe_symbols) - set(actual_symbols)
    print(f"In Universe but not in Dir: {len(diff)}")
    if diff:
        print(f"Example missing: {list(diff)[:5]}")
    
    for sym in universe_symbols:
        p = minute_dir / f"{sym}_1m.csv"
        if not p.exists():
            # Try with 'KR_' prefix or other patterns if needed
            # But list_dir showed '005930_1m.csv' so it should match
            # print(f"File not found: {p}")
            pass
            
        if p.exists():
            df = pd.read_csv(p)
            # Basic cleanup
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
                df.set_index('date', inplace=True)
            elif 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df.set_index('timestamp', inplace=True)
            
            # Filter for 2024-12 ~ 
            # Relaxed filter: Load all, let simulation loop handle it
            # df = df[df.index >= pd.to_datetime("2024-12-01")]
            
            if not df.empty:
                minute_data[sym] = df
                # print(f"Loaded {sym}: {df.index[0]} ~ {df.index[-1]}")
            
    print(f"Loaded minute data for {len(minute_data)} symbols.")
    
    # Load Market Proxy (005930) for Regime
    market_proxy_file = Path("g:/내 드라이브/garamdata/history/KR_005930_SamsungElec_daily_20y.csv")
    if not market_proxy_file.exists():
        market_proxy_file = Path("g:/내 드라이브/garamdata/history/daily/KR_005930_SamsungElec_daily_20y.csv")
        
    market_history = pd.DataFrame()
    if market_proxy_file.exists():
        market_history = pd.read_csv(market_proxy_file)
        if 'date' in market_history.columns:
            market_history['date'] = pd.to_datetime(market_history['date'])
            market_history.set_index('date', inplace=True)
        elif 'timestamp' in market_history.columns:
            market_history['timestamp'] = pd.to_datetime(market_history['timestamp'])
            market_history.set_index('timestamp', inplace=True)
        market_history.sort_index(inplace=True)
        print(f"Loaded Market Proxy (005930) for Regime: {len(market_history)} rows")
    else:
        print("Warning: Market Proxy file not found. Regime will default to R4_BOX.")

    # --- Multi-Alpha Engine Setup ---
    from garam.scoring.multi_alpha_aggregator import MultiAlphaAggregator
    
    print("Initializing Multi-Alpha Engine...")
    alpha_catalog_path = project_root / "config" / "alpha_catalog.yaml"
    aggregator = MultiAlphaAggregator(str(alpha_catalog_path))
    
    # Load Daily Data for Universe (for A3/A4)
    print("Loading Daily Data for Alpha Computation...")
    daily_dir = Path("g:/내 드라이브/garamdata/history/daily")
    
    # Containers for Market Data
    df_close = pd.DataFrame()
    df_open = pd.DataFrame()
    df_high = pd.DataFrame()
    df_low = pd.DataFrame()
    df_volume = pd.DataFrame()
    
    loaded_cnt = 0
    for sym in universe_symbols:
        p = daily_dir / f"{sym}_daily.csv"
        if p.exists():
            df = pd.read_csv(p)
            # Normalize Date
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
                df.set_index('date', inplace=True)
            elif 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df.set_index('timestamp', inplace=True)
            
            # Clean duplicates
            df = df[~df.index.duplicated(keep='last')]
            
            # Append to master DFs (using concat/merge is slow in loop, but for 50 items ok)
            # Better: collect Series then concat
            if 'close' in df.columns: df_close[sym] = df['close']
            if 'open' in df.columns: df_open[sym] = df['open']
            if 'high' in df.columns: df_high[sym] = df['high']
            if 'low' in df.columns: df_low[sym] = df['low']
            if 'volume' in df.columns: df_volume[sym] = df['volume']
            loaded_cnt += 1
            
    print(f"Loaded daily data for {loaded_cnt} symbols.")
    
    # Load Intraday Features (A2)
    print("Loading Intraday Features...")
    intraday_file = project_root / "GARAM_Data" / "intraday_features.parquet"
    df_intraday = pd.DataFrame()
    
    if intraday_file.exists():
        try:
            df_intraday = pd.read_parquet(intraday_file)
            # It's MultiIndex (date, symbol). We need to pivot to Wide Format for each feature.
            # Features: intraday_morning_ret, intraday_afternoon_ret, intraday_trend_q, intraday_range_pos, intraday_vol_rel
        except Exception as e:
            print(f"Failed to load parquet: {e}")
            
    # Prepare market_data dict
    market_data = {
        'daily_close': df_close.sort_index(),
        'daily_open': df_open.sort_index(),
        'daily_high': df_high.sort_index(),
        'daily_low': df_low.sort_index(),
        'daily_volume': df_volume.sort_index()
    }
    
    if not df_intraday.empty:
        # Pivot and add to market_data
        features = ['intraday_morning_ret', 'intraday_afternoon_ret', 'intraday_trend_q', 'intraday_range_pos', 'intraday_vol_rel']
        for feat in features:
            if feat in df_intraday.columns:
                # Reset index to pivot
                if isinstance(df_intraday.index, pd.MultiIndex):
                    df_temp = df_intraday.reset_index()
                else:
                    df_temp = df_intraday.copy()
                    
                df_wide = df_temp.pivot(index='date', columns='symbol', values=feat)
                market_data[feat] = df_wide.sort_index()
                print(f"  Loaded feature: {feat} {df_wide.shape}")
    
    # Pre-compute Alphas
    print("Pre-computing Alpha Scores...")
    raw_alpha_scores = aggregator.precompute_all_alphas(market_data, universe_symbols)
    for aid, sdf in raw_alpha_scores.items():
        print(f"  {aid}: {sdf.shape}")

    # Simulation Loop
    cash = cfg['capital']['initial_equity']
    positions = {} # sym -> Position
    trades_history = []
    equity_curve = []
    
    dates = score_matrix.index.sort_values()
    dates = [d for d in dates if d >= pd.to_datetime("2024-12-02")]
    
    print(f"Simulation Period: {dates[0]} ~ {dates[-1]} ({len(dates)} days)")
    
    for d in dates:
        # 0. Determine Regime
        current_regime = "R4_BOX"
        if not market_history.empty:
            # Get history up to d-1 (Yesterday)
            # If d is Monday, d-1 is Sunday. We need last trading day.
            # slice: market_history.loc[:d] includes d.
            # We want strictly before d?
            # calculate_latest_micro_regime uses the LAST row of the DF passed.
            # So if we pass history up to d-1, it uses d-1 close.
            
            # Efficient slicing
            # history_subset = market_history.loc[:d - timedelta(days=1)]
            # But loc slicing by date works even if date not in index.
            
            # Optimization: Don't slice every time if possible.
            # But we need expanding window.
            # Let's just slice.
            
            history_subset = market_history.loc[:d - timedelta(days=1)]
            if not history_subset.empty:
                current_regime = calculate_latest_micro_regime(history_subset)
        
        # Apply Regime Overrides
        active_config = apply_regime_parameters(cfg, current_regime)
        
        # Debug Regime
        print(f"Date: {d}, Regime: {current_regime}")
        
        # Calculate Benchmark (005930)
        bench_val = cfg['capital']['initial_equity']
        if not market_history.empty:
            # Find closest price
            try:
                # We need the price at start of sim to normalize
                if 'initial_bench_price' not in locals():
                    # Find first valid price in sim period
                    start_date = dates[0]
                    if start_date in market_history.index:
                        initial_bench_price = market_history.at[start_date, 'close']
                    else:
                        # Fallback
                        initial_bench_price = market_history['close'].iloc[0]
                
                if d in market_history.index:
                    curr_bench_price = market_history.at[d, 'close']
                    bench_val = (curr_bench_price / initial_bench_price) * cfg['capital']['initial_equity']
            except:
                pass

        # 1. Get Daily Scores
        if d not in score_matrix.index: continue
        daily_scores_a1 = score_matrix.loc[d]
        
        # Multi-Alpha Aggregation
        daily_scores = aggregator.aggregate_daily_score(d, current_regime, raw_alpha_scores, daily_scores_a1)
        
        # Debug: Print top scores if A3/A4 active
        # if current_regime in ['R3_UP_BOX', 'R4_BOX']:
        #     print(f"  Top Scores ({current_regime}):")
        #     print(daily_scores.nlargest(3))
        
        # 2. Calculate Portfolio Value & Handle Morning Stops
        current_equity = cash
        
        # [S6] Manage Blacklist
        # Decrement days remaining
        if 'blacklist' not in locals(): blacklist = {} # sym -> days_remaining
        expired_blacklist = []
        for sym in blacklist:
            blacklist[sym] -= 1
            if blacklist[sym] <= 0:
                expired_blacklist.append(sym)
        for sym in expired_blacklist:
            del blacklist[sym]
            
        # [S6] Morning Stop Logic
        exec_cfg = active_config.get('execution', {})
        morning_stop_active = exec_cfg.get('morning_stop_loss', False)
        blacklist_duration = exec_cfg.get('blacklist_days', 0)
        
        symbols_to_morning_close = []
        
        for sym, pos in positions.items():
            # Get Price Data
            open_price = pos.entry_price
            prev_close = pos.entry_price
            
            if sym in minute_data:
                day_data = minute_data[sym][minute_data[sym].index.date == d.date()]
                if not day_data.empty:
                    open_price = day_data.iloc[0]['open']
            
            # Get Previous Close (from df_close if available)
            # We need yesterday's close.
            # Since we are at 'd', we can look at df_close.at[d-1] if exists?
            # Or just use the 'close' from market_data if we had it.
            # Simpler: Use pos.entry_price as proxy for "Cost Basis".
            # Rule: "Yesterday Loss" -> Current Price < Entry Price (roughly).
            # Rule: "Morning Down" -> Open < Prev Close.
            
            # Let's try to get actual Prev Close
            # We can use df_close shifted? Or just look up.
            # Optimization: We loaded df_close.
            # Find index location of d, take -1.
            
            # Simplified Logic for "Morning Weakness":
            # If (Open < Entry) AND (Open < Prev_Close_Approx)
            # We don't have easy access to Prev Close here without lookup.
            # Let's use: If (Open < pos.entry_price * 0.97) OR ...
            # User Rule: "전일 하락(Loss) & 오전 하락(Gap Down)"
            
            # 1. Check if we are in Loss (based on Open)
            is_loss = open_price < pos.entry_price
            
            # 2. Check Morning Weakness (Gap Down)
            # We need yesterday's close.
            yesterday_close = open_price # Fallback
            try:
                # Find date before d in df_close
                if sym in df_close.columns:
                    # Get series up to d
                    series = df_close[sym].loc[:d]
                    if len(series) >= 2:
                        yesterday_close = series.iloc[-2] # -1 is today (if data exists) or we are at d.
                        # Wait, df_close has data for 'd' usually.
                        # If we are running backtest, df_close contains future?
                        # Yes, we loaded entire history.
                        # So loc[:d] includes d. iloc[-2] is yesterday.
            except:
                pass
            
            is_gap_down = open_price < yesterday_close
            
            if morning_stop_active and is_loss and is_gap_down:
                # Trigger Morning Stop
                # print(f"  [Morning Stop] {sym}: Open {open_price} < Entry {pos.entry_price} & Prev {yesterday_close}")
                pos.close(open_price, d, "Morning Stop")
                cash += open_price * pos.qty * (1 - 0.002)
                trades_history.append(pos)
                symbols_to_morning_close.append(sym)
                
                # Add to Blacklist
                if blacklist_duration > 0:
                    blacklist[sym] = blacklist_duration
            else:
                # Mark to Market
                current_equity += open_price * pos.qty

        # Remove Morning Closed Positions
        for sym in symbols_to_morning_close:
            del positions[sym]
            
        # [S11] BB Profit Exit Logic
        bb_exit_threshold = exec_cfg.get('bb_profit_exit_threshold', 0.0)
        if bb_exit_threshold > 0:
            symbols_to_bb_close = []
            for sym, pos in positions.items():
                # Need History for BB
                if sym in df_close.columns:
                    # Get history up to d
                    # We need 20 days
                    series = df_close[sym].loc[:d]
                    if len(series) >= 20:
                        # Calculate BB (Period 20, k=1.0 - Hardcoded to match Alpha)
                        # Or use config? Alpha uses 20, 1.0.
                        # Let's assume 20, 1.0 for consistency with "A8".
                        window = 20
                        k = 1.0
                        
                        recent_close = series.iloc[-window:]
                        mid = recent_close.mean()
                        std = recent_close.std()
                        lower = mid - k * std
                        
                        # Distance (Mid - Low) = k * std
                        distance = k * std
                        
                        # Threshold Price
                        # "Mid + 0.6 * Distance"
                        exit_price_trigger = mid + bb_exit_threshold * distance
                        
                        current_close = series.iloc[-1]
                        
                        if current_close > exit_price_trigger:
                            # Trigger Profit Exit
                            # print(f"  [BB Exit] {sym}: Close {current_close:.0f} > Trigger {exit_price_trigger:.0f} (%b > 0.8)")
                            pos.close(current_close, d, "BB Profit Exit")
                            cash += current_close * pos.qty * (1 - 0.002)
                            trades_history.append(pos)
                            symbols_to_bb_close.append(sym)
                            
                            # Apply Profit Rest (if enabled)
                            profit_rest_days = exec_cfg.get('profit_rest_days', 0)
                            if profit_rest_days > 0:
                                blacklist[sym] = profit_rest_days

            for sym in symbols_to_bb_close:
                del positions[sym]

        # 3. Selection
        # Filter scores to exclude Blacklisted symbols
        valid_scores = daily_scores.copy()
        for sym in blacklist:
            if sym in valid_scores.index:
                valid_scores.drop(sym, inplace=True)
                
        champions, challengers = select_champions_and_challengers(valid_scores, positions, active_config)
        
        # 4. Allocation
        target_weights = build_target_weights(champions, challengers, positions, active_config, current_equity)
        
        # 5. Execution (Rebalance)
        # Turnover Control Setup
        # Turnover Control Setup
        exec_cfg = active_config.get('execution', {})
        max_turnover = exec_cfg.get('max_turnover_per_day', 1.0) * current_equity
        min_trade_size = exec_cfg.get('min_trade_size_pct', 0.0) * current_equity
        current_turnover = 0.0
        
        # Sell Logic
        symbols_to_close = []
        # Sort sells by size (largest first? or just iterate)
        # Actually, we should process sells first to free up cash.
        
        for sym, pos in list(positions.items()):
            target_w = target_weights.get(sym, 0.0)
            
            price = pos.entry_price
            if sym in minute_data:
                day_data = minute_data[sym][minute_data[sym].index.date == d.date()]
                if not day_data.empty:
                    price = day_data.iloc[0]['open']
            
            current_val = price * pos.qty
            current_w = current_val / current_equity if current_equity > 0 else 0
            
            trade_val = 0
            
            if target_w == 0:
                # Full Close
                trade_val = current_val
                # Allow partial close if exceeds turnover?
                # For closing, we usually want to exit fast.
                # But if we strictly enforce turnover...
                # Let's allow full close if it's a signal exit, but here it's allocation 0.
                # To be safe, let's cap it.
                allowed_val = max_turnover - current_turnover
                if allowed_val > 0:
                    close_qty = pos.qty
                    if trade_val > allowed_val:
                        # Partial close
                        close_qty = int(allowed_val / price)
                    
                    if close_qty > 0:
                        # [S9] Profit Rest Logic
                        # Check PnL before closing
                        # PnL = (Exit Price - Entry Price) * Qty
                        pnl = (price - pos.entry_price) * close_qty
                        
                        # Close Position
                        if close_qty == pos.qty:
                            pos.close(price, d, "Allocation 0")
                            cash += price * close_qty * (1 - 0.002)
                            trades_history.append(pos)
                            symbols_to_close.append(sym)
                            
                            # [S9] If Profitable, Rest
                            profit_rest_days = exec_cfg.get('profit_rest_days', 0)
                            if pnl > 0 and profit_rest_days > 0:
                                blacklist[sym] = profit_rest_days
                                
                        else:
                            pos.qty -= close_qty
                            cash += price * close_qty * (1 - 0.002)
                        
                        current_turnover += price * close_qty

            elif target_w < current_w * 0.9:
                # Reduce
                reduce_val = current_val - (target_w * current_equity)
                if reduce_val >= min_trade_size:
                    allowed_val = max_turnover - current_turnover
                    if allowed_val > 0:
                        actual_reduce_val = min(reduce_val, allowed_val)
                        reduce_qty = int(actual_reduce_val / price)
                        if reduce_qty > 0:
                            cash += price * reduce_qty * (1 - 0.002)
                            pos.qty -= reduce_qty
                            current_turnover += price * reduce_qty
        
        for sym in symbols_to_close:
            del positions[sym]
            
        # Buy Logic
        print(f"Date: {d}, Target Weights: {len(target_weights)}")
        for sym, target_w in target_weights.items():
            price = 0
            if sym in minute_data:
                day_data = minute_data[sym][minute_data[sym].index.date == d.date()]
                if not day_data.empty:
                    price = day_data.iloc[0]['open']
            
            if price == 0: 
                print(f"  No price for {sym}")
                continue
            
            target_val = target_w * current_equity
            # print(f"  {sym}: Target {target_val:,.0f}, Cash {cash:,.0f}")
            
            if sym in positions:
                # Add more?
                pos = positions[sym]
                current_val = price * pos.qty
                if target_val > current_val * 1.1: # Buffer
                    add_val = target_val - current_val
                    if add_val >= min_trade_size:
                        allowed_val = max_turnover - current_turnover
                        if allowed_val > 0:
                            actual_add_val = min(add_val, allowed_val)
                            if cash > actual_add_val:
                                add_qty = int(actual_add_val / price)
                                if add_qty > 0:
                                    cash -= price * add_qty * (1 + 0.002)
                                    pos.qty += add_qty
                                    current_turnover += price * add_qty
            else:
                # New Entry
                if target_val >= min_trade_size:
                    allowed_val = max_turnover - current_turnover
                    if allowed_val > 0:
                        actual_target_val = min(target_val, allowed_val)
                        
                        # Calculate max affordable value including fee
                        max_affordable_val = cash / (1 + 0.002)
                        buy_val = min(actual_target_val, max_affordable_val)
                        
                        if buy_val > 0:
                            qty = int(buy_val / price)
                            if qty > 0:
                                pos = Position(sym, price, qty, d, daily_scores.get(sym, 0), target_w)
                                positions[sym] = pos
                                cash -= price * qty * (1 + 0.002)
                                current_turnover += price * qty

        # [S7] Afternoon Stop Logic (Exit at Close)
        if exec_cfg.get('afternoon_stop_loss', False):
            blacklist_duration = exec_cfg.get('blacklist_days', 0)
            symbols_to_afternoon_close = []
            
            for sym, pos in positions.items():
                # We need Today's Close and Yesterday's Close
                today_close = 0
                yesterday_close = 0
                
                if sym in df_close.columns:
                    # Get series
                    series = df_close[sym]
                    # Check if d in index
                    if d in series.index:
                        today_close = series.at[d]
                        # Find loc of d
                        loc = series.index.get_loc(d)
                        if loc > 0:
                            yesterday_close = series.iloc[loc-1]
                
                if today_close > 0 and yesterday_close > 0:
                    # Rule: "전일 하락(Holding Loss) & 당일 하락(Drop)"
                    # 1. Holding Loss: Entry > Yesterday Close (We carried a loss into today)
                    #    Or simply: We are currently in loss?
                    #    User said: "전일 하락에" -> "If it was down yesterday" (relative to entry? or just a down day?)
                    #    Context: "Holding a loser". So Entry > Yesterday Close is a good proxy for "It was bad yesterday".
                    # 2. Morning/Today Drop: Today Close < Yesterday Close.
                    
                    was_loss_yesterday = pos.entry_price > yesterday_close
                    is_drop_today = today_close < yesterday_close
                    
                    if was_loss_yesterday and is_drop_today:
                        # Exit at Close
                        # print(f"  [Afternoon Stop] {sym}: Entry {pos.entry_price} > Prev {yesterday_close} & Curr {today_close} < Prev")
                        pos.close(today_close, d, "Afternoon Stop")
                        cash += today_close * pos.qty * (1 - 0.002)
                        trades_history.append(pos)
                        symbols_to_afternoon_close.append(sym)
                        
                        # Add to Blacklist
                        if blacklist_duration > 0:
                            blacklist[sym] = blacklist_duration

            for sym in symbols_to_afternoon_close:
                del positions[sym]

        # Update Equity Curve
        # Mark to Market (Close Price)
        mtm_value = 0
        for sym, pos in positions.items():
            price = pos.entry_price
            if sym in df_close.columns and d in df_close.index:
                c = df_close.at[d, sym]
                if c > 0: price = c
            mtm_value += price * pos.qty
            
        total_equity = cash + mtm_value
        equity_curve.append({'date': d, 'equity': total_equity, 'cash': cash, 'benchmark': bench_val})
        
    # Final Report
    initial_capital = cfg['capital']['initial_equity']
    final_equity = equity_curve[-1]['equity'] if equity_curve else initial_capital
    total_return = (final_equity - initial_capital) / initial_capital
    
    print("-" * 30)
    print(f"Final Equity: {final_equity:,.0f}")
    print(f"Total Return: {total_return*100:.2f}%")
    
    # Save Results
    os.makedirs(args.results_dir, exist_ok=True)
    pd.DataFrame(equity_curve).to_csv(Path(args.results_dir) / "equity.csv", index=False)
    
    # Save Trades
    trades_data = []
    for t in trades_history:
        trades_data.append({
            'symbol': t.symbol,
            'entry_time': t.entry_time,
            'exit_time': t.exit_time,
            'pnl': t.pnl,
            'return_pct': t.pnl / (t.entry_price * t.qty) if t.qty > 0 else 0,
            'exit_reason': t.exit_reason
        })
    pd.DataFrame(trades_data).to_csv(Path(args.results_dir) / "trades.csv", index=False)

if __name__ == "__main__":
    main()
