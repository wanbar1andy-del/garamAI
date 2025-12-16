# scripts/research/universe_loader.py
from __future__ import annotations

from pathlib import Path
from typing import List
import yaml

def load_universe_symbols(universe_path: str | Path) -> List[str]:
    p = Path(universe_path)
    if not p.exists():
        raise FileNotFoundError(f"Universe file not found: {p}")

    if p.suffix.lower() == ".csv":
        import pandas as pd
        df = pd.read_csv(p, dtype=str)
        # Try common columns
        for col in ["Code", "Symbol", "symbol", "code", "KS_CODE"]:
            if col in df.columns:
                symbols = df[col].tolist()
                # Remove leading 'A' if present for some formats, though standard is 6 digit
                # Ensure we strictly treat them as strings
                return sorted(list(set([str(s).strip() for s in symbols if str(s).strip()])))
        # If no header, maybe first column?
        return sorted(list(set([str(s).strip() for s in df.iloc[:,0].tolist() if str(s).strip()])))

    data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}

    # 유연한 포맷 지원:
    # 1) symbols: ["005930","000660"]
    # 2) universe: ["005930","000660"]
    # 3) items: [{symbol:"005930"}, {symbol:"000660"}]
    if isinstance(data, dict):
        if "symbols" in data and isinstance(data["symbols"], list):
            symbols = data["symbols"]
        elif "universe" in data and isinstance(data["universe"], list):
            symbols = data["universe"]
        elif "items" in data and isinstance(data["items"], list):
            symbols = [it.get("symbol") for it in data["items"] if isinstance(it, dict) and it.get("symbol")]
        else:
            symbols = []
    elif isinstance(data, list):
        symbols = data
    else:
        symbols = []

    symbols = [str(s).strip() for s in symbols if str(s).strip()]
    # 중복 제거 + 정렬
    symbols = sorted(list(dict.fromkeys(symbols)))
    if not symbols:
        raise ValueError(f"No symbols found in universe file: {p}")
    return symbols
