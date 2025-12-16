import os
import sys
import yaml
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import json
import logging

# Add project root to path
# Add project root to path
# Add project root to path
# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root)) # Add c:/garam/garam to path

print("SYS PATH:", sys.path)

# Direct imports from project root packages
try:
    from core.alpha_aggregator import AlphaAggregator
    from risk.pretrade_checks import PreTradeRiskManager
    from regime.micro_regime import calculate_latest_micro_regime
    # from engine.mss_engine import MarketSensingEngine # Replaced by HybridController
    from engine.controller import HybridController
    from config import PATHS
except ImportError as e:
    print(f"Import Error with direct path: {e}")
    # Fallback/Debug
    try:
        import garam.core.alpha_aggregator as AlphaAggregator
    except:
        raise
# from garam.engines.mss_engine import MarketSensingEngine # Replaced by HybridController
# Removed broken legacy imports (handled above)

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("paper_trading.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class LiveTradingEngine:
    def __init__(self, config_path, state_path="portfolio_state.json"):
        self.config_path = config_path
        self.state_path = state_path
        self.config = self.load_config()
        self.state = self.load_state()
        
        # Initialize Components
        # Initialize Components
        # self.aggregator = AlphaAggregator() # Replaced by LegacyEngine inside Controller
        self.risk_manager = PreTradeRiskManager()
        # self.mss = MarketSensingEngine() # Replaced by AdvancedEngine inside Controller
        self.controller = HybridController() # Dual Engine Controller
        
        # Data Storage
        self.data_dir = Path("g:/내 드라이브/garamdata/history")
        # Full Data (Cached)
        self.full_df_close = None
        self.full_df_open = None
        self.full_df_high = None
        self.full_df_low = None
        self.full_df_volume = None
        self.full_market_history = None
        
        # Current Cycle Data (Sliced)
        self.df_close = None
        self.df_open = None
        self.df_high = None
        self.df_low = None
        self.df_volume = None
        self.market_history = None

    def load_config(self):
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
            
    def load_state(self):
        if os.path.exists(self.state_path):
            with open(self.state_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # Initialize Default State
            initial_capital = self.config.get('capital', {}).get('initial_equity', 100_000_000)
            return {
                "cash": initial_capital,
                "positions": {}, # sym: {qty, entry_price, entry_date}
                "blacklist": {}, # sym: days_remaining
                "equity": initial_capital,
                "last_update": None
            }
            
    def save_state(self):
        with open(self.state_path, 'w', encoding='utf-8') as f:
            json.dump(self.state, f, indent=4, default=str)

    def load_market_data(self):
        # Check if full data is already loaded
        if self.full_df_close is not None and not self.full_df_close.empty:
            return True

        logger.info("Loading Market Data from CSVs...")
        
        # 1. Load Universe
        universe_cfg = self.config.get('universe', {})
        # Config key is 'file', default to real_universe_400.csv (Live V3)
        universe_path_str = universe_cfg.get('file', 'GARAM_Data/real_universe_400.csv')
        
        # Resolve path
        universe_file = Path(universe_path_str)
        if not universe_file.exists():
            # Try relative to project root
            p = project_root / universe_path_str
            if p.exists():
                universe_file = p
        
        # Fallback to default if still not found
        if not universe_file.exists():
            logger.warning(f"Universe file {universe_path_str} not found. Falling back to config/universe_kr_top50.yaml")
            universe_file = project_root / "config" / "universe_kr_top50.yaml"
            
        if not universe_file.exists():
            logger.error(f"Universe file not found: {universe_file}")
            return False
            
        with open(universe_file, 'r', encoding='utf-8') as f:
            # Check extension
            if universe_file.suffix == '.yaml':
                univ_data = yaml.safe_load(f)
                universe_symbols = univ_data.get('symbols', [])
            elif universe_file.suffix == '.csv':
                df_univ = pd.read_csv(universe_file)
                # Assume first column or 'symbol' column
                if 'symbol' in df_univ.columns:
                    universe_symbols = df_univ['symbol'].astype(str).tolist()
                elif 'code' in df_univ.columns:
                    universe_symbols = df_univ['code'].astype(str).tolist()
                else:
                    universe_symbols = df_univ.iloc[:, 0].astype(str).tolist()
            else:
                logger.error(f"Unknown universe file format: {universe_file.suffix}")
                return False
            
        logger.info(f"Universe Loaded from {universe_file}: {len(universe_symbols)} symbols")
        
        # 2. Load Daily Data
        daily_dir = Path("g:/내 드라이브/garamdata/history/daily")
        
        close_list = []
        open_list = []
        high_list = []
        low_list = []
        volume_list = []
        
        loaded_cnt = 0
        for sym in universe_symbols:
            p = daily_dir / f"{sym}_daily.csv"
            if p.exists():
                df = pd.read_csv(p)
                if 'date' in df.columns:
                    df['date'] = pd.to_datetime(df['date'])
                    df.set_index('date', inplace=True)
                elif 'timestamp' in df.columns:
                    df['timestamp'] = pd.to_datetime(df['timestamp'])
                    df.set_index('timestamp', inplace=True)
                else:
                    logger.warning(f"No date/timestamp column in {p}")
                    continue
                
                df = df[~df.index.duplicated(keep='last')]
                
                if 'close' in df.columns: close_list.append(df['close'].rename(sym))
                if 'open' in df.columns: open_list.append(df['open'].rename(sym))
                if 'high' in df.columns: high_list.append(df['high'].rename(sym))
                if 'low' in df.columns: low_list.append(df['low'].rename(sym))
                if 'volume' in df.columns: volume_list.append(df['volume'].rename(sym))
                loaded_cnt += 1
                
        if close_list: 
            self.full_df_close = pd.concat(close_list, axis=1)
            self.full_df_close.sort_index(inplace=True)
            print(f"DEBUG: Full Close Data Range: {self.full_df_close.index[0]} to {self.full_df_close.index[-1]}")
            print(f"DEBUG: Index Type: {self.full_df_close.index.dtype}")
            print(f"DEBUG: Tail:\n{self.full_df_close.tail()}")
            logger.info(f"Full Close Data Range: {self.full_df_close.index[0]} to {self.full_df_close.index[-1]}")
            logger.info(f"Index Type: {self.full_df_close.index.dtype}")
        else: 
            print("DEBUG: close_list is empty!")
            self.full_df_close = pd.DataFrame()
        
        if open_list: 
            self.full_df_open = pd.concat(open_list, axis=1)
            self.full_df_open.sort_index(inplace=True)
        else: self.full_df_open = pd.DataFrame()
        
        if high_list: 
            self.full_df_high = pd.concat(high_list, axis=1)
            self.full_df_high.sort_index(inplace=True)
        else: self.full_df_high = pd.DataFrame()
        
        if low_list: 
            self.full_df_low = pd.concat(low_list, axis=1)
            self.full_df_low.sort_index(inplace=True)
        else: self.full_df_low = pd.DataFrame()
        
        if volume_list: 
            self.full_df_volume = pd.concat(volume_list, axis=1)
            self.full_df_volume.sort_index(inplace=True)
        else: self.full_df_volume = pd.DataFrame()
        
        logger.info(f"Loaded Daily Data for {loaded_cnt} symbols. Shape: {self.full_df_close.shape}")
        
        # 3. Load Market History
        market_proxy_file = daily_dir / "005930_daily.csv"
        if market_proxy_file.exists():
            mh = pd.read_csv(market_proxy_file)
            if 'date' in mh.columns:
                mh['date'] = pd.to_datetime(mh['date'])
                mh.set_index('date', inplace=True)
            elif 'timestamp' in mh.columns:
                mh['timestamp'] = pd.to_datetime(mh['timestamp'])
                mh.set_index('timestamp', inplace=True)
            mh.sort_index(inplace=True)
            self.full_market_history = mh
            logger.info(f"Loaded Market History: {len(mh)} rows")
        else:
            logger.warning("Market Proxy file not found.")
            
        # NEW: Validate Score Freshness and Coverage
        self._validate_score_pipeline()
        
        return True

    def inject_realtime_data(self):
        """Inject real-time 1m data as 'Today's Daily Bar'"""
        try:
            today_str = datetime.now().strftime("%Y%m%d")
            today_date = pd.Timestamp(datetime.now().date())
            
            realtime_dir = PATHS.DATA_DIR / "kr" / "realtime" / "1m"
            if not realtime_dir.exists():
                logger.warning(f"Realtime dir not found: {realtime_dir}")
                return

            # Find today's files
            files = list(realtime_dir.glob(f"*_{today_str}.csv"))
            if not files:
                logger.warning(f"No realtime data found for {today_str}")
                return

            logger.info(f"Injecting Realtime Data for {today_date.date()} ({len(files)} symbols)...")
            
            new_data = {'open': {}, 'high': {}, 'low': {}, 'close': {}, 'volume': {}}
            
            for csv_file in files:
                try:
                    symbol = csv_file.name.split('_')[0]
                    
                    # Read CSV
                    df = pd.read_csv(csv_file)
                    if df.empty: continue
                    
                    # Last row is current status
                    last_row = df.iloc[-1]
                    
                    # First row is Open (approx)
                    first_row = df.iloc[0]
                    
                    # Extract OHLCV
                    # CSV Header: datetime,open,high,low,close,volume
                    close = float(last_row['close'])
                    daily_high = float(last_row['high']) 
                    daily_low = float(last_row['low'])
                    daily_vol = float(last_row['volume'])
                    
                    # Open from first row
                    open_px = float(first_row['open'])
                    
                    new_data['open'][symbol] = open_px
                    new_data['high'][symbol] = daily_high
                    new_data['low'][symbol] = daily_low
                    new_data['close'][symbol] = close
                    new_data['volume'][symbol] = daily_vol
                    
                except Exception as e:
                    logger.warning(f"Failed to parse {csv_file.name}: {e}")

            # Update DataFrames
            for field, data_dict in new_data.items():
                if not data_dict: continue
                
                # Create Today's Row
                today_df = pd.DataFrame(data_dict, index=[today_date])
                
                # Target DF
                target_df = getattr(self, f"full_df_{field}")
                
                # Remove today if exists (to overwrite)
                if today_date in target_df.index:
                    target_df = target_df.drop(today_date)
                
                # Filter to universe
                common_cols = target_df.columns.intersection(today_df.columns)
                if common_cols.empty: continue
                
                # Concat
                target_df = pd.concat([target_df, today_df[common_cols]])
                target_df.sort_index(inplace=True)
                
                setattr(self, f"full_df_{field}", target_df)
                
            logger.info(f"Successfully injected realtime data for {today_date.date()}")
            
        except Exception as e:
            logger.error(f"Error injecting realtime data: {e}")

    def run_daily_cycle(self, target_date=None):
        if target_date is None:
            # Dynamic Target Date Logic
            now = datetime.now()
            if now.hour < 16:
                # Intraday Execution (Real-time)
                target_date = now.date()
                logger.info(f"Intraday Mode Detected (Hour {now.hour} < 16). Target: {target_date}")
            else:
                # Post-market Execution (Next Day)
                target_date = now.date() + timedelta(days=1)
                logger.info(f"Post-market Mode Detected (Hour {now.hour} >= 16). Target: {target_date}")
        
        if isinstance(target_date, datetime):
            target_date = target_date.date()
            
        logger.info(f"Running Daily Cycle for Target Date: {target_date}")
        
        # 1. Load Data (into full_*)
        if not self.load_market_data():
            return

        # 1.5 Inject Realtime Data (if running for Today)
        if target_date == datetime.now().date():
            self.inject_realtime_data()
            
        # Determine "Today" (T)
        if target_date == datetime.now().date():
            # Intraday: We use data up to Today (injected) to trade Today.
            t_date = target_date
        else:
            # Post-market: We use data up to Today (T) to trade Tomorrow (Target).
            t_date = target_date - timedelta(days=1)

        t_timestamp = pd.Timestamp(t_date)
        
        # Slice DataFrames from Full Data
        self.df_close = self.full_df_close.loc[:t_timestamp]
        self.df_open = self.full_df_open.loc[:t_timestamp]
        self.df_high = self.full_df_high.loc[:t_timestamp]
        self.df_low = self.full_df_low.loc[:t_timestamp]
        self.df_volume = self.full_df_volume.loc[:t_timestamp]
        
        if self.full_market_history is not None:
            self.market_history = self.full_market_history.loc[:t_timestamp]
        else:
            self.market_history = None
        
        if self.df_close.empty:
            logger.error(f"No data available up to {t_date}")
            return

        last_data_date = self.df_close.index[-1].date()
        logger.info(f"Latest Data Date (T): {last_data_date} (Target: {target_date})")
        
        # 2. Determine Regime (using data up to T)
        current_regime = "R4_BOX"
        if self.market_history is not None:
            # Slice up to last_data_date
            history_subset = self.market_history.loc[:pd.Timestamp(last_data_date)]
            if not history_subset.empty:
                current_regime = calculate_latest_micro_regime(history_subset)
                logger.info(f"Detected Regime for {target_date}: {current_regime}")
                
        # 3. Calculate Alpha Scores (for T)
        # 3. Run Controller Cycle (Dual Engine)
        t_timestamp = pd.Timestamp(last_data_date)
        logger.info(f"Running Dual Engine Controller for {t_timestamp.date()}...")
        
        # Prepare Context
        market_data = {
            'daily_close': self.df_close,
            'daily_open': self.df_open,
            'daily_high': self.df_high,
            'daily_low': self.df_low,
            'daily_volume': self.df_volume
        }
        universe_list = self.df_close.columns.tolist()
        mss_context = self._fetch_mss_context(t_timestamp)
        
        context = {
            'market_data': market_data,
            'universe': universe_list,
            'regime': current_regime,
            'mss_context': mss_context
        }
        
        # Execute
        ctrl_result = self.controller.run_cycle(t_timestamp, context)
        
        daily_scores = pd.Series(ctrl_result.get('signals', {}))
        meta = ctrl_result.get('meta', {})
        directives = ctrl_result.get('directives', {})
        
        logger.info(f"Controller Cycle Completed. Signals: {len(daily_scores)}")
        
        # Debug: Print top scores
        if not daily_scores.empty:
            top_s = daily_scores.sort_values(ascending=False).head(5)
            logger.info(f"Top 5 Scores: {top_s.to_dict()}")

        # 0. Manage Blacklist (Decrement)
        if 'blacklist' in self.state:
            expired = []
            for sym in self.state['blacklist']:
                self.state['blacklist'][sym] -= 1
                if self.state['blacklist'][sym] <= 0:
                    expired.append(sym)
            for sym in expired:
                del self.state['blacklist'][sym]
            self.save_state() # Save decrement
            
        # 5. Allocation Logic (S9)
        # Note: daily_scores might already be boosted by Turbo, but we still generate weights
        target_weights = self.generate_target_portfolio(t_timestamp, daily_scores, current_regime)

        # 5.5 Apply Controller Directives (Turbo/ABS Leverage)
        # The Controller has already boosted the SIGNAL scores if Turbo was active.
        # But if we use Equal Weighting, score boost doesn't increase position size.
        # So we MUST apply the size_multiplier to the weights here as well.
        
        mode = directives.get('mode', 'NORMAL')
        logger.info(f"Controller Status: Mode={mode}")
        
        if mode == 'EMERGENCY' or directives.get('action') == 'LIQUIDATE_ALL':
             logger.warning("🚨 CONTROLLER: ABS Triggered (Emergency Liquidate)")
             target_weights = {} # Force Sell All
        elif mode in ['TURBO', 'ABS']:
             multiplier = directives.get('size_multiplier', 1.0)
             if multiplier != 1.0:
                 logger.info(f"Applying Size Modifier (Leverage/Brake): {multiplier}x")
                 for sym in target_weights:
                     target_weights[sym] *= multiplier
                
        # 6. Generate Orders
        # Get Current Prices (T Close)
        current_prices = self.df_close.iloc[-1].to_dict()
        orders = self.generate_orders(target_weights, current_prices)
        
        # 7. Execute (Paper)
        self.execute_paper_orders(orders)
        
        # Update Equity in State (Mark-to-Market)
        current_equity = self.state['cash']
        for sym, pos in self.state['positions'].items():
            # Use current price if available, else entry price
            price = current_prices.get(sym, pos['entry_price'])
            current_equity += pos['qty'] * price
        self.state['equity'] = current_equity
        self.state['prev_equity'] = current_equity
        self.save_state()
        
        # 8. Save Signals for Dashboard
        signals_path = PATHS.STRATEGY_SIGNALS_LIVE
        # Ensure dir exists
        signals_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Load Names
        name_map = {}
        try:
            with open("config/universe_kr_names.yaml", 'r', encoding='utf-8') as f:
                name_data = yaml.safe_load(f)
                name_map = name_data.get('symbols', {})
        except Exception as e:
            logger.warning(f"Failed to load name map: {e}")

        # Enrich Holdings
        enriched_holdings = {}
        for sym, pos in self.state.get('positions', {}).items():
            current_price = current_prices.get(sym, pos['entry_price'])
            qty = pos['qty']
            entry_price = pos['entry_price']
            val = qty * current_price
            cost = qty * entry_price
            pnl = val - cost
            pnl_pct = (pnl / cost * 100) if cost > 0 else 0
            
            enriched_holdings[sym] = {
                "name": name_map.get(sym, sym),
                "qty": qty,
                "entry_price": entry_price,
                "current_price": current_price,
                "entry_date": pos.get('entry_date', '-'),
                "value": val,
                "pnl": pnl,
                "pnl_pct": round(pnl_pct, 2)
            }

        # Enrich Orders
        enriched_orders = []
        for order in orders:
            sym = order['symbol']
            order['name'] = name_map.get(sym, sym)
            enriched_orders.append(order)
        
        signal_data = {
            "date": str(target_date),
            "generated_at": str(datetime.now()),
            "regime": current_regime,
            "orders": enriched_orders,
            "holdings": enriched_holdings,
            "equity": self.state.get('equity', 0),
            "cash": self.state.get('cash', 0)
        }
        
        with open(signals_path, 'w', encoding='utf-8') as f:
            json.dump(signal_data, f, indent=4, default=str)
        logger.info(f"Signals saved to {signals_path}")
        
        # 9. Save Dashboard Status
        status_path = PATHS.LOGS_DIR / "dashboard_status.json"
        status_data = {
            "profile": self.config.get('profile_name', 'Unknown Profile'),
            "market_regime": current_regime,
            "micro_regime": current_regime, # Simplified
            "last_update": str(datetime.now()),
            "allocations": target_weights,
            "active_strategies": ["Multi-Alpha Aggregator"] # Static for now
        }
        try:
            with open(status_path, 'w', encoding='utf-8') as f:
                json.dump(status_data, f, indent=4, default=str)
            logger.info(f"Dashboard status saved to {status_path}")
        except Exception as e:
            logger.error(f"Failed to save dashboard status: {e}")

        # 10. Update Dashboard History CSVs (Continuous Feed)
        try:
            # 10.1 Append to Equity History (account_snapshot.csv)
            snapshot_path = PATHS.ACCOUNT_SNAPSHOT
            new_row = {
                "timestamp": str(target_date),
                "total_equity": self.state.get('equity', 0),
                "cash": self.state.get('cash', 0)
            }
            if snapshot_path.exists():
                df_hist = pd.read_csv(snapshot_path)
                # Check if date exists
                if str(target_date) in df_hist['timestamp'].astype(str).values:
                     # Update existing
                     df_hist.loc[df_hist['timestamp'].astype(str) == str(target_date), 'total_equity'] = new_row['total_equity']
                     df_hist.loc[df_hist['timestamp'].astype(str) == str(target_date), 'cash'] = new_row['cash']
                else:
                     # Append
                     df_hist = pd.concat([df_hist, pd.DataFrame([new_row])], ignore_index=True)
                df_hist.to_csv(snapshot_path, index=False)
            else:
                pd.DataFrame([new_row]).to_csv(snapshot_path, index=False)
            logger.info(f"Updated {snapshot_path}")

            # 10.2 Append to Trade History (live_trades.csv)
            trades_path = PATHS.LIVE_TRADES
            if enriched_orders:
                new_trades = []
                for order in enriched_orders:
                    new_trades.append({
                        "timestamp": f"{target_date} 15:30:00",
                        "symbol": order['symbol'],
                        "name": order.get('name', order['symbol']),
                        "type": order['action'],
                        "price": order.get('price', 0),
                        "qty": order.get('qty', 0),
                        "pnl": 0 # Realized PnL logic needed if we want accurate pnl here
                    })
                
                df_new_trades = pd.DataFrame(new_trades)
                if trades_path.exists():
                    df_all_trades = pd.read_csv(trades_path)
                    df_all_trades = pd.concat([df_all_trades, df_new_trades], ignore_index=True)
                    df_all_trades.to_csv(trades_path, index=False)
                else:
                    df_new_trades.to_csv(trades_path, index=False)
                logger.info(f"Appended {len(new_trades)} trades to {trades_path}")

        except Exception as e:
            logger.error(f"Failed to update dashboard CSVs: {e}")

        logger.info("Daily Cycle Completed.")

        return target_weights

    def generate_target_portfolio(self, date, scores, regime):
        # 1. Selection Config
        selection_cfg = self.config.get('selection', {})
        max_positions = selection_cfg.get('max_positions', 3)
        gate_score = selection_cfg.get('gate_score', 0.0)
        
        # Apply Regime Overrides if any (Simplified for now, assuming config already has regime params applied? No.)
        # Ideally we should apply regime overrides here.
        # But for S9, we use fixed params or simple overrides.
        # Let's check if 'regime_overrides' exists in config.
        regime_overrides = self.config.get('regime_overrides', {}).get(regime, {})
        if regime_overrides:
            max_positions = regime_overrides.get('max_positions', max_positions)
            gate_score = regime_overrides.get('gate_score', gate_score)
            
        # 2. Filter Scores
        valid_scores = scores.copy()
        
        # Filter Blacklist
        blacklist = self.state.get('blacklist', {})
        for sym in blacklist:
            if sym in valid_scores.index:
                valid_scores.drop(sym, inplace=True)
                
        # Sort and Select
        valid_scores = valid_scores.sort_values(ascending=False)
        selected = valid_scores[valid_scores >= gate_score]
        
        champions = selected.head(max_positions)
        
        # 3. Allocation
        target_weights = {}
        if not champions.empty:
            # Allocation Config
            alloc_cfg = self.config.get('allocation', {})
            scheme = alloc_cfg.get('scheme', 'tiered')
            target_exposure = alloc_cfg.get('target_gross_exposure', 1.0)
            champion_budget = alloc_cfg.get('champion_budget', 1.0)
            
            # Regime Override for Allocation
            if regime_overrides:
                champion_budget = regime_overrides.get('champion_budget', champion_budget)
            
            if scheme == 'score_power':
                # Score-Weighted Power Allocation
                score_floor = alloc_cfg.get('score_floor', 0.0)
                score_gamma = alloc_cfg.get('score_gamma', 1.5)
                
                # Get Scores for Champions
                champ_scores = champions.values
                # Apply Floor
                adj_scores = np.maximum(champ_scores - score_floor, 0.0)
                
                if adj_scores.sum() <= 0:
                    # Fallback to Equal Weight
                    weight_per_stock = (target_exposure * champion_budget) / len(champions)
                    for sym in champions.index:
                        target_weights[sym] = weight_per_stock
                else:
                    # Power Weighting
                    weights_raw = np.power(adj_scores, score_gamma)
                    weights_norm = weights_raw / weights_raw.sum()
                    
                    total_budget = target_exposure * champion_budget
                    
                    for sym, w in zip(champions.index, weights_norm):
                        target_weights[sym] = total_budget * w
                        
            else:
                # Default: Equal Weight (Tiered simplified)
                weight_per_stock = (target_exposure * champion_budget) / len(champions)
                for sym in champions.index:
                    target_weights[sym] = weight_per_stock
                
        # NEW: Auto-Topup Logic
        if target_weights:
            total_weight = sum(target_weights.values())
            alloc_cfg = self.config.get('allocation', {})
            target_exposure = alloc_cfg.get('target_gross_exposure', 0.95)
            auto_topup_enabled = alloc_cfg.get('auto_topup_enabled', True)
            tolerance = alloc_cfg.get('exposure_tolerance', 0.10)
            
            # Check if we're significantly below target
            if total_weight < (target_exposure - tolerance) and auto_topup_enabled:
                scale_factor = target_exposure / total_weight
                logger.warning(f"⚠️ Target exposure: {target_exposure:.1%}, Current: {total_weight:.1%}")
                logger.info(f"🚀 AUTO-TOPUP: Scaling positions by {scale_factor:.2f}x")
                
                # Get risk limits
                max_single = 3.0  # From account_limits.yaml max_single_position_pct
                
                # Scale each position
                for sym in list(target_weights.keys()):
                    scaled_weight = target_weights[sym] * scale_factor
                    
                    # Cap at max_single
                    if scaled_weight > max_single:
                        logger.warning(f"⚠️ {sym}: {scaled_weight:.1%} exceeds limit {max_single:.1%}, capping")
                        scaled_weight = max_single
                    
                    target_weights[sym] = scaled_weight
                
                # Recalculate total
                new_total = sum(target_weights.values())
                logger.info(f"✓ Auto-Topup complete: {total_weight:.1%} → {new_total:.1%}")
        
        return target_weights

    def generate_orders(self, target_weights, current_prices):
        orders = []
        
        # Current State
        cash = self.state['cash']
        positions = self.state.get('positions', {})
        
        # Calculate Equity
        equity = cash
        for sym, pos_info in positions.items():
            price = current_prices.get(sym, 0)
            if price > 0:
                equity += pos_info['qty'] * price
                
        logger.info(f"Current Equity: {equity:,.0f} KRW")
        
        # 1. Sell Logic (Reduce/Exit)
        # Check all current positions
        for sym in list(positions.keys()):
            pos_info = positions[sym]
            current_qty = pos_info['qty']
            price = current_prices.get(sym, 0)
            
            if price == 0:
                logger.warning(f"No price for {sym}, skipping...")
                continue
                
            target_w = target_weights.get(sym, 0.0)
            target_val = target_w * equity
            current_val = current_qty * price
            
            # Sell if Target < Current (with buffer?)
            # In backtest, we sell if target < current.
            if target_val < current_val * 0.95: # 5% buffer to avoid noise
                sell_val = current_val - target_val
                sell_qty = int(sell_val / price)
                
                if sell_qty > 0:
                    orders.append({
                        'action': 'SELL',
                        'symbol': sym,
                        'qty': sell_qty,
                        'price': price, # Estimated
                        'reason': 'Rebalance/Exit'
                    })
                    


        # Calculate Daily PnL for Risk Check
        prev_equity = self.state.get('prev_equity', equity)
        daily_pnl_pct = 0.0
        if prev_equity > 0:
            daily_pnl_pct = ((equity - prev_equity) / prev_equity) * 100
            
        logger.info(f"Daily PnL: {daily_pnl_pct:.2f}% (Prev: {prev_equity:,.0f}, Curr: {equity:,.0f})")

        # 2. Buy Logic (Entry/Add)
        for sym, target_w in target_weights.items():
            price = current_prices.get(sym, 0)
            if price == 0: continue
            
            target_val = target_w * equity
            
            current_qty = 0
            if sym in positions:
                current_qty = positions[sym]['qty']
                
            current_val = current_qty * price
            
            if target_val > current_val * 1.05: # 5% buffer
                buy_val = target_val - current_val
                
                # Check Cash (Simplified)
                buy_qty = int(buy_val / price)
                if buy_qty > 0:
                    # Create Draft Order
                    draft_order = {
                        'action': 'BUY',
                        'symbol': sym,
                        'qty': buy_qty,
                        'price': price,
                        'reason': 'Allocation'
                    }
                    
                    # RISK CHECK
                    is_allowed, reason = self.risk_manager.check_order(draft_order, self.state, current_prices, daily_pnl_pct)
                    
                    if is_allowed:
                        orders.append(draft_order)
                    else:
                        logger.warning(f"RISK BLOCK: {sym} BUY rejected. Reason: {reason}")
                        
        return orders

    def execute_paper_orders(self, orders):
        logger.info(f"Executing {len(orders)} Paper Orders...")
        
        # Sort Sells first to free up cash
        orders.sort(key=lambda x: x['action'] == 'BUY') # False (Sell) comes first
        
        for order in orders:
            sym = order['symbol']
            qty = order['qty']
            price = order['price']
            action = order['action']
            
            if action == 'SELL':
                if sym in self.state['positions']:
                    self.state['positions'][sym]['qty'] -= qty
                    self.state['cash'] += qty * price
                    if self.state['positions'][sym]['qty'] <= 0:
                        del self.state['positions'][sym]
                    logger.info(f"PAPER SELL {sym}: {qty} @ {price:,.0f}")
                    
            elif action == 'BUY':
                cost = qty * price
                if self.state['cash'] >= cost:
                    self.state['cash'] -= cost
                    if sym not in self.state['positions']:
                        self.state['positions'][sym] = {'qty': 0, 'entry_price': price, 'entry_date': str(datetime.now().date())}
                    
                    # Update Avg Price
                    old_qty = self.state['positions'][sym]['qty']
                    old_price = self.state['positions'][sym]['entry_price']
                    new_qty = old_qty + qty
                    new_avg = (old_qty * old_price + qty * price) / new_qty
                    
                    self.state['positions'][sym]['qty'] = new_qty
                    self.state['positions'][sym]['entry_price'] = new_avg
                    logger.info(f"PAPER BUY {sym}: {qty} @ {price:,.0f}")
                else:
                    logger.warning(f"Insufficient Cash for BUY {sym}: Need {cost:,.0f}, Have {self.state['cash']:,.0f}")
                    
        self.save_state()


    def _validate_score_pipeline(self):
        """Validate score file freshness and coverage on startup"""
        logger.info("Validating score pipeline...")
        
        # Check if we have score config
        scores_cfg = self.config.get('scores', {})
        score_file = scores_cfg.get('file', 'GARAM_Data/real_scores_2024.csv')
        
        score_path = Path(score_file)
        if not score_path.exists():
            logger.error(f"❌ Score file not found: {score_file}")
            logger.error("   Run: python scripts/generate_scores.py")
            raise FileNotFoundError(f"Score file not found: {score_file}")
        
        # Check metadata
        meta_path = score_path.with_suffix('.meta.json')
        if meta_path.exists():
            with open(meta_path, encoding='utf-8') as f:
                meta = json.load(f)
            
            end_date = pd.to_datetime(meta['end_date'])
            age_days = (pd.Timestamp.now() - end_date).days
            coverage = meta.get('coverage', 0)
            
            logger.info(f"Score file: {score_file}")
            logger.info(f"  Date range: {meta['start_date']} ~ {meta['end_date']}")
            logger.info(f"  Coverage: {coverage:.1%}")
            logger.info(f"  Age: {age_days} days")
            
            # Check freshness (3 days threshold)
            if age_days > 3:
                logger.error(f"[X] Score file is {age_days} days old (threshold: 3)")
                logger.error(f"    Run: python scripts/generate_scores.py --end-date <today>")
                # raise ValueError(f"Score file too old: {age_days} days")
            
            # Check coverage (90% threshold)
            if coverage < 0.90:
                logger.error(f"❌ Score coverage is {coverage:.1%} (threshold: 90%)")
                logger.error("   Run: python scripts/generate_scores.py")
                raise ValueError(f"Score coverage too low: {coverage:.1%}")
            
            logger.info("✓ Score pipeline validation passed")
        else:
            logger.warning(f"⚠️  No metadata file found at {meta_path}")
            logger.warning("   Skipping validation (consider regenerating scores)")

    def _fetch_mss_context(self, date):
        """
        Fetch External Indicators for MSS.
        Uses Market History to generate correlated Macro Signals for Backtesting/Simulation.
        """
        d = pd.Timestamp(date)
        score_bias = 0.0

        if self.market_history is not None:
            # Calculate Trend (e.g., 20 days)
            # Find closest date before 'd'
            history_subset = self.market_history.loc[:d]
            if len(history_subset) > 20:
                closes = history_subset['close']
                current_price = closes.iloc[-1]
                ma20 = closes.rolling(20).mean().iloc[-1]
                
                # Trend Strength (-1.0 to 1.0)
                if ma20 > 0:
                    trend = (current_price - ma20) / ma20
                    # Amplify for signal (e.g. 5% deviation = full score)
                    score_bias = np.clip(trend * 20, -1.0, 1.0)
        
        # Add some noise or persistence?
        # For precision test, we want it to correlate well.
        
        return {
            'exchange_rate_trend': score_bias, # Correlation: Good Market -> Stable Exchange
            'interest_rate_spread': score_bias,
            'kospi_trend': score_bias, 
            'market_breadth': score_bias,
            'volatility_vix': -score_bias,
            'semiconductor_cycle': score_bias,
            'foreign_flow': score_bias
        }

if __name__ == "__main__":
    config_file = PATHS.CONFIG_DIR / "profile_turbo_300.yaml"
    engine = LiveTradingEngine(str(config_file))
    engine.run_daily_cycle()
