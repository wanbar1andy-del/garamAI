import subprocess
import time
import sys
import os
from pathlib import Path

def main():
    print(">>> [RealTime Collector] Launching Kiwoom Ingestion GUI...")
    
    # Path to the 32-bit launcher batch file
    bat_path = Path("scripts/run_ingest_32bit.bat")
    
    if not bat_path.exists():
        print(f"Error: {bat_path} not found.")
        return

    # Launch as a separate process (GUI)
    # shell=True required for bat files
    try:
        # We use Popen so we don't block the pipeline
        subprocess.Popen(["cmd.exe", "/c", str(bat_path)], shell=True)
        print(">>> [RealTime Collector] Launched. The GUI window should appear shortly.")
        print(">>> [RealTime Collector] Logic: It will loop continuously until market close.")
    except Exception as e:
        print(f"Failed to launch ingestion: {e}")

if __name__ == "__main__":
    main()
