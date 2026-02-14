import sys
import os
from pathlib import Path

def check_gate_violations():
    print("=== Gate Violation Checker (Pure Python) ===")
    project_root = Path(__file__).resolve().parent.parent
    
    # Patterns that imply legacy direct access
    patterns = [
        "read_csv",
        "GARAM_Data/history",
        "GARAM_Data/validated",
    ]
    
    # Sub-patterns to refine "read_csv" hits (to reduce noise, though user asked for "read_csv" generally)
    # Actually, user said: rg -n "read_csv\(|history/minute|validated/minute|GARAM_Data|universe_.*\.csv"
    # We will look for these strings.
    
    search_terms = [
        "read_csv(", 
        "history/minute", 
        "validated/minute", 
        "GARAM_Data", 
        "universe_"
    ]

    # Exclude files/directories
    excludes_dirs = [
        ".git", ".idea", "__pycache__", "venv", "env", "logs", 
        "pipeline/_01_ingest", "pipeline/_02_validate", "pipeline/_03_store", # Allowed internals
        "pipeline/ingest", # specific allow
        "garamdata" # output dir
    ]
    
    excludes_files = [
        "check_gate_violations.py", 
        "verify_phase2_e2e.py",
        "project_inventory.md",
        "schema_definition.md",
        "implementation_plan.md",
        "task.md",
        "walkthrough.md",
        "paths.yaml"
    ]

    violations = []
    
    for root, dirs, files in os.walk(project_root):
        # Prune excluded dirs
        dirs[:] = [d for d in dirs if d not in excludes_dirs and not d.startswith(".")]
        
        for file in files:
            if not file.endswith(".py"): continue
            if file in excludes_files: continue
            
            fpath = Path(root) / file
            try:
                # Use utf-8, ignore errors
                content = fpath.read_text(encoding="utf-8", errors="ignore")
                lines = content.splitlines()
                
                for idx, line in enumerate(lines, 1):
                    for term in search_terms:
                        if term in line:
                            # Context check: allow comments? simpler to flag all
                            # Special allowance: config/paths.yaml reference or internal logic
                            # But we are scanning .py files.
                            
                            # Skip if line is a comment (naive check)
                            if line.strip().startswith("#"): continue
                            
                            rel_path = fpath.relative_to(project_root).as_posix()
                            
                            # Whitelist
                            if "pipeline/store/data_loader.py" in rel_path and "load_validated_minute_csv" in line: continue
                            if "garam_core/data/loader.py" in rel_path and "store.get_data" in line: continue
                            
                            violations.append(f"{rel_path}:{idx}: {line.strip()}")
                            break
            except Exception as e:
                print(f"[WARN] Could not read {fpath}: {e}")

    if violations:
        print(f"\n[FAIL] Found {len(violations)} GATE VIOLATIONS:")
        # Sort for readability
        for v in sorted(violations):
            print(f"  {v}")
        sys.exit(1)
    else:
        print("\n[PASS] No gate violations found.")
        sys.exit(0)

if __name__ == "__main__":
    check_gate_violations()
