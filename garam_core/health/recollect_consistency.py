# garam_core/health/recollect_consistency.py
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Set
import pandas as pd


def _list_symbols_from_history(base: Path) -> Set[str]:
    syms = set()
    if not base.exists():
        return syms
    for p in base.glob("*.csv"):
        syms.add(p.stem)
    for p in base.glob("*.parquet"):
        syms.add(p.stem)
    return syms


def load_universe_symbols(universe_path: Path) -> List[str]:
    if not universe_path.exists():
        return []
    txt = universe_path.read_text(encoding="utf-8", errors="replace")
    out: List[str] = []
    for line in txt.splitlines():
        line = line.strip()
        if line.startswith("-"):
            s = line[1:].strip().strip('"').strip("'")
            if s:
                out.append(s)
    # de-dup keep order
    seen = set()
    uniq = []
    for s in out:
        if s not in seen:
            seen.add(s)
            uniq.append(s)
    return uniq


def recollect_consistency_check(
    data_root: Path,
    universe_path: Path,
    timeframe: str = "minute",
) -> Dict[str, object]:
    """
    Returns a dict suitable for JSON/Markdown embedding.
    """
    history_dir = (data_root / "history" / timeframe).resolve()
    universe_syms = load_universe_symbols(universe_path)
    history_syms = _list_symbols_from_history(history_dir)

    u = set(universe_syms)
    h = set(history_syms)

    missing_in_history = sorted(list(u - h))
    extra_in_history = sorted(list(h - u))

    return {
        "timeframe": timeframe,
        "universe_count": len(u),
        "history_count": len(h),
        "missing_in_history": missing_in_history[:50],  # cap for report
        "missing_in_history_count": len(missing_in_history),
        "extra_in_history": extra_in_history[:50],
        "extra_in_history_count": len(extra_in_history),
        "history_dir": str(history_dir),
        "universe_path": str(universe_path),
    }
