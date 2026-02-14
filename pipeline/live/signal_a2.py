import pandas as pd
import numpy as np

class SignalA2:
    def __init__(self, config):
        self.cfg = config
        self.lookback = config['factors']['lookback_window']
        self.history = {} # sym -> DataFrame of 5m bars
        
    def on_bar_closed(self, closed_bars, vol_accel=1.0):
        """
        closed_bars: {sym: {dt, open, high, low, close, volume}}
        Returns: best_symbol (str or None)
        """
        # Update History
        for sym, bar in closed_bars.items():
            if sym not in self.history:
                self.history[sym] = pd.DataFrame(columns=['open','high','low','close','volume'])
            
            new_row = pd.DataFrame([bar]).set_index('dt')
            if self.history[sym].empty:
                self.history[sym] = new_row
            else:
                self.history[sym] = pd.concat([self.history[sym], new_row])
            
            # Trim history (Keep enough for lookback)
            # Lookback 100 + Buffer
            if len(self.history[sym]) > self.lookback + 50:
                self.history[sym] = self.history[sym].iloc[-(self.lookback+50):]

        # Calculate Scores
        scores = {}
        
        for sym, df in self.history.items():
            if len(df) < 20: continue # Not enough data
            
            try:
                # Factors
                c = df['close']
                h = df['high']
                v = df['volume']
                
                # A) Compression
                rolling = c.rolling(window=self.cfg['factors']['bb_window'])
                mid = rolling.mean()
                std = rolling.std()
                width = (mid + 2*std - (mid - 2*std)) / (mid + 1e-9)
                
                w_mean = width.rolling(window=self.lookback).mean()
                w_std = width.rolling(window=self.lookback).std()
                w_z = (width - w_mean) / (w_std + 1e-9)
                score_comp = -w_z.iloc[-1]
                
                # B) Breakout
                h_20 = h.shift(1).rolling(window=self.cfg['factors']['breakout_window']).max()
                brk_str = (c / (h_20 + 1e-9) - 1.0)
                
                b_mean = brk_str.rolling(window=self.lookback).mean()
                b_std = brk_str.rolling(window=self.lookback).std()
                score_brk = ((brk_str - b_mean) / (b_std + 1e-9)).iloc[-1]
                score_brk_val = brk_str.iloc[-1] # Actual value for gate
                
                # C) Volume
                v_ma = v.rolling(window=self.cfg['factors']['vol_ma_window']).mean()
                vol_ratio = (v / (v_ma + 1e-9)).iloc[-1]
                score_vol = min(vol_ratio, 5.0)
                
                # Composite
                w = self.cfg['weights']
                final = (w['compression']*score_comp) + (w['breakout']*score_brk) + (w['volume']*score_vol)
                
                # Gates (Spec: Phase 30 Fixed)
                # 1. Compression: Width Z-Score < 0 (Narrow)
                # 2. Breakout: (Close / 20d High) - 1 > 0.15%
                # 3. Volume: Ratio > 1.3
                
                g = self.cfg['gates'] # Ensure g is defined
                w_z_val = w_z.iloc[-1]
                
                # [AESTHETIC] Dynamic Threshold
                # Scale Breakout Min by VolAccel
                # If Vol=2.0 -> Gate doubles.
                dynamic_brk_min = g['breakout_min'] * vol_accel
                
                if (w_z_val < 0.0 and 
                    score_brk_val > dynamic_brk_min and 
                    vol_ratio > g['vol_ratio_min']):
                    
                    scores[sym] = {
                        'score': final,
                        'w_z': w_z_val,
                        'brk_val': score_brk_val,
                        'vol_ratio': vol_ratio
                    }
            except:
                continue
                
        # Rank
        if not scores:
            return None, {}
            
        # Top 1
        best_sym = max(scores, key=lambda s: scores[s]['score'])
        
        # Debug Info for Best Sym
        details = scores[best_sym]
        debug = {
             'symbol': best_sym,
             'score': details['score'],
             'w_z': details['w_z'],
             'brk_val': details['brk_val'],
             'vol_ratio': details['vol_ratio'],
             'passed': len(scores)
        }
        
        return best_sym, debug

    def get_fallback_candidate(self, exclude_symbols=[]):
        """
        [Phase 1 Normalization] Top-up Logic.
        Returns best candidate IGNORING strict gates, to maximize exposure.
        """
        scores = {}
        for sym, df in self.history.items():
            if sym in exclude_symbols: continue
            if len(df) < 20: continue
            
            try:
                # Same Factors (Duplicated for consistency)
                c = df['close']
                h = df['high']
                v = df['volume']
                
                # A) Compression
                rolling = c.rolling(window=self.cfg['factors']['bb_window'])
                mid = rolling.mean()
                std = rolling.std()
                width = (mid + 2*std - (mid - 2*std)) / (mid + 1e-9)
                w_mean = width.rolling(window=self.lookback).mean()
                w_std = width.rolling(window=self.lookback).std()
                w_z = (width - w_mean) / (w_std + 1e-9)
                score_comp = -w_z.iloc[-1]
                
                # B) Breakout
                h_20 = h.shift(1).rolling(window=self.cfg['factors']['breakout_window']).max()
                brk_str = (c / (h_20 + 1e-9) - 1.0)
                b_mean = brk_str.rolling(window=self.lookback).mean()
                b_std = brk_str.rolling(window=self.lookback).std()
                score_brk = ((brk_str - b_mean) / (b_std + 1e-9)).iloc[-1]
                
                # C) Volume
                v_ma = v.rolling(window=self.cfg['factors']['vol_ma_window']).mean()
                vol_ratio = (v / (v_ma + 1e-9)).iloc[-1]
                score_vol = min(vol_ratio, 5.0)
                
                # Composite
                w = self.cfg['weights']
                final = (w['compression']*score_comp) + (w['breakout']*score_brk) + (w['volume']*score_vol)
                
                # FALLBACK GATES (Very Relaxed)
                # 1. Must have positive score (better than random)
                # 2. Must not be crashing (Breakout > -2%)
                if final > 0.0 and brk_str.iloc[-1] > -0.02:
                    scores[sym] = final
            except:
                continue
                
        if not scores:
            return None, {}
            
        best_sym = max(scores, key=scores.get)
        return best_sym, {'symbol': best_sym, 'score': scores[best_sym], 'type': 'FALLBACK'}
