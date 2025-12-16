import multiprocessing
import subprocess
import sys
import argparse
import shutil
from pathlib import Path
import time

def run_verify_wrapper(args):
    """
    Args is a tuple (symbol, days) to work with pool.map or starmap
    """
    symbol, days = args
    print(f"[{symbol}] Starting...")
    try:
        cmd = [sys.executable, "scripts/verify_turbo_v3.py", "--symbol", symbol, "--days", str(days)]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        print(f"[{symbol}] Done.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[{symbol}] FAILED. Mean Error: {e.stderr.decode('utf-8')[:100]}...")
        return False

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=8, help="Number of parallel workers")
    parser.add_argument("--days", type=int, default=365, help="Simulation days")
    parser.add_argument("--clean", action="store_true", help="Clean reports directory before running")
    args = parser.parse_args()
    
    universe_path = Path("configs/universe_400.txt")
    if not universe_path.exists():
        print(f"Universe file not found: {universe_path}")
        return
        
    symbols = universe_path.read_text(encoding='utf-8').splitlines()
    symbols = [s.strip() for s in symbols if s.strip()]
    
    print(f"Loaded {len(symbols)} symbols from {universe_path}")
    
    if args.clean:
        print("Cleaning previous reports (reports/verify_turbo_v3_*)...")
        reports_dir = Path("reports")
        if reports_dir.exists():
            for p in reports_dir.glob("verify_turbo_v3_*"):
                if p.is_dir():
                    shutil.rmtree(p)
        print("Clean complete.")
        
    print(f"Starting Grid Execution with {args.workers} workers...")
    start_t = time.time()
    
    # Prepare args for starmap
    task_args = [(sym, args.days) for sym in symbols]
    
    with multiprocessing.Pool(processes=args.workers) as pool:
        results = pool.map(run_verify_wrapper, task_args)
        
    elapsed = time.time() - start_t
    success_count = sum(results)
    
    print(f"Grid Complete in {elapsed:.1f}s")
    print(f"Success: {success_count}/{len(symbols)}")

if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
