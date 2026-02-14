
import subprocess
import time

def monitor_gpu():
    print("=== GPU Activity Monitor ===")
    while True:
        try:
            # nvidia-smi query
            res = subprocess.check_output(['nvidia-smi', '--query-gpu=utilization.gpu,memory.used', '--format=csv,noheader,nounits']).decode('utf-8')
            util, mem = res.strip().split(',')
            print(f"\r[NVIDIA RTX 3060] Usage: {util}% | VRAM: {mem} MB   ", end="")
            time.sleep(1)
        except:
            print("[Error] nvidia-smi not found or failed.")
            break

if __name__ == "__main__":
    monitor_gpu()
