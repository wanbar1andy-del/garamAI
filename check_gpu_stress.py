import torch
import time

print("[HARDWARE CHECK] Pinging GPU...")
if torch.cuda.is_available():
    print(f"✅ CUDA Available: {torch.cuda.get_device_name(0)}")
    print(f"Memory Usage: {torch.cuda.memory_allocated()/1024**2:.1f}MB")
    
    # Force heavy load
    print("🔥 Stress Test Initiated...")
    x = torch.randn(10000, 10000, device='cuda')
    y = torch.randn(10000, 10000, device='cuda')
    start = time.time()
    for _ in range(50):
        z = torch.matmul(x, y)
    torch.cuda.synchronize()
    print(f"✅ Calculation Complete in {time.time()-start:.4f}s")
    print("GPU is ALIVE and Working Hard.")
else:
    print("❌ NO CUDA DEVICE FOUND. Running on CPU (SLOW).")
