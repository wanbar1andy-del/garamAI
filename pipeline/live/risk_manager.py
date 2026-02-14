class RiskManager:
    def __init__(self, config):
        self.cfg = config['risk']
        self.daily_start_equity = config['execution']['capital'] # Init
        self.halt_triggered = False
        
        # Spec A2: daily_kill_switch (-0.02)
        # Compatibility Layer for Config
        risk_cfg = config.get("risk", {})
        self.daily_kill_threshold = float(risk_cfg.get('daily_kill_switch', risk_cfg.get('max_daily_loss', -0.02)))
        self.time_stop_minutes = int(risk_cfg.get('time_stop_minutes', 30))
        self.time_stop_threshold = float(risk_cfg.get('time_stop_threshold', 0.002))

        # Per Trade State
        self.entry_price = {} # sym -> price
        self.entry_time = {}  # sym -> dt
        self.last_fill_ts = {} # sym -> ts
        self.post_entry_cooldown_min = int(risk_cfg.get('post_entry_cooldown_min', 5))
        self.peak_price = {}  # sym -> price
        
    def on_fill(self, fill_event):
        """
        fill_event: {symbol, side, fill_px, fill_ts...}
        """
        required = {"symbol", "side", "qty", "fill_px", "fill_ts"}
        missing = required - set(fill_event.keys())
        if missing:
             raise KeyError(f"Fill schema missing: {missing} | fill={fill_event}")

        sym = fill_event['symbol']
        side = fill_event['side']
        qty = fill_event['qty']
        fill_px = fill_event['fill_px']
        current_dt = fill_event['fill_ts']
        
        if side == 'BUY':
            self.entry_price[sym] = fill_px
            self.entry_time[sym] = current_dt
            self.peak_price[sym] = fill_px
            self.last_fill_ts[sym] = current_dt # Record entry time for cooldown
        elif side == 'SELL':
            # Clear state
            if sym in self.entry_price: del self.entry_price[sym]
            if sym in self.entry_time: del self.entry_time[sym]
            if sym in self.peak_price: del self.peak_price[sym]
            
    def update_global(self, current_equity):
        if self.daily_start_equity > 0:
            self.daily_pnl_pct = (current_equity / self.daily_start_equity) - 1.0
            
        # Debug Print
        # print(f"[Risk] Global Check: Eq={current_equity:.0f}, Start={self.daily_start_equity:.0f}, PnL={self.daily_pnl_pct*100:.2f}%, Thr={self.daily_kill_threshold*100:.2f}%, Halted={self.halt_triggered}")

        if (not self.halt_triggered) and (self.daily_pnl_pct <= self.daily_kill_threshold):
            print(f"[Risk] HALT TRIGGERED! PnL {self.daily_pnl_pct*100:.2f}% <= {self.daily_kill_threshold*100:.2f}%")
            self.halt_triggered = True
            return "DAILY_KILL_HALT"
            
        if self.halt_triggered:
            return "DAILY_KILL_HALT_ACTIVE"
            
        return None
        
    def check_risk(self, current_ts, symbol, current_px, current_equity):
        """
        Check individual position risk (Stop Loss, Time Stop)
        Returns: "STOP_LOSS", "TIME_STOP", or None
        """
        if self.halt_triggered:
            return "DAILY_KILL_HALT_ACTIVE"
            
        # 0. Cooldown Check (Post-Entry)
        last_ts = self.last_fill_ts.get(symbol)
        if last_ts:
             delta = (current_ts - last_ts).total_seconds() / 60.0
             if delta < self.post_entry_cooldown_min:
                 # Inside cooldown, skip risk checks
                 return None

        # 1. Stop Loss (Fixed %)
        # NOT IMPLEMENTED FOR ALPHA A2 (Time-based exit primarily)
        pass 

        # 2. Time Stop (N minutes)
        if symbol in self.entry_time:
            entry_ts = self.entry_time[symbol]
            duration_min = (current_ts - entry_ts).total_seconds() / 60.0
            
            if duration_min >= self.time_stop_minutes:
                # Check Profit Threshold condition if needed, or hard time stop
                return "TIME_STOP"
                
        return None
        
    def reset_daily(self, equity):
        self.daily_start_equity = float(equity)
        self.halt_triggered = False
        self.daily_pnl_pct = 0.0
