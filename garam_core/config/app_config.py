# garam_core/config/app_config.py
from __future__ import annotations
import yaml
from pathlib import Path
from dataclasses import dataclass

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Load .env manually to avoid external dependencies
_env_path = PROJECT_ROOT / ".env"
if _env_path.exists():
    try:
        with open(_env_path, "r", encoding="utf-8") as _f:
            for _line in _f:
                _line = _line.strip()
                if not _line or _line.startswith("#"): continue
                if "=" in _line:
                    _k, _v = _line.split("=", 1)
                    if not os.environ.get(_k.strip()): # Don't overwrite existing
                        os.environ[_k.strip()] = _v.strip()
    except Exception as e:
        print(f"Warning: Failed to load .env: {e}")

@dataclass(frozen=True)
class AppPaths:
    data_root: Path
    logs_root: Path
    reports_root: Path
    config_root: Path
    
    live_data_root: Path
    live_logs: Path
    live_flags: Path
    
    strategy_profile: Path
    strategy_menu: Path
    alpha_catalog: Path
    risk_policies: Path


def load_app_paths() -> AppPaths:
    config_dir = Path(__file__).parent
    paths_yaml = config_dir / "paths.yaml"
    
    if not paths_yaml.exists():
        # Fallback defaults if verification fails
        return AppPaths(
            data_root=PROJECT_ROOT / "data",
            logs_root=PROJECT_ROOT / "logs",
            reports_root=PROJECT_ROOT / "reports",
            config_root=PROJECT_ROOT / "garam_core/config",
            live_data_root=PROJECT_ROOT / "GARAM_Data",
            live_logs=PROJECT_ROOT / "GARAM_Data/logs",
            live_flags=PROJECT_ROOT / "GARAM_Data/flags",
            strategy_profile=PROJECT_ROOT / "garam_core/config/strategy_profile.yaml",
            strategy_menu=PROJECT_ROOT / "garam_core/config/strategy_menu.yaml",
            alpha_catalog=PROJECT_ROOT / "garam_core/config/alpha_catalog.yaml",
            risk_policies=PROJECT_ROOT / "garam_core/config/risk_policies.yaml",
        )

    with open(paths_yaml, "r", encoding="utf-8") as f:
        d = yaml.safe_load(f)
        
    def _p(key, default):
        # Resolve relative to PROJECT_ROOT
        val = d.get(key, default)
        return PROJECT_ROOT / val

    return AppPaths(
        data_root=_p("data_root", "data"),
        logs_root=_p("logs_root", "logs"),
        reports_root=_p("reports_root", "reports"),
        config_root=_p("config_root", "garam_core/config"),
        
        live_data_root=_p("live_data_root", "GARAM_Data"),
        live_logs=_p("live_logs", "GARAM_Data/logs"),
        live_flags=_p("live_flags", "GARAM_Data/flags"),
        
        strategy_profile=_p("strategy_profile", "garam_core/config/strategy_profile.yaml"),
        strategy_menu=_p("strategy_menu", "garam_core/config/strategy_menu.yaml"),
        alpha_catalog=_p("alpha_catalog", "garam_core/config/alpha_catalog.yaml"),
        risk_policies=_p("risk_policies", "garam_core/config/risk_policies.yaml"),
    )

PATHS = load_app_paths()
