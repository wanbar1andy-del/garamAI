import time
import subprocess
import os
from datetime import datetime
from pathlib import Path

def run_cmd(cmd):
    print(f"[{datetime.now()}] RUN: {cmd}")
    os.system(cmd)

def main():
    dt = datetime.now().strftime("%Y-%m-%d")
    dt_compact = datetime.now().strftime("%Y%m%d")
    
    # Paths
    tape_script = r"scripts\phase24\build_decision_tape.py"
    ops_script = r"scripts\phase25\run_paper_ops_tracks.bat"
    
    tape_out = Path(f"results/phase25/paper_ops/live_tape/decision_tape_{dt_compact}.csv")
    
    # Ensure live tape dir
    tape_out.parent.mkdir(parents=True, exist_ok=True)

    print(f"=== Starting Live Loop for {dt} ===")
    
    while True:
        # 1. Build Tape (Phase 24)
        # We assume data is being collected by external collector. 
        # We run builder to update decision_tape.csv from whatever data is in GARAM_Data.
        # Output tag: live_tape -> results/phase24/tape/live_tape/decision_tape_{dt}_{dt}.csv
        cmd_tape = f"python {tape_script} --start_date {dt} --end_date {dt} --out_tag live_tape"
        run_cmd(cmd_tape)
        
        # Move/Copy to Ops Location
        src_tape = Path(f"results/phase24/tape/live_tape/decision_tape_{dt}_{dt}.csv")
        if src_tape.exists():
            # Copy to target
            print(f"[{datetime.now()}] Copying tape to {tape_out}")
            if tape_out.exists():
                os.remove(tape_out)
            import shutil
            shutil.copy(src_tape, tape_out)
        else:
            print(f"[{datetime.now()}] WARN: Generated tape not found at {src_tape}")

        # 2. Run Paper Ops (Phase 25)
        # This reads the tape we just updated
        run_cmd(ops_script)
        
        print(f"[{datetime.now()}] Cycle done. Sleeping 60s...")
        time.sleep(60)

if __name__ == "__main__":
    main()
