
import pandas as pd
import glob, os

IN_DIR = "GARAM_Data/5day_replay"
OUT_DIR = "GARAM_Data/5day_replay_kst"
os.makedirs(OUT_DIR, exist_ok=True)

def classify_day_times(ts_series):
    # returns fraction within KST session window
    t = ts_series.dt.time
    # Simple check: is it in 09:00~15:30?
    start = pd.to_datetime("09:00:00").time()
    end = pd.to_datetime("15:30:00").time()
    
    # Handle midnight crossing if necessary (not for KST stock market)
    in_kst = t.between(start, end)
    return in_kst.mean()

def normalize():
    print(f"Normalizing data from {IN_DIR} to {OUT_DIR}...")
    files = glob.glob(os.path.join(IN_DIR, "*.csv"))
    
    for fp in files:
        sym = os.path.basename(fp)
        try:
            df = pd.read_csv(fp)
            if "ts" not in df.columns: continue
            
            df["ts"] = pd.to_datetime(df["ts"], errors="coerce")
            df = df.dropna(subset=["ts"]).copy()

            # Split by Date and normalize per day
            df["date_only"] = df["ts"].dt.date
            unique_dates = df["date_only"].unique()
            
            normalized_chunks = []
            
            for d in unique_dates:
                day_df = df[df["date_only"] == d].copy()
                
                # Check ratio for THIS day
                ratio = classify_day_times(day_df["ts"]) # 0.0 if UTC (00~06), 1.0 if KST (09~15)
                
                # If ratio is low (< 0.6) AND shifting makes it high (> 0.6), Apply Shift
                # But careful about "Empty" or "Small" days
                action_day = "KEEP"
                if ratio < 0.6:
                     # Simulate Shift
                     shifted_ts = day_df["ts"] + pd.Timedelta(hours=9)
                     ratio_shifted = classify_day_times(shifted_ts)
                     
                     if ratio_shifted > 0.6 and ratio_shifted > ratio + 0.3:
                         day_df["ts"] = shifted_ts
                         action_day = "SHIFT"
                
                if action_day == "SHIFT":
                    print(f"{sym} [{d}]: SHIFT+9H (Ratio {ratio:.2f}->{ratio_shifted:.2f})")
                
                normalized_chunks.append(day_df)
            
            # Combine
            if normalized_chunks:
                df = pd.concat(normalized_chunks)
            else:
                 pass # keep full df if no chunks (shouldn't happen)
            
            # Remove helper
            df = df.drop(columns=["date_only"], errors="ignore")
            
            # cleanup + save
            if "date" in df.columns:
                df = df.drop(columns=["date"], errors="ignore")
            
            # STRICT TRIM: 09:00 - 15:30 ONLY
            t = df["ts"].dt.time
            start_t = pd.to_datetime("09:00:00").time()
            end_t = pd.to_datetime("15:30:00").time()
            df = df[(t >= start_t) & (t <= end_t)]
            
            if df.empty:
                print(f"{sym}: Empty after trim")
                continue

            df = df.sort_values("ts").drop_duplicates(subset=["ts"], keep="last")
            out_fp = os.path.join(OUT_DIR, sym)
            df.to_csv(out_fp, index=False)
                
        except Exception as e:
            print(f"Error {sym}: {e}")

    print("Done. Output:", OUT_DIR)

if __name__ == "__main__":
    normalize()
