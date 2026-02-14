from __future__ import annotations

from pathlib import Path
import sys
import pandas as pd

# Standard: Run via python -m scripts.sync_universe_to_ingest
# But if run directly, ensure sys path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from pipeline.store.data_loader import store  # SSOT Universe

def main():
    print("[SYNC] Starting Universe Sync (SSOT -> Ingest CSV)...")
    
    df = store.get_universe()
    col = "symbol" if "symbol" in df.columns else ("Code" if "Code" in df.columns else None)
    if col is None:
        raise ValueError(f"[SYNC] universe missing symbol column. cols={df.columns.tolist()}")

    # Format codes for Ingest (raw csv often expects 'Code' column for legacy Kiwoom UI)
    codes = (
        df[col].astype(str).str.strip()
        .map(lambda x: x.zfill(6))
        .tolist()
    )

    out_dir = project_root / "GARAM_Data"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "real_universe_400.csv"

    # Ingest expects "Code" column typically
    out_df = pd.DataFrame({"Code": codes})
    out_df.to_csv(out_path, index=False, encoding="utf-8", lineterminator="\n")

    print(f"[SYNC] wrote: {out_path} rows={len(out_df)}")

if __name__ == "__main__":
    main()
