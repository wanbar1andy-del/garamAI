# garam_core/config/settings.py
"""
GARAM Configuration Settings (Local SSOT)

Data path priority:
1. GARAM_DATA_ROOT environment variable (if set)
2. Local repo: C:\garam\garam\GARAM_Data (SSOT)
"""
from __future__ import annotations
import os
from pathlib import Path


def get_repo_root() -> Path:
    """
    Get repository root.
    
    .../garam_core/config/settings.py -> repo root is parents[2]
    """
    return Path(__file__).resolve().parents[2]


def get_data_root() -> Path:
    """
    Get data root path (SSOT: Local first).
    
    Priority:
    1. GARAM_DATA_ROOT environment variable
    2. Local: <repo_root>/GARAM_Data
    
    NO G:\ drive fallback.
    """
    env = os.getenv("GARAM_DATA_ROOT")
    if env:
        return Path(env)
    
    # SSOT: Local GARAM_Data
    local = get_repo_root() / "GARAM_Data"
    return local


def get_minute_data_path(symbol: str) -> Path:
    """
    Get minute data CSV path for a symbol.
    
    Args:
        symbol: Stock symbol (6-digit format, e.g., "005930")
    
    Returns:
        Path to minute CSV file
    """
    return get_data_root() / "history" / "minute" / f"{symbol}.csv"


def get_daily_data_path(symbol: str) -> Path:
    """
    Get daily data CSV path for a symbol.
    
    Args:
        symbol: Stock symbol
    
    Returns:
        Path to daily CSV file
    """
    return get_data_root() / "history" / "daily" / f"{symbol}_daily.csv"
