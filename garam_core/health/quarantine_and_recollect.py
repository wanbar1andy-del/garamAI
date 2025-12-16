# garam_core/health/quarantine_and_recollect.py
from __future__ import annotations

from pathlib import Path
from typing import List, Dict
import pandas as pd
import shutil


def quarantine_files(
    base_dir: Path,
    corrupt_list: List[Dict[str, str]],
    quarantine_dir: Path,
) -> List[Dict[str, str]]:
    """
    Moves corrupt files to quarantine_dir preserving names.
    Returns list of moved files.
    """
    quarantine_dir.mkdir(parents=True, exist_ok=True)
    moved = []
    for item in corrupt_list:
        name = item.get("file")
        if not name:
            continue
        src = base_dir / name
        if src.exists():
            dst = quarantine_dir / name
            shutil.move(str(src), str(dst))
            moved.append({"file": name, "from": str(src), "to": str(dst)})
    return moved


def write_recollect_csv(
    symbols: List[str],
    out_path: Path,
) -> None:
    """
    Writes recollect targets to CSV.
    """
    df = pd.DataFrame({"symbol": symbols})
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False, encoding="utf-8")
