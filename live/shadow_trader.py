import logging
import pandas as pd
from typing import Dict, Any, Optional
from garam.data.feed.kiwoom_feed import KiwoomFeed
from garam.features.stream_processor import StreamProcessor
from garam.features.factory import FeatureFactory
from garam.broker.real_broker_sim import RealBrokerSim
from garam.agents.gpt_css_agent import GPTCSSAgent
from garam.live.surfing_brain_adapter import SurfingBrainAdapter
from garam.monitoring.signal_logger import SignalLogger
from garam.live.regime_router import RegimeRouter
from garam.risk.dge import DailyGrowthEngine, RiskConfig

logger = logging.getLogger(__name__)

class ShadowTrader:
    """
    Shadow Trading Engine.
    Connects Real-Time Data -> Features -> Strategy -> Paper Broker.
    """
    
    def __init__(self, mode: str = "SHADOW", risk_config: Dict = None, symbol: str = "005930", initial_capital: float = 100_000_000, feed_mode: str = 'mock'):
        self.mode = mode
        self.risk_config = risk_config or {}
        self.symbol = symbol
        self.feed_mode = feed_mode
        
        # Components
        if self.feed_mode != 'manual':
            self.feed = KiwoomFeed(mode=self.feed_mode) 
        else:
            self.feed = None
            
        self.factory = FeatureFactory()
        self.processor = StreamProcessor(self.factory)
        self.brain = SurfingBrainAdapter()
        self.signal_logger = SignalLogger()
        self.regime_router = RegimeRouter()
        
        # Setup Persistent Broker
        from garam.config import PATHS
        from datetime import datetime
        
        # Log path depends on mode
        log_subdir = "live_paper" if self.mode == "LIVE_PAPER" else "shadow"
        log_dir = PATHS.LOGS_DIR / log_subdir
        log_dir.mkdir(parents=True, exist_ok=True)
        
        trade_log_path = log_dir / f"trades_{datetime.now().strftime('%Y%m%d')}.json"
        
        # Use risk config for initial capital if available
        capital = self.risk_config.get('initial_equity', initial_capital)
        self.broker = RealBrokerSim(initial_balance=capital, trade_log_path=trade_log_path)
        
        self.css_agent = GPTCSSAgent()
        
        # State
        self.running = False
        self.current_strategy = None
        
        # Initialize DGE
        dge_config = RiskConfig(
            max_daily_loss_pct=self.risk_config.get('max_daily_loss_pct', 0.03),
            max_risk_per_trade_pct=self.risk_config.get('max_risk_per_trade_pct', 0.01),
            kelly_fraction=self.risk_config.get('kelly_fraction', 0.25),
            use_kelly=self.risk_config.get('use_kelly', True)
        )
        self.dge = DailyGrowthEngine(dge_config)
        
        # Status file for Dashboard (Unique per symbol)
        self.status_file = log_dir / f"status_{self.symbol}.json"
        self.last_status_update = 0
        self.activity_logs = [] # Buffer for dashboard logs
        
        # Setup
        self._setup_pipeline()
        self._log_activity(f"ShadowTrader initialized for {symbol} in {self.mode} mode", "system")
        logger.info(f"ShadowTrader initialized for {symbol} in {self.mode} mode")

    def _setup_pipeline(self):
        """Configure the data pipeline."""
        # 1. Register symbol with processor
        config = [
            {'name': 'ma_trend', 'params': {'fast': 20, 'slow': 60}},
            {'name': 'rsi', 'params': {'period': 14}},
            {'name': 'bollinger', 'params': {'window': 20, 'num_std': 2.0}}
        ]
        self.processor.register_symbol(self.symbol, config)
        
        # 2. Connect Feed -> Processor -> Strategy
        if self.feed:
            self.feed.subscribe(self.symbol)
            self.feed.add_callback(self.on_tick)

    def _log_activity(self, message: str, type: str = 'info'):
        """Add log to buffer and update status file immediately."""
        from datetime import datetime
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        log_entry = {
            'time': timestamp,
            'message': message,
            'type': type # system, trade, alert, info
        }
        
        self.activity_logs.append(log_entry)
        # Keep last 10 logs
        if len(self.activity_logs) > 10:
            self.activity_logs.pop(0)

    def start(self):
        """Start the shadow trading loop."""
        if self.running:
            return
        self.running = True
        
        if self.feed:
            self.feed.start()
        self._log_activity(f"ShadowTrader started in {self.mode} mode.", "system")
        logger.info(f"ShadowTrader started in {self.mode} mode.")

    def stop(self):
        """Stop the shadow trading loop."""
        self.running = False
        if self.feed:
            self.feed.stop()
        self._log_activity("ShadowTrader stopped.", "system")
        logger.info("ShadowTrader stopped.")

    def on_tick(self, tick: Dict):
        """Callback for new ticks."""
        # 1. Process Tick -> Features
        features = self.processor.on_tick(tick)
        
        if features:
            self.on_bar(features)
            
        # Update status file every 1 second
        import time
        if time.time() - self.last_status_update > 1.0:
            # logger.info(f"Writing status for {self.symbol}") # Debug
            self._write_status(tick)
            self.last_status_update = time.time()

    def _write_status(self, tick: Dict):
        """Write current status to file for Dashboard."""
        try:
            import json
            from datetime import datetime
            
            status = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'symbol': self.symbol,
                'price': tick.get('close'),
                'change': tick.get('change', 0),
                'mode': self.mode,
                'regime': 'UNCERTAIN', # Default, updated by strategy
                'signal': 'HOLD',
                'reason': 'Waiting for signal...',
                'positions': self.broker.get_position(self.symbol),
                'balance': self.broker.get_balance(),
                'recent_logs': self.activity_logs # Add logs
            }
            
            # If we have a recent decision, use it
            if hasattr(self, 'last_decision') and self.last_decision:
                status['regime'] = self.last_decision.get('regime', 'UNCERTAIN')
                status['signal'] = self.last_decision.get('signal', 'HOLD')
                status['reason'] = self.last_decision.get('reason', '')
                
            with open(self.status_file, 'w', encoding='utf-8') as f:
                json.dump(status, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to write status file: {e}")

    def on_bar(self, features: Dict):
        """Callback for new bars (features computed)."""
        logger.debug(f"New Bar: {features.get('timestamp')}")
        self._log_activity(f"Bar 완성: 지표 계산 완료 ({features.get('timestamp')})", "info")
        
        # 3. Get Active Strategy (Regime Based)
        strategy_config = self.regime_router.get_active_strategy()
        
        # Use SurfingBrainAdapter with config
        decision = self.brain.decide(features, config=strategy_config)
        
        # Store for status reporting
        decision['regime'] = strategy_config.get('regime', 'unknown')
        self.last_decision = decision
        
        raw_signal = decision['signal']
        strategy_id = decision['strategy_id']
        reason = decision['reason']
        regime = strategy_config.get('regime', 'unknown')
        
        self._log_activity(f"전략 분석: {raw_signal} ({reason})", "info")
        
        # Log Signal (Audit)
        from datetime import datetime
        import pandas as pd
        
        # Ensure timestamp is datetime object
        ts = features.get('timestamp')
        if isinstance(ts, str):
            try:
                ts = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
            except:
                ts = datetime.now()
        elif isinstance(ts, pd.Timestamp):
            ts = ts.to_pydatetime()
        elif not ts:
            ts = datetime.now()
            
        # Prepare serializable features
        serializable_features = {}
        for k, v in features.items():
            if isinstance(v, (pd.Timestamp, datetime)):
                serializable_features[k] = v.strftime('%Y-%m-%d %H:%M:%S')
            else:
                serializable_features[k] = v
            
        self.signal_logger.log_signal(
            timestamp=ts,
            symbol=self.symbol,
            signal=raw_signal,
            price=features['close'],
            strategy_id=strategy_id,
            regime=regime,
            features=serializable_features,
            reason=reason
        )
        
        # 4. Risk Guard
        if self._hit_daily_loss_limit():
            logger.warning("Daily loss limit hit. Stopping trading.")
            self._flat_all()
            return

        # 5. Execute Signal based on Mode
        if self.mode in ("SHADOW", "LIVE_PAPER"):
            self._paper_execute(
                raw_signal, 
                features['close'],
                strategy_id=strategy_id,
                reason=reason,
                regime=regime
            )

    def _hit_daily_loss_limit(self) -> bool:
        """Check if daily loss exceeds limit."""
        if not self.risk_config:
            return False
            
        max_loss_R = self.risk_config.get('max_daily_loss_R', 5)
        return False 

    def _paper_execute(self, signal: int, price: float, **kwargs):
        """Execute signal against RealBrokerSim."""
        position = self.broker.get_position(self.symbol)
        current_qty = position['qty'] if position else 0
        
        # Calculate Position Size via DGE
        capital = self.broker.get_balance()
        stop_loss_price = price * 0.95 if signal == 1 else price * 1.05
        
        stats = {'win_rate': 0.5, 'payoff_ratio': 2.0} 
        
        notional_size = self.dge.calculate_position_size(capital, price, stop_loss_price, stats)
        qty = int(notional_size / price)
        
        if qty <= 0:
            logger.warning(f"DGE calculated 0 quantity. Capital: {capital}, Price: {price}")
            return 
        
        if signal == 1 and current_qty == 0:
            # Buy
            self.broker.send_order(self.symbol, 'BUY', qty, price, **kwargs)
            logger.info(f"[{self.mode}] BUY: {qty} @ {price}")
            self._log_activity(f"매수 주문 실행: {qty}주 @ {price}", "trade")
            
        elif signal == -1 and current_qty > 0:
            # Sell
            self.broker.send_order(self.symbol, 'SELL', current_qty, price, **kwargs)
            logger.info(f"[{self.mode}] SELL: {current_qty} @ {price}")
            self._log_activity(f"매도 주문 실행: {current_qty}주 @ {price}", "trade")
            
    def _flat_all(self):
        """Close all positions."""
        position = self.broker.get_position(self.symbol)
        if position and position['qty'] > 0:
             self.broker.send_order(self.symbol, 'SELL', position['qty'], position['current_price'])
             logger.info("Flatted all positions.")

    def get_status(self) -> Dict:
        """Get current status for Dashboard."""
        return {
            'running': self.running,
            'mode': self.mode,
            'balance': self.broker.get_balance(),
            'position': self.broker.get_position(self.symbol),
            'trades': len(self.broker.trade_log)
        }
