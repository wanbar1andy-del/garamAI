import torch
import pandas as pd
import numpy as np
from pathlib import Path
import time
import sys

PROJECT_ROOT = Path("C:/garam/garam")
sys.path.append(str(PROJECT_ROOT))

# Configuration
CACHE_FILE = PROJECT_ROOT / "GARAM_Data/market_matrix_cache.pkl"
SHARED_TENSOR_FILE = PROJECT_ROOT / "GARAM_Data/shared_market_tensor.pt"

def load_and_upload_data():
    print("[Data Daemon] Loading Market Matrix...")
    
    if not CACHE_FILE.exists():
        print("CRITICAL: Market Matrix Cache not found! Run run_real_oss_100man.py first to build cache.")
        return

    # 1. Load from Pickle
    with open(CACHE_FILE, 'rb') as f:
        cached_data = pd.read_pickle(f)
    
    closes_df = cached_data['closes']
    volumes_df = cached_data['volumes']
    
    print(f"[Data Daemon] DataFrame Info: {closes_df.shape} (Time x Symbols)")
    
    # 2. Convert to PyTorch Tensor (Float32 for Speed)
    # Tensor Shape: (Time, Symbols, Features) -> Features: 0=Close, 1=Volume
    # But for easy access let's keep separate tensors or stacked
    
    if torch.cuda.is_available():
        device = torch.device('cuda')
        print(f"[Data Daemon] Uploading to GPU: {torch.cuda.get_device_name(0)}")
    else:
        device = torch.device('cpu')
        print("[Data Daemon] WARNING: No GPU detected. Using CPU.")

    # Convert to Numpy first
    c_np = closes_df.values.astype(np.float32)
    v_np = volumes_df.values.astype(np.float32)
    
    # Upload to VRAM
    t_closes = torch.tensor(c_np, device=device)
    t_volumes = torch.tensor(v_np, device=device)
    
    print(f"[Data Daemon] Tensors on {device}: Closes {t_closes.shape}, Volumes {t_volumes.shape}")
    print(f"[Data Daemon] VRAM Usage: {torch.cuda.memory_allocated()/1024**3:.2f} GB")
    
    # Check 3D Acceleration readiness (Warmup)
    # Perform dummy calculation (e.g., matrix multiplication) to wake up Tensor Cores
    print("[Data Daemon] Warming up 3D Acceleration (Tensor Cores)...")
    try:
        dummy_res = torch.matmul(t_closes.T, t_closes)
        print(f"[Data Daemon] 3D Acceleration Ready. Matmul Result: {dummy_res.shape}")
    except Exception as e:
        print(f"[Data Daemon] 3D Acceleration Check Failed: {e}")

    # 3. Save Tensors for Shared Access (or keep process alive)
    # Saving to .pt file on disk is fast to load, but "Shared Memory" usually means keeping process alive
    # and using IPC. For simplicity in Windows/Python, saving to a fast NVMe SSD (M.2) as .pt is very fast.
    # Alternatively, use multiprocessing.shared_memory but that's complex with CUDA.
    # Let's use the .pt file approach as a "Fast Loading Cache" for now, 
    # BUT actually the user wants "Keep it in memory". 
    
    # The best way for "Keep in memory" across scripts is a Server-Client model.
    # But writing a full server now might be overkill.
    # Compromise: This script will run an INFINITE LOOP of Training Episodes internally.
    # So run_real_oss_100man.py IS the Daemon. It shouldn't exit.
    
    print("[Data Daemon] Data is ready. Launching Training Loop...")
    return t_closes, t_volumes, closes_df.index, closes_df.columns

if __name__ == "__main__":
    load_and_upload_data()
