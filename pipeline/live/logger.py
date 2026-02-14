import os
import json
import csv
from datetime import datetime

class LiveLogger:
    def __init__(self, log_dir, reset=False):
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        
        self.paths = {
            'events': os.path.join(log_dir, 'events.jsonl'),
            'orders': os.path.join(log_dir, 'orders.csv'),
            'fills': os.path.join(log_dir, 'fills.csv'),
            'signals': os.path.join(log_dir, 'signals.csv')
        }
        
        # Reset if requested
        if reset:
             for p in self.paths.values():
                 if os.path.exists(p):
                     os.remove(p)
        
        # Init CSVs
        if not os.path.exists(self.paths['orders']):
            with open(self.paths['orders'], 'w', newline='', encoding='utf-8') as f:
                f.write("ts,id,symbol,side,qty,type,status,reject_reason,event\n")
                
        if not os.path.exists(self.paths['fills']):
            with open(self.paths['fills'], 'w', newline='', encoding='utf-8') as f:
                f.write("ts,id,symbol,side,fill_px,qty\n")

        if not os.path.exists(self.paths['signals']):
            with open(self.paths['signals'], 'w', newline='', encoding='utf-8') as f:
                f.write("ts,symbol,score,w_z,brk_val,vol_ratio,passed_count\n")
                
    def _to_ts_str(self, x):
        if isinstance(x, datetime):
            return x.strftime("%Y-%m-%d %H:%M:%S")
        return str(x)

    def log_event(self, event_type, data, ts=None):
        ts_str = self._to_ts_str(ts) if ts else self._to_ts_str(datetime.now())
            
        entry = {
            'ts': ts_str,
            'type': event_type,
            'data': data
        }
        with open(self.paths['events'], 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry) + "\n")
            
    def log_order(self, order, event="UPDATE"):
        with open(self.paths['orders'], 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                self._to_ts_str(order['ts']), order['id'], order['symbol'], 
                order['side'], order['qty'], order['type'], order['status'], 
                order.get('reject_reason',''), event
            ])
            
    def log_fill(self, fill):
        with open(self.paths['fills'], 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                self._to_ts_str(fill['fill_ts']), fill['id'], fill['symbol'], 
                fill['side'], fill['fill_px'], fill['qty']
            ])

    def log_signal(self, ts, debug):
        if not debug:
            debug = {'symbol':'', 'score':0, 'w_z':0, 'brk_val':0, 'vol_ratio':0, 'passed':0}
            
        with open(self.paths['signals'], 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                self._to_ts_str(ts), debug.get('symbol',''), debug.get('score',0),
                debug.get('w_z',0), debug.get('brk_val',0), debug.get('vol_ratio',0),
                debug.get('passed',0)
            ])
            f.flush()
