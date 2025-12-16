import yaml
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class PreTradeRiskManager:
    def __init__(self, config_path="risk/account_limits.yaml"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.mode = self.config.get('mode', 'MONITOR_ONLY')
        self.limits = self.config.get('limits', {})
        
    def _load_config(self):
        try:
            # Try absolute path first if relative fails
            if not self.config_path.exists():
                # Fallback to project root relative
                root = Path(__file__).parent.parent
                p = root / self.config_path
                if p.exists():
                    with open(p, 'r', encoding='utf-8') as f:
                        return yaml.safe_load(f)
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load risk config: {e}")
            return {'mode': 'MONITOR_ONLY', 'limits': {}}

    def check_order(self, order, state, current_prices, daily_pnl_pct=0.0):
        """
        Check if an order violates risk limits.
        Returns: (is_allowed, reason)
        """
        # If SELL, usually allow (unless we have specific restrictions)
        if order['action'] == 'SELL':
            return True, "SELL allowed"

        # 3. Daily Loss Check
        # If we hit the daily loss limit, STOP NEW BUYS.
        daily_loss_limit = self.limits.get('daily_loss_limit_pct', -100.0)
        if daily_pnl_pct < daily_loss_limit:
            msg = f"Daily Loss Limit Hit: {daily_pnl_pct:.2f}% < {daily_loss_limit}%"
            if self.mode == 'ACTIVE':
                return False, msg
            else:
                logger.warning(f"[RISK MONITOR] {msg}")

        # For BUY orders, check limits
        symbol = order['symbol']
        qty = order['qty']
        price = order['price']
        order_val = qty * price
        
        equity = state.get('equity', 0)
        if equity <= 0:
            return False, "Equity is zero or negative"

        # 1. Max Single Position Check
        max_pos_pct = self.limits.get('max_single_position_pct', 100.0)
        
        # Current position value
        current_pos = state.get('positions', {}).get(symbol, {})
        current_qty = current_pos.get('qty', 0)
        current_val = current_qty * price
        
        new_val = current_val + order_val
        new_weight_pct = (new_val / equity) * 100
        
        if new_weight_pct > max_pos_pct:
            msg = f"Max Position Violation: {symbol} would be {new_weight_pct:.1f}% (Limit: {max_pos_pct}%)"
            if self.mode == 'ACTIVE':
                return False, msg
            else:
                logger.warning(f"[RISK MONITOR] {msg}")

        # 2. Max Gross Exposure Check
        max_gross_pct = self.limits.get('max_gross_exposure_pct', 100.0)
        
        total_exposure = 0
        for s, p in state.get('positions', {}).items():
            p_price = current_prices.get(s, p['entry_price'])
            total_exposure += p['qty'] * p_price
            
        new_exposure = total_exposure + order_val
        new_gross_pct = (new_exposure / equity) * 100
        
        if new_gross_pct > max_gross_pct:
            msg = f"Max Exposure Violation: Would be {new_gross_pct:.1f}% (Limit: {max_gross_pct}%)"
            if self.mode == 'ACTIVE':
                return False, msg
            else:
                logger.warning(f"[RISK MONITOR] {msg}")
                
        # 3. Daily Loss Check (Requires Daily PnL tracking, simplified here)
        # Assuming 'equity' is updated daily. 
        # We need 'start_of_day_equity' to calculate daily loss.
        # This might need state update to track SOD equity.
        # Skipping for now or using simple check if available.
        
        return True, "OK"
