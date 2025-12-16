# scripts/migrate_data_standard.py
from __future__ import annotations

import shutil
import sys
from pathlib import Path

# Add project root to sys.path to find garam_core
sys.path.append(str(Path(__file__).resolve().parents[1]))

from garam_core.health.gate import gate_environment

def main():
    print(">>> Starting Data Migration (Option A: Standardization)...")
    
    # 1. Resolve Data Root via Gate0
    project_root = Path("c:/garam/garam/garam_core")
    paths = gate_environment(project_root)
    data_root = paths.data_root
    
    print(f"Data Root: {data_root}")
    
    # Sources (Legacy)
    src_dir = data_root / "minute" / "kr"
    
    # Destination (Standard)
    dst_dir = data_root / "history" / "minute"
    dst_dir.mkdir(parents=True, exist_ok=True)
    
    if not src_dir.exists():
        print(f"[SKIP] Source directory not found: {src_dir}")
        return

    # Scan and Move
    files = list(src_dir.glob("*_1m.csv"))
    print(f"Found {len(files)} legacy files in {src_dir}")
    
    count = 0
    for p in files:
        # 005930_1m.csv -> 005930.csv
        symbol = p.stem.replace("_1m", "")
        new_name = f"{symbol}.csv"
        target = dst_dir / new_name
        
        # Copy to ensure safety (Move is riskier if something goes wrong, but let's do move for speed if user wants migration. 
        # Actually user said 'Standardize', let's use move but check dest)
        if target.exists():
            print(f"[SKIP] Target exists: {target.name}")
            continue
            
        shutil.move(str(p), str(target))
        count += 1
        
    print(f"Migrated {count} files to {dst_dir}")
    
    # Check if empty, maybe remove source? NO, safety first. Leave empty dir or manual cleanup.
    # User just asked to move files.
    
    print(">>> Migration Complete.")

if __name__ == "__main__":
    main()
