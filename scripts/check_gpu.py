
import torch
import sys

def check_gpu():
    print("=== GARAM AI Hardware Accelerator Check ===")
    print(f"Python Version: {sys.version}")
    
    try:
        is_available = torch.cuda.is_available()
        print(f"CUDA Available: {is_available}")
        
        if is_available:
            count = torch.cuda.device_count()
            print(f"GPU Count: {count}")
            for i in range(count):
                print(f"[{i}] {torch.cuda.get_device_name(i)}")
                print(f"    - Memory: {torch.cuda.get_device_properties(i).total_memory / 1024**3:.2f} GB")
                print(f"    - Capability: {torch.cuda.get_device_capability(i)}")
            
            # Simple Tensor Test
            print("\n>> Running Tensor Core Test...")
            x = torch.rand(5000, 5000).cuda()
            y = torch.rand(5000, 5000).cuda()
            msg = "Matrix Multiplication..."
            import time
            s = time.time()
            z = torch.matmul(x, y)
            torch.cuda.synchronize()
            e = time.time()
            print(f"{msg} Done in {e-s:.4f}s (GPU Power Confirmed)")
            return True
        else:
            print("\n[!] No CUDA device detected for PyTorch.")
            return False
            
    except ImportError:
        print("\n[!] PyTorch (`torch`) is not installed or accessible.")
        return False
    except Exception as e:
        print(f"\n[!] Error checking GPU: {e}")
        return False

if __name__ == "__main__":
    check_gpu()
