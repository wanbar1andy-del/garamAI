# scripts/cleanup_legacy.py
import os
import shutil
from pathlib import Path

def main():
    print(">>> Starting Legacy Script Cleanup...")
    
    root = Path("c:/garam/garam/scripts")
    archive_dir = root / "_archive"
    archive_dir.mkdir(exist_ok=True)
    
    # Whitelist: Core Rebuild Files (Phase 1-6)
    whitelist = {
        "migrate_data_standard.py",
        "sync_universe.py",
        "verify_turbo_v3.py",
        "research_alpha.py",
        "verify_generalization.py", 
        "run_ingest_32bit.bat",
        "cleanup_legacy.py", # Self
        "__init__.py"
    }
    
    count = 0
    for item in root.iterdir():
        if item.is_dir():
            if item.name == "_archive":
                continue
            # Move subdirs too (e.g. old backtests)
            # But be careful if any are needed. 
            # Current Rebuild uses NO subdirs in scripts.
            pass
        
        if item.is_file():
            if item.name not in whitelist:
                # Move
                try:
                    shutil.move(str(item), str(archive_dir / item.name))
                    count += 1
                except Exception as e:
                    print(f"Failed to move {item.name}: {e}")
                    
    print(f">>> Cleanup Complete. Moved {count} items to scripts/_archive")
    print(">>> Active Scripts Remaining:")
    for f in root.glob("*"):
        if f.is_file():
            print(f" - {f.name}")

    print("\n>>> Phase 2: Root Directory Cleanup...")
    project_root = Path("c:/garam/garam")
    root_archive = root / "_archive" / "root_legacy"
    root_archive.mkdir(parents=True, exist_ok=True)
    
    # Whitelist for Root
    root_whitelist = {
        "garam_core", "scripts", "GARAM_Data", "garamdata", "logs", 
        "pipeline", "tests", "reports", ".git", ".gitignore", ".agent", ".vscode"
    }
    
    # Extensions to move
    extensions = {".py", ".bat", ".ps1", ".txt", ".json", ".csv", ".log", ".html"}
    
    count_root = 0
    for item in project_root.iterdir():
        if item.name in root_whitelist:
            continue
            
        if item.is_file() and item.suffix in extensions:
             try:
                shutil.move(str(item), str(root_archive / item.name))
                count_root += 1
             except Exception as e:
                print(f"Failed to move {item.name}: {e}")
                
    print(f">>> Root Cleanup Complete. Moved {count_root} items to scripts/_archive/root_legacy")

if __name__ == "__main__":
    main()
