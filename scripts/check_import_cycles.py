# scripts/check_import_cycles.py
"""
Import Cycle Checker (AST-based)

Verifies no circular dependencies in core modules.
"""
import ast
from pathlib import Path
from typing import Dict, Set, List
import sys


def extract_imports(filepath: Path) -> Set[str]:
    """
    Extract all imported modules from a Python file using AST.
    
    Returns set of module names (e.g., {'garam_core.fastlane.feature_store', ...})
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read())
    except Exception as e:
        print(f"[ERROR] Failed to parse {filepath}: {e}")
        return set()
    
    imports = set()
    
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module)
    
    return imports


def build_dependency_graph(module_paths: Dict[str, Path]) -> Dict[str, Set[str]]:
    """
    Build dependency graph.
    
    Args:
        module_paths: {module_name: filepath}
    
    Returns:
        {module_name: set of imported module names}
    """
    graph = {}
    
    for module_name, filepath in module_paths.items():
        imports = extract_imports(filepath)
        # Filter to only include modules we're tracking
        graph[module_name] = {imp for imp in imports if imp in module_paths}
    
    return graph


def find_cycles(graph: Dict[str, Set[str]]) -> List[List[str]]:
    """
    Find all cycles in dependency graph using DFS.
    
    Returns list of cycles, each cycle is a list of module names.
    """
    cycles = []
    visited = set()
    rec_stack = []
    
    def dfs(node):
        if node in rec_stack:
            # Found cycle
            cycle_start = rec_stack.index(node)
            cycle = rec_stack[cycle_start:] + [node]
            cycles.append(cycle)
            return
        
        if node in visited:
            return
        
        visited.add(node)
        rec_stack.append(node)
        
        for neighbor in graph.get(node, set()):
            dfs(neighbor)
        
        rec_stack.pop()
    
    for node in graph:
        dfs(node)
    
    return cycles


def main():
    # Core modules to check
    root = Path("c:/garam/garam")
    
    modules = {
        "garam_core.fastlane.feature_store": root / "garam_core/fastlane/feature_store.py",
        "garam_core.fastlane.policy_eval": root / "garam_core/fastlane/policy_eval.py",
        "garam_core.analysis.hero_finder": root / "garam_core/analysis/hero_finder.py",
        "garam_core.analysis.edge_decomposer": root / "garam_core/analysis/edge_decomposer.py",
        "garam_core.analysis.capital_policy": root / "garam_core/analysis/capital_policy.py",
    }
    
    print(f"\n{'='*60}")
    print(f"  Import Cycle Check (AST-based)")
    print(f"{'='*60}")
    print(f"Checking {len(modules)} modules...\n")
    
    # Build graph
    graph = build_dependency_graph(modules)
    
    # Print imports
    print("[Import Graph]")
    for module, imports in graph.items():
        short_name = module.split('.')[-1]
        if imports:
            print(f"  {short_name}:")
            for imp in imports:
                imp_short = imp.split('.')[-1]
                print(f"    → {imp_short}")
        else:
            print(f"  {short_name}: (no tracked imports)")
    
    # Find cycles
    cycles = find_cycles(graph)
    
    print(f"\n{'='*60}")
    if cycles:
        print(f"  ⚠️  CIRCULAR DEPENDENCIES FOUND: {len(cycles)}")
        print(f"{'='*60}")
        for i, cycle in enumerate(cycles, 1):
            cycle_short = [m.split('.')[-1] for m in cycle]
            print(f"\nCycle {i}: {' → '.join(cycle_short)}")
        
        print(f"\n[Action Required]")
        print(f"Refactor imports to break circular dependencies.")
        sys.exit(1)
    else:
        print(f"  ✅ NO CIRCULAR DEPENDENCIES")
        print(f"{'='*60}")
        print(f"\nAll modules have clean, one-way dependencies.")
        sys.exit(0)


if __name__ == "__main__":
    main()
