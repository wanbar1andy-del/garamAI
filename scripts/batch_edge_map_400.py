import subprocess
from pathlib import Path
import multiprocessing
import sys

def run_bt(sym):
    # Using sys.executable to ensure same python env
    cmd = [sys.executable, "scripts/verify_turbo_v3.py", "--symbol", sym, "--days", "365"]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

def main():
    u_path = Path("configs/universe_400.txt")
    if not u_path.exists():
        if Path("config/universe_400.txt").exists():
             u_path = Path("config/universe_400.txt")
        else:
             print("Universe not found")
             return

    symbols = u_path.read_text(encoding='utf-8').splitlines()
    symbols = [s.strip() for s in symbols if s.strip()]

    print(f"Total Universe: {len(symbols)}")

    # Resumable Logic: Check existing reports for TODAY (KST)
    import datetime
    # KST is UTC+9. Reports use UTC timestamp filename but maybe we just check 'verify_turbo_v3_{symbol}_YYYYMMDD...'
    # Or just check directory creation time?
    # verify_turbo_v3_005930_20251215_...
    # We check if a directory exists for today's date prefix.
    
    # Calculate Today's Date String in KST or UTC?
    # The script verify_turbo_v3.py uses `pd.Timestamp.utcnow().strftime('%Y%m%d_...')` (Line 257)
    # But wait, date changes at 9AM KST (00:00 UTC).
    # If we run at 10AM KST, it is 1AM UTC. Date matches.
    # So we check `YYYYMMDD` of UTC.
    
    today_str = datetime.datetime.utcnow().strftime('%Y%m%d')
    report_root = Path("garam_core/reports")
    
    done_symbols = set()
    if report_root.exists():
        for item in report_root.iterdir():
            if item.is_dir() and item.name.startswith("verify_turbo_v3_"):
                # Format: verify_turbo_v3_{symbol}_{date}_{time}
                parts = item.name.split('_')
                # verify(0), turbo(1), v3(2), symbol(3), date(4), time(5)
                if len(parts) >= 5:
                    sym_code = parts[3]
                    date_code = parts[4]
                    if date_code == today_str:
                        done_symbols.add(sym_code)

    print(f"Found {len(done_symbols)} completed symbols for today ({today_str}).")
    
    # Filter
    todo_symbols = [s for s in symbols if s not in done_symbols]
    print(f"Remaining to process: {len(todo_symbols)}")

    if not todo_symbols:
        print("All symbols completed. Skipping Backtest.")
        return

    print(f"Starting Batch Backtest for {len(todo_symbols)} symbols...")
    
    with multiprocessing.Pool(processes=8) as pool:
        pool.map(run_bt, todo_symbols)
        
    print("Batch Backtest Complete.")

if __name__ == "__main__":
    main()
