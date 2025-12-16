"""
Real Broker Simulator for GARAM
Paper trading broker that simulates real trading without actual API calls
"""

import logging
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Optional
from uuid import uuid4

# Import centralized paths
try:
    from garam.config import PATHS
    DEFAULT_DATA_DIR = PATHS.MARKET_DATA_DIR
except ImportError:
    DEFAULT_DATA_DIR = Path("C:/garam/GARAM_Data/market_data")

from .abstract_broker import AbstractBroker

# 로깅 설정
logger = logging.getLogger("RealBrokerSim")

class RealBrokerSim(AbstractBroker):
    """
    실계좌 연동 시뮬레이션 브로커
    - 데이터: Kiwoom Data Server (HTTP API, persistent session)
    - 주문: 100% 가상 체결 (Paper Trading)
    - 안전장치: 실제 주문 API 호출 원천 차단
    """
    
    is_live = False  # NEVER CHANGE THIS TO TRUE

    def __init__(self, initial_balance: float = 100_000_000, trade_log_path: Optional[Path] = None):
        self.balance = initial_balance
        self.positions: Dict[str, Dict] = {}
        self.orders: Dict[str, Dict] = {}
        self.order_counter = 0
        self.trade_log = []
        self.trade_log_path = trade_log_path
        self.exposure_history = [] # Track portfolio exposure %
        
        # Data directory
        self.data_dir = DEFAULT_DATA_DIR
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Load existing trades if persistent
        if self.trade_log_path and self.trade_log_path.exists():
            try:
                import json
                with open(self.trade_log_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        self.trade_log = data
                    elif isinstance(data, dict):
                        self.trade_log = data.get('trades', [])
                        # Could also load daily_summary if needed, but we recalculate for now
                logger.info(f"Loaded {len(self.trade_log)} trades from {self.trade_log_path}")
            except Exception as e:
                logger.error(f"Failed to load trade log: {e}")

        logger.info("🛡️ RealBrokerSim initialized. LIVE TRADING DISABLED.")
        
    def connect(self) -> bool:
        """Simulate connection to broker."""
        logger.info("✅ Connected to RealBrokerSim (Virtual)")
        return True
        
    @property
    def base_capital(self) -> float:
        """
        Total Capital (Equity).
        SAFEGUARD: If 0 or less in SIMULATION mode, return 100M Mock Capital.
        """
        equity = self.get_total_equity()
        if equity <= 0 and not self.is_live:
            logger.warning("⚠️ Virtual Equity is 0. Using Mock Capital (100M) for Simulation.")
            return 100_000_000
        return equity

    def get_balance(self) -> float:
        return self.balance
        
    def get_position(self, symbol: str) -> Optional[Dict]:
        return self.positions.get(symbol)

    def get_total_equity(self) -> float:
        """Calculate total equity (Balance + Unrealized PnL)"""
        equity = self.balance
        for symbol, pos in self.positions.items():
            # Use current_price if available, else avg_price
            price = pos.get('current_price', pos['avg_price'])
            equity += pos['qty'] * price
        return equity

    def calculate_exposure(self) -> float:
        """Calculate current gross exposure %"""
        equity = self.get_total_equity()
        if equity <= 0: return 0.0
        
        gross_position_value = 0.0
        for symbol, pos in self.positions.items():
            price = pos.get('current_price', pos['avg_price'])
            gross_position_value += abs(pos['qty'] * price)
            
        return gross_position_value / equity
        
    # ... (get_price_history omitted for brevity) ...

    def send_order(self, symbol: str, action: str, qty: int, price: float, **kwargs) -> str:
        """
        [SAFETY CRITICAL]
        Logs the order but DOES NOT execute it against the real API.
        Returns a fake order ID.
        """
        if self.is_live:
            raise RuntimeError("CRITICAL: RealBrokerSim cannot be in LIVE mode!")
            
        self.order_counter += 1
        order_id = f"SIM-{uuid4()}"
        
        logger.info(f"[SIM_ONLY] 🛑 BLOCKED REAL ORDER: {action} {symbol} {qty} @ {price}")
        
        # 가상 체결 처리 (Paper Trading Logic)
        self._execute_paper_trade(order_id, symbol, action, qty, price, **kwargs)
        
        return order_id
        
    def cancel_order(self, order_id: str) -> bool:
        """
        [SAFETY CRITICAL]
        Logs the cancel request but DOES NOT execute it.
        """
        logger.info(f"[SIM_ONLY] 🛑 BLOCKED CANCEL ORDER: {order_id}")
        return True
        
    def _execute_paper_trade(self, order_id: str, symbol: str, action: str, qty: int, price: float, **kwargs):
        """내부 가상 체결 로직"""
        timestamp = datetime.now().isoformat()
        
        # Update Position & Balance
        if action == 'BUY':
            cost = qty * price
            if cost > self.balance:
                logger.warning(f"Insufficient balance for BUY {symbol}: {cost} > {self.balance}")
                return 
                
            self.balance -= cost
            if symbol in self.positions:
                pos = self.positions[symbol]
                total_qty = pos['qty'] + qty
                pos['avg_price'] = ((pos['qty'] * pos['avg_price']) + (qty * price)) / total_qty
                pos['qty'] = total_qty
                pos['current_price'] = price # Update current price
            else:
                self.positions[symbol] = {'qty': qty, 'avg_price': price, 'current_price': price}
                
        elif action == 'SELL':
            if symbol not in self.positions or self.positions[symbol]['qty'] < qty:
                logger.warning(f"Insufficient position for SELL {symbol}")
                return 
                
            proceeds = qty * price
            self.balance += proceeds
            self.positions[symbol]['qty'] -= qty
            self.positions[symbol]['current_price'] = price # Update current price
            
            if self.positions[symbol]['qty'] == 0:
                del self.positions[symbol]
        
        # Calculate Exposure Metrics
        total_equity = self.get_total_equity()
        portfolio_exposure = self.calculate_exposure()
        self.exposure_history.append(portfolio_exposure)
        
        position_value = qty * price
        exposure_pct = (position_value / total_equity) if total_equity > 0 else 0
        
        # Create Log Entry
        log_entry = {
            'timestamp': timestamp,
            'order_id': order_id,
            'symbol': symbol,
            'action': action,
            'qty': qty,
            'price': price,
            # New Fields
            'position_value': position_value,
            'exposure_pct': exposure_pct,
            'portfolio_exposure_pct': portfolio_exposure,
            'portfolio_value': total_equity
        }
        
        # Merge extra data (e.g. strategy_id, reason)
        log_entry.update(kwargs)
        
        self.trade_log.append(log_entry)
        
        if self.trade_log_path:
            self._save_trade_log()

    def _save_trade_log(self):
        """Save trade log to file with daily summary"""
        import json
        try:
            # Calculate Daily Summary
            summary = {}
            if self.exposure_history:
                summary = {
                    'avg_gross_exposure_pct': np.mean(self.exposure_history) * 100,
                    'max_gross_exposure_pct': np.max(self.exposure_history) * 100,
                    'min_gross_exposure_pct': np.min(self.exposure_history) * 100,
                    'trade_count': len(self.trade_log),
                    'current_equity': self.get_total_equity()
                }
            
            data = {
                'date': datetime.now().strftime('%Y%m%d'),
                'trades': self.trade_log,
                'daily_summary': summary
            }
            
            with open(self.trade_log_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save trade log: {e}")
        
    def get_price_history(self, symbol: str, days: int = 365, timeframe: str = '1min') -> pd.DataFrame:
        """
        과거 데이터 조회
        1. 로컬 CSV 캐시 확인 (data/{symbol}_{timeframe}.csv)
        2. Kiwoom Data Server 호출 (HTTP API, persistent session)
        3. 실패 시 Mock 데이터 생성
        """
        cache_file = self.data_dir / f"{symbol}_{timeframe}.csv"
        
        # 1. 캐시 확인
        if cache_file.exists():
            logger.info(f"📂 Loading cached data from {cache_file}")
            try:
                df = pd.read_csv(cache_file)
                df['date'] = pd.to_datetime(df['date'])
                df.set_index('date', inplace=True)
                return df
            except Exception as e:
                logger.warning(f"Failed to load cache: {e}")
        
        # 2. Kiwoom Data Server 호출 (HTTP API)
        # 2. Kiwoom Data Server 호출 (HTTP API) -> REPLACED with Direct CSV Read from Collector
        if timeframe == '1min':
            try:
                # Try to read from Collector's CSV (generated by kiwoom_login_ui.py)
                from config import PATHS
                today_str = datetime.now().strftime("%Y%m%d")
                collector_csv = PATHS.DATA_DIR / "kr" / "realtime" / "1m" / f"{symbol}_{today_str}.csv"
                
                if collector_csv.exists():
                    logger.info(f"📂 Loading real-time data from Collector: {collector_csv}")
                    df = pd.read_csv(collector_csv)
                    
                    # Ensure columns match
                    # Collector CSV: datetime,open,high,low,close,volume
                    if 'datetime' in df.columns:
                        df['date'] = pd.to_datetime(df['datetime'])
                        df.set_index('date', inplace=True)
                        df.drop(columns=['datetime'], inplace=True, errors='ignore')
                    
                    logger.info(f"✅ Data loaded from Collector! ({len(df)} rows)")
                    return df
                else:
                    logger.warning(f"⏳ No real-time data yet for {symbol} (Waiting for Collector...)")
                    # If no file yet, we might fall back to mock or return empty
                    
            except Exception as e:
                logger.error(f"Exception reading collector CSV: {e}")
            
        # 3. Fallback: Mock Data Generation
        logger.warning(f"⚠️ Using MOCK data for {symbol} (Real data fetch failed or not supported)")
        return self._generate_mock_data(days, symbol)
        


    def get_latest_bar(self, symbol: str) -> Optional[pd.Series]:
        """
        Get the latest available bar for the symbol.
        In simulation, this might return the next bar in the sequence or current real-time bar.
        For Paper Trading with Mock Data, we simulate time progression.
        """
        # For now, we just generate a random bar based on last price to simulate live feed
        # Or fetch from Kiwoom if available
        
        # 1. Try Kiwoom (if live) - Not implemented for single bar yet
        
        # 2. Mock Generation
        if symbol not in self.positions:
            last_price = 70000 # Default
        else:
            last_price = self.positions[symbol]['current_price']
            
        # Random walk
        change = np.random.normal(0, 0.001)
        current_price = last_price * (1 + change)
        
        now = datetime.now()
        
        return pd.Series({
            'open': current_price,
            'high': current_price * 1.001,
            'low': current_price * 0.999,
            'close': current_price,
            'volume': 1000
        }, name=now)

    def _generate_mock_data(self, days: int, symbol: str) -> pd.DataFrame:
        """현실적인 Mock 데이터 생성"""
        start_date = datetime.now() - timedelta(days=days)
        dates = []
        opens = []
        highs = []
        lows = []
        closes = []
        volumes = []
        
        price = 70000
        
        # 장세 시나리오
        regimes = [
            (int(days*0.3), 0.0001, 0.0005),
            (int(days*0.2), -0.0002, 0.0010),
            (int(days*0.2), 0.0000, 0.0003),
            (int(days*0.3), 0.00015, 0.0006)
        ]
        
        current_day = 0
        for duration, trend, volatility in regimes:
            for _ in range(duration):
                current_date = start_date + timedelta(days=current_day)
                current_day += 1
                
                if current_date.weekday() >= 5: continue
                
                current_time = current_date.replace(hour=9, minute=0)
                end_time = current_date.replace(hour=15, minute=30)
                
                price *= (1 + np.random.normal(trend * 100, volatility * 2)) # Gap
                
                while current_time <= end_time:
                    change = np.random.normal(trend / 380, volatility)
                    price *= (1 + change)
                    
                    bar_range = price * volatility * np.random.uniform(0.5, 2.0)
                    high = price + (bar_range / 2)
                    low = price - (bar_range / 2)
                    
                    dates.append(current_time)
                    opens.append(price)
                    highs.append(high)
                    lows.append(low)
                    closes.append(price)
                    volumes.append(int(np.random.exponential(1000)))
                    
                    current_time += timedelta(minutes=1)
                    
        return pd.DataFrame({
            'open': opens, 'high': highs, 'low': lows, 'close': closes, 'volume': volumes
        }, index=dates)
