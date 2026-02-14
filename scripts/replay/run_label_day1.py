import sys
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings

# Path Setup
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from garam_core.data.loader import load_ohlcv, LoadSpec

# Configuration
CONFIG = {
    "anchor_min": 5,        # 5분 단위 앵커
    "horizon_min": 30,      # 30분 뒤 성과 측정
    "top_k": 5,
    "cost_bps": 10.0,       # 10bps
    "session_start": "09:05", # First anchor
    "session_end": "15:15"    # Last anchor
}

class LabelRunnerDay1:
    def __init__(self, target_date: str):
        self.target_date = target_date # "YYYY-MM-DD"
        self.minute_dir = project_root / "GARAM_Data" / "history" / "minute"
        self.output_dir = project_root / "results" / "labels" / f"day={pd.to_datetime(target_date).strftime('%Y%m%d')}"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Data Containers
        self.price_map = {} # {symbol: pd.Series(close, index=time)}
        self.univ_index = None # pd.Series(index=time)
        
    def load_and_build_index(self):
        print(f"[1/4] Loading Data & Building Universe Index for {self.target_date}...")
        
        all_changes = [] # List of Series
        valid_symbols = []
        
        import gc
        
        # 1. Load 400 symbols
        csv_files = list(self.minute_dir.glob("*.csv"))[:401] # Limit for safety
        if not csv_files:
            print("[ERR] No minute data found.")
            return

        date_ts = pd.Timestamp(self.target_date)
        target_ymd = date_ts.strftime('%Y%m%d') # For string match optimization
        
        print(f"  Found {len(csv_files)} files. Loading...")
        
        cnt = 0
        for f in csv_files:
            sym = f.stem
            try:
                # Optimized Load: Read only necessary columns
                # Check header first isn't worth it, just try/except or assume standard
                # Standard: date, open, high, low, close, volume. We need date, close.
                # However, headers might vary (english/korean).
                # We'll read header first.
                header = pd.read_csv(f, nrows=0).columns.tolist()
                header = [h.lower() for h in header]
                
                usecols = []
                date_col = 'date'
                close_col = 'close'
                
                if 'date' in header: date_col = 'date'
                elif '체결시간' in header: date_col = '체결시간'
                
                if 'close' in header: close_col = 'close'
                elif '현재가' in header: close_col = '현재가'
                
                # Load
                df = pd.read_csv(f, usecols=[date_col, close_col])
                df.rename(columns={date_col: 'date', close_col: 'close'}, inplace=True)
                
                # String based filtering first (faster than datetime conversion for all rows)
                # Assuming YYYYMMDDHHMMSS format (int or str)
                # Filter by string/int prefix
                # This avoids converting massive amount of non-target dates
                df['date_str'] = df['date'].astype(str)
                df = df[df['date_str'].str.startswith(target_ymd)].copy()
                
                if df.empty: continue
                
                # Now Parse DateTime
                df['date'] = pd.to_datetime(df['date_str'], format='%Y%m%d%H%M%S')
                
                df.set_index('date', inplace=True)
                df.sort_index(inplace=True)
                
                # Resample to 1min
                session_idx = pd.date_range(f"{self.target_date} 09:00", f"{self.target_date} 15:30", freq="1T")
                df_res = df.reindex(session_idx, method='ffill')
                
                self.price_map[sym] = df_res['close']
                valid_symbols.append(sym)
                
                # Pct Change for Index
                pct = df_res['close'].pct_change().fillna(0.0)
                all_changes.append(pct)
                
                cnt += 1
                if cnt % 50 == 0:
                    print(f"    Loaded {cnt}/{len(csv_files)}...")
                    gc.collect()
                    
            except Exception as e:
                # print(f"Skip {sym}: {e}")
                pass
                
        print(f"  Loaded {len(valid_symbols)} symbols.")
        if not all_changes:
            print("[ERR] No valid data.")
            sys.exit(1)
            
        # 2. Build Universe Index (Median)
        df_concat = pd.concat(all_changes, axis=1)
        # Median across symbols per minute
        median_chg = df_concat.median(axis=1)
        
        # Construct cumulative index starting at 100.0
        self.univ_index = (1 + median_chg).cumprod() * 100.0
        self.univ_index.name = "Universe_IDX"
        print("  Universe Index Built.")

    def run_labeling(self):
        print("[2/4] Calculating Net Rel Ret & Ranking...")
        
        anchors = pd.date_range(
            f"{self.target_date} {CONFIG['session_start']}", 
            f"{self.target_date} {CONFIG['session_end']}", 
            freq=f"{CONFIG['anchor_min']}T"
        )
        
        records = []
        
        for t in anchors:
            h_min = CONFIG['horizon_min']
            t_fwd = t + timedelta(minutes=h_min)
            
            # Univ Return
            try:
                if t not in self.univ_index.index or t_fwd not in self.univ_index.index:
                    continue
                
                u_t = self.univ_index.loc[t]
                u_fwd = self.univ_index.loc[t_fwd]
                univ_ret = (u_fwd / u_t) - 1.0
            except:
                continue
                
            # Symbol Returns
            step_res = []
            for sym, series in self.price_map.items():
                try:
                    p_t = series.loc[t]
                    p_fwd = series.loc[t_fwd]
                    
                    if pd.isna(p_t) or pd.isna(p_fwd) or p_t <= 0:
                        continue
                        
                    fwd_ret = (p_fwd / p_t) - 1.0
                    rel_ret = fwd_ret - univ_ret
                    net_rel_ret = rel_ret - (CONFIG['cost_bps'] / 10000.0)
                    
                    step_res.append({
                        "symbol": sym, 
                        "net_rel_ret": net_rel_ret,
                        "ref_price": p_t
                    })
                except KeyError:
                    continue
            
            # Ranking
            if not step_res: continue
            
            df_step = pd.DataFrame(step_res)
            df_step.sort_values("net_rel_ret", ascending=False, inplace=True)
            df_step.reset_index(drop=True, inplace=True)
            
            # Assign Rank & Flag
            for rank, row in df_step.iterrows():
                real_rank = rank + 1
                is_hero = 1 if (real_rank <= CONFIG['top_k'] and row['net_rel_ret'] > 0) else 0
                
                records.append({
                    "anchor_time": t,
                    "symbol": row['symbol'],
                    "rank": real_rank,
                    "net_rel_ret": row['net_rel_ret'],
                    "hero_flag": is_hero
                })

        self.df_labels = pd.DataFrame(records)
        print(f"  Generated {len(self.df_labels)} label points.")

    def extract_segments(self):
        print("[3/4] Extracting Hero Segments...")
        
        if self.df_labels.empty:
            print("No labels generated.")
            return

        segments = []
        
        # Group by Symbol
        for sym, sub in self.df_labels.groupby("symbol"):
            sub = sub.sort_values("anchor_time")
            
            # Find continuous blocks where hero_flag == 1
            sub['grp'] = (sub['hero_flag'] != sub['hero_flag'].shift()).cumsum()
            
            for g_id, group in sub[sub['hero_flag'] == 1].groupby('grp'):
                start_time = group['anchor_time'].min()
                end_time = group['anchor_time'].max() # Last anchor in block
                
                duration = (len(group) * CONFIG['anchor_min']) # Approx duration
                
                # Metrics
                score = (group['net_rel_ret'] * CONFIG['anchor_min']).sum() # Area approx
                avg_rank = group['rank'].mean()
                max_ret = group['net_rel_ret'].max()
                total_ret = group['net_rel_ret'].sum()
                
                segments.append({
                    "symbol": sym,
                    "start_time": start_time,
                    "end_time": end_time,
                    "duration_min": duration,
                    "segment_score": score,
                    "avg_rank": avg_rank,
                    "max_rel_ret": max_ret,
                    "total_net_rel_ret": total_ret
                })
                
        self.df_segments = pd.DataFrame(segments)
        if not self.df_segments.empty:
            self.df_segments.sort_values("segment_score", ascending=False, inplace=True)
            
        print(f"  Extracted {len(self.df_segments)} hero segments.")

    def save(self):
        print("[4/4] Saving Results...")
        if self.df_segments.empty:
            print("  No segments to save.")
            # Save empty to satisfy contract
            pd.DataFrame(columns=["symbol","start_time","segment_score"]).to_csv(self.output_dir / "hero_segments.csv")
            return

        seg_path = self.output_dir / "hero_segments.csv"
        rank_path = self.output_dir / "hero_rank.csv"
        
        self.df_segments.to_csv(seg_path, index=False)
        print(f"  Saved: {seg_path}")
        
        # Daily Rank Summary
        # Just top segments
        self.df_segments.head(50).to_csv(rank_path, index=False)
        print(f"  Saved: {rank_path}")

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", type=str, required=True, help="YYYY-MM-DD")
    args = parser.parse_args()
    
    runner = LabelRunnerDay1(args.date)
    runner.load_and_build_index()
    runner.run_labeling()
    runner.extract_segments()
    runner.save()

if __name__ == "__main__":
    main()
