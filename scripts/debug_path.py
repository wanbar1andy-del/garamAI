# debug_path.py
import sys
from pathlib import Path

# Try to setup path like scripts do
sys.path.append(str(Path(__file__).resolve().parents[1]))

try:
    import garam_core
    print(f"garam_core location: {garam_core.__file__}")
except ImportError:
    print("garam_core import failed")

try:
    from garam_core.health.gate import gate_environment
    project_root = Path(garam_core.__file__).parent
    print(f"Project Root (derived): {project_root}")
    
    paths = gate_environment(project_root)
    print(f"Gate Data Root: {paths.data_root}")
    print(f"Data Root Exists: {paths.data_root.exists()}")
    
    target = paths.data_root / "primary/minute"
    print(f"Target Primary/Minute: {target}")
    print(f"Target Exists: {target.exists()}")

except Exception as e:
    print(f"Gate Debug Failed: {e}")
