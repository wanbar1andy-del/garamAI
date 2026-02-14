import pandas as pd
import numpy as np
from pathlib import Path
import sys
from datetime import timedelta

# Setup Paths
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

class SignalMiner:
    def __init__(self, start_date, end_date):
        self.start_date = pd.Timestamp(start_date)
        self.end_date = pd.Timestamp(end_date)
        self.hero_segments = self.load_all_hero_segments()
        self.out_dir = project_root / "results" / "mining" / "week1"
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.birth_samples = []
        self.death_samples = []
        
    def load_all_hero_segments(self):
        segments = []
        current = self.start_date
        while current <= self.end_date:
            ymd = current.strftime("%Y%m%d")
            path = project_root / "results" / "labels" / f"day={ymd}" / "hero_segments.csv"
            if path.exists():
                df = pd.read_csv(path)
                df['start_time'] = pd.to_datetime(df['start_time'])
                df['end_time'] = pd.to_datetime(df['end_time'])
                segments.append(df)
            current += timedelta(days=1)
        return pd.concat(segments, ignore_index=True) if segments else pd.DataFrame()

    def load_minute_data(self, symbol, date_str):
        p = project_root / "GARAM_Data" / "history" / "minute" / f"{str(symbol).zfill(6)}.csv"
        if not p.exists():
            return None
        df = pd.read_csv(p, usecols=['date', 'open', 'high', 'low', 'close', 'volume'])
        df = df[df['date'].astype(str).str.startswith(date_str)].copy()
        df['date'] = pd.to_datetime(df['date'], format='%Y%m%d%H%M%S', errors='coerce')
        df.dropna(subset=['date'], inplace=True)
        df.set_index('date', inplace=True)
        return df

    def extract_features(self, df, t_target, lookback=10):
        start_win = t_target - timedelta(minutes=lookback)
        ts_slice = df.loc[start_win:t_target]
        if len(ts_slice) < 5:
            return None
        
        current_close = ts_slice['close'].iloc[-1]
        current_vol = ts_slice['volume'].iloc[-1]
        
        vol_ma = ts_slice['volume'].mean()
        vol_accel = current_vol / vol_ma if vol_ma > 0 else 0
        
        cum_vol = ts_slice['volume'].cumsum()
        cum_pv = (ts_slice['close'] * ts_slice['volume']).cumsum()
        vwap_local = cum_pv.iloc[-1] / cum_vol.iloc[-1] if cum_vol.iloc[-1] > 0 else current_close
        vwap_div = (current_close / vwap_local) - 1.0
        
        p_5m_ago = ts_slice['close'].iloc[-5] if len(ts_slice) >= 5 else ts_slice['close'].iloc[0]
        roc_5 = (current_close / p_5m_ago) - 1.0
        
        return {"vol_accel": vol_accel, "vwap_div": vwap_div, "roc_5m": roc_5}

    def run(self):
        total_segs = len(self.hero_segments)
        for idx, seg in self.hero_segments.iterrows():
            if idx % 50 == 0: print(f"Processing {idx}/{total_segs}...")
            sym = seg['symbol']
            t_start = seg['start_time']
            t_end = seg['end_time']
            date_str = t_start.strftime("%Y%m%d")
            df = self.load_minute_data(sym, date_str)
            if df is None or df.empty:
                continue
            
            # Birth positive
            t_birth = t_start - timedelta(minutes=1)
            feats = self.extract_features(df, t_birth)
            if feats:
                feats.update({"label": 1, "symbol": sym, "time": t_birth})
                self.birth_samples.append(feats)
            
            # Birth negative (far before)
            t_neg = t_start - timedelta(minutes=30)
            if t_neg in df.index:
                feats = self.extract_features(df, t_neg)
                if feats:
                    feats.update({"label": 0, "symbol": sym, "time": t_neg})
                    self.birth_samples.append(feats)

            # Death positive
            t_death = t_end - timedelta(minutes=1)
            feats = self.extract_features(df, t_death)
            if feats:
                feats.update({"label": 1, "symbol": sym, "time": t_death})
                self.death_samples.append(feats)

            # Death negative (mid segment)
            t_mid = (t_start + (t_end - t_start) / 2).round('1T')
            if t_mid in df.index:
                feats = self.extract_features(df, t_mid)
                if feats:
                    feats.update({"label": 0, "symbol": sym, "time": t_mid})
                    self.death_samples.append(feats)

        self.save_results()

    def save_results(self):
        pd.DataFrame(self.birth_samples).to_csv(self.out_dir / "mining_birth_features.csv", index=False)
        pd.DataFrame(self.death_samples).to_csv(self.out_dir / "mining_death_features.csv", index=False)
        print(f"Saved {len(self.birth_samples)} birth samples and {len(self.death_samples)} death samples.")

if __name__ == "__main__":
    SignalMiner("2025-12-15", "2025-12-19").run()
