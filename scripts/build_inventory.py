import os
import ast
import time
from pathlib import Path
from datetime import datetime
import collections

# --- CONFIGURATION (SSOT Rules) ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent
IGNORE_DIRS = {
    "GARAM_Data", "logs", "results", "backup", "cache", 
    "__pycache__", ".git", ".venv", ".vscode", ".idea", "site-packages"
}
DOCS_DIR = PROJECT_ROOT / "docs"

# --- TO-BE STRUCTURE MAPPING (Heuristic) ---
ROLE_MAPPING = {
    "pipeline": "PIPELINE",
    "garam_core": "CORE_LEGACY",
    "scripts": "SCRIPTS",
    "ui": "UI",
    "tests": "TESTS",
    "config": "CONFIG",
    "data": "DATA_ASSETS",
    "docs": "DOCS"
}

def is_ignored(path_parts):
    for part in path_parts:
        if part in IGNORE_DIRS or part.startswith('.'):
            return True
    return False

def get_file_info(filepath):
    stat = os.stat(filepath)
    size_str = f"{stat.st_size / 1024:.1f} KB"
    mtime = datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M')
    return size_str, mtime

def guess_target_stage(rel_path_str):
    # Simple heuristics for V2 Stage Recommendation
    if "ingest" in rel_path_str or "collector" in rel_path_str:
        return "01_INGEST"
    if "validate" in rel_path_str or "integrity" in rel_path_str:
        return "02_VALIDATE"
    if "loader" in rel_path_str or "store" in rel_path_str:
        return "03_STORE"
    if "feature" in rel_path_str:
        return "04_FEATURE"
    if "signal" in rel_path_str or "strategy" in rel_path_str or "hero" in rel_path_str:
        return "05_SIGNAL"
    if "monitor" in rel_path_str or "log" in rel_path_str:
        return "06_MONITOR"
    if "execution" in rel_path_str or "order" in rel_path_str:
        return "07_EXECUTION"
    if "engine" in rel_path_str or "manager" in rel_path_str:
        return "08_ORCHESTRATOR"
    if "ui" in rel_path_str or "dashboard" in rel_path_str or "server" in rel_path_str:
        return "09_DASHBOARD"
    return "TBD"

def scan_project(root_path):
    inventory = []
    py_files = []
    
    print(f"Scanning {root_path}...")
    
    for root, dirs, files in os.walk(root_path):
        # In-place filtering of dirs to avoid walking ignored ones
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and not d.startswith('.')]
        
        for file in files:
            full_path = Path(root) / file
            rel_path = full_path.relative_to(root_path)
            
            if is_ignored(rel_path.parts):
                continue
                
            size, mtime = get_file_info(full_path)
            
            # Determine Top-Level Role
            top_level = rel_path.parts[0] if len(rel_path.parts) > 0 else "ROOT"
            role = ROLE_MAPPING.get(top_level, "OTHER")
            
            inventory.append({
                "path": str(rel_path).replace("\\", "/"),
                "type": file.split('.')[-1] if '.' in file else "NO_EXT",
                "size": size,
                "last_modified": mtime,
                "current_role": role,
                "target_stage_guess": guess_target_stage(str(rel_path).lower()),
                "status": "ACTIVE" 
            })
            
            if file.endswith(".py"):
                py_files.append(full_path)
                
    return inventory, py_files

def analyze_imports(py_files, root_path):
    # Map: module_name -> list of dependencies
    dependencies = collections.defaultdict(set)
    
    for file_path in py_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read())
        except Exception as e:
            print(f"Skipping AST parse for {file_path}: {e}")
            continue
            
        rel_path = file_path.relative_to(root_path)
        module_name = str(rel_path).replace("\\", "/").replace(".py", "").replace("/", ".")
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    dependencies[module_name].add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    dependencies[module_name].add(node.module)

    return dependencies

def generate_inventory_md(inventory):
    lines = ["# Project Inventory (AS-IS Analysis)", "", "| Path | Type | Size | Last Modified | Current Role | Target Stage (Guess) | Status |", "|---|---|---|---|---|---|---|"]
    
    # Sort by path
    inventory.sort(key=lambda x: x['path'])
    
    for item in inventory:
        line = f"| `{item['path']}` | {item['type']} | {item['size']} | {item['last_modified']} | {item['current_role']} | {item['target_stage_guess']} | {item['status']} |"
        lines.append(line)
        
    return "\n".join(lines)

def generate_dependency_graph_md(dependencies):
    lines = ["# Dependency Graph (Visualize via Mermaid)", "", "```mermaid", "graph TD"]
    
    # Create subgraphs for top-level modules
    lines.append("    subgraph scripts")
    lines.append("    style scripts fill:#f9f,stroke:#333,stroke-width:2px")
    for mod in dependencies:
        if mod.startswith("scripts."):
            lines.append(f"    {mod.replace('.', '_')}[{mod}]")
    lines.append("    end")

    lines.append("    subgraph garam_core")
    lines.append("    style garam_core fill:#bbf,stroke:#333,stroke-width:2px")
    for mod in dependencies:
        if mod.startswith("garam_core."):
            lines.append(f"    {mod.replace('.', '_')}[{mod}]")
    lines.append("    end")
    
    lines.append("    subgraph pipeline")
    lines.append("    style pipeline fill:#bfb,stroke:#333,stroke-width:2px")
    for mod in dependencies:
        if mod.startswith("pipeline."):
            lines.append(f"    {mod.replace('.', '_')}[{mod}]")
    lines.append("    end")

    # Add edges (Limit to internal dependencies to reduce noise)
    internal_prefixes = ["garam_core", "pipeline", "scripts", "ui", "utils"]
    
    edge_count = 0
    for src, targets in dependencies.items():
        src_id = src.replace('.', '_')
        for tgt in targets:
            is_internal = any(tgt.startswith(p) for p in internal_prefixes)
            if is_internal:
                tgt_id = tgt.replace('.', '_')
                lines.append(f"    {src_id} --> {tgt_id}")
                edge_count += 1
                
    lines.append("```")
    lines.append(f"\n*Total Internal Edges: {edge_count}*")
    return "\n".join(lines)

def generate_mapping_table_md(inventory):
    lines = ["# Refactoring Mapping Table", "", "| AS-IS Path | TO-BE Path (Proposed) | Status | Note |", "|---|---|---|---|"]
    
    inventory.sort(key=lambda x: x['path'])
    for item in inventory:
        # Suggest V2 path
        tobe = ""
        stage = item['target_stage_guess']
        if stage != "TBD":
            filename = os.path.basename(item['path'])
            stage_dir = stage.lower().split('_')[-1] # e.g., 01_INGEST -> ingest
            tobe = f"pipeline/{stage}/{filename}"
        
        lines.append(f"| `{item['path']}` | `{tobe}` | OPEN | {item['current_role']} |")
        
    return "\n".join(lines)

def generate_architecture_v2():
    return """# GARAM V2 Architecture Strategy

## 1. Structure Principles

*   **01-09 Numbered Stages**: Explicit execution order.
*   **Contracts First**: `core/contracts` defines all I/O schemas (DataClasses/Pydantic).
*   **SSOT Everywhere**: No hardcoded paths. All paths from `core/config`.

## 2. Directory Structure (TO-BE)

```text
/pipeline
  /01_ingest       # Data Collection (Kiwoom, etc.)
  /02_validate     # Data Integrity Check & Repair
  /03_store        # Standardized Data Storage (Parquet/DB)
  /04_feature      # Feature Engineering (Technical Indicators)
  /05_signal       # Strategy Logic (HeroFinder, Probe, Regime)
  /06_monitor      # System Health & Alerting
  /07_execution    # Order Management & Execution
  /08_orchestrator # Trading Loop & Main Controller
  /09_dashboard    # UI Backend & API

/core
  /config          # Configuration Loader (paths.yaml)
  /contracts       # Shared Data Models (Artifacts)
  /utils           # Common Utilities
```

## 3. Migration Strategy (Wrapper & Adapter)

1.  **Do Not Move Files Yet**: Create wrappers in `/pipeline/XX_stage/` first.
2.  **Import Legacy**: Wrappers import logic from `garam_core` or `scripts`.
3.  **Refactor Later**: Once the wrapper is working and tested, move the code into the wrapper.

## 4. Key Contracts (Draft)

*   `Universe`: List of symbols to trade.
*   `MarketData`: OHLCV DataFrame + Metadata.
*   `HeroCandidate`: Symbol + Score + Evidence.
*   `OrderSignal`: Symbol + Side + Price + Qty.
*   `PortfolioState`: Current Holdings + Cash + PnL.
"""

def main():
    if not DOCS_DIR.exists():
        DOCS_DIR.mkdir()
        print(f"Created {DOCS_DIR}")
        
    print("Step 1: Scanning project...")
    inventory, py_files = scan_project(PROJECT_ROOT)
    print(f"found {len(inventory)} files.")

    print("Step 2: Analyzing dependencies...")
    dependencies = analyze_imports(py_files, PROJECT_ROOT)
    
    print("Step 3: Generating Artifacts...")
    
    # A. Inventory
    with open(DOCS_DIR / "project_inventory.md", "w", encoding="utf-8") as f:
        f.write(generate_inventory_md(inventory))
    print(" -> docs/project_inventory.md")
    
    # B. Dependency Graph
    with open(DOCS_DIR / "dependency_graph.md", "w", encoding="utf-8") as f:
        f.write(generate_dependency_graph_md(dependencies))
    print(" -> docs/dependency_graph.md")

    # C. Mapping Table
    with open(DOCS_DIR / "refactor_mapping_table.md", "w", encoding="utf-8") as f:
        f.write(generate_mapping_table_md(inventory))
    print(" -> docs/refactor_mapping_table.md")
    
    # D. Architecture V2
    with open(DOCS_DIR / "architecture_v2_overview.md", "w", encoding="utf-8") as f:
        f.write(generate_architecture_v2())
    print(" -> docs/architecture_v2_overview.md")
    
    print("\nPhase 1 Artifact Generation Complete.")

if __name__ == "__main__":
    main()
