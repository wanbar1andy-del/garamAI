from __future__ import annotations
from pathlib import Path
import pandas as pd

def _z6(symbol: str) -> str:
    s = str(symbol).strip()
    if not s.isdigit():
        raise ValueError(f"[STORE] invalid symbol (non-digit): {symbol}")
    return s.zfill(6)

def load_validated_minute_csv(symbol: str, validated_minute_dir: Path) -> pd.DataFrame:
    """
    STRICT READER:
    - Reads ONLY from validated_minute_dir/{symbol}.csv
    - Falls back to nothing (raises FileNotFoundError)
    - Enforces dtype={'date': str} to prevent timestamp corruption
    """
    sym = _z6(symbol)
    path = validated_minute_dir / f"{sym}.csv"
    if not path.exists():
        raise FileNotFoundError(f"[STORE] missing validated minute: {path}")

    # FORCE DTYPE: critical for date parsing safety
    df = pd.read_csv(path, dtype={"date": str})
    
    # Minimal Schema Check (Lightweight)
    need = ["date","open","high","low","close","volume"]
    missing = [c for c in need if c not in df.columns]
    if missing:
        raise ValueError(f"[STORE] schema mismatch {sym}: missing={missing}")

    return df
