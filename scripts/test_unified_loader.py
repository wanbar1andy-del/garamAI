
import sys
import os
sys.path.append(os.getcwd())
from pipeline.data.unified_loader import loader
import time

def test_loader():
    print("Testing UnifiedDataLoader...")
    t0 = time.time()
    
    try:
        df_close = loader.load_wide_close()
        print(f"[OK] Loaded Close: {df_close.shape} in {time.time()-t0:.2f}s")
        print(f"Time Range: {df_close.index[0]} ~ {df_close.index[-1]}")
        print(f"Columns (First 5): {df_close.columns[:5].tolist()}")
        print(df_close.iloc[-5:, :5].to_markdown())
        
        t1 = time.time()
        df_vol = loader.load_wide_volume()
        print(f"[OK] Loaded Volume: {df_vol.shape} in {time.time()-t1:.2f}s")
        
    except Exception as e:
        print(f"[FAIL] Loader Error: {e}")

if __name__ == "__main__":
    test_loader()
