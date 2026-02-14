from __future__ import annotations

import sys
from pathlib import Path
import pandas as pd


REQUIRED_COLS = [
    "symbol",
    "champion_score_norm",
    "ref_price",
    "veto",
    "veto_reason",
]

OPTIONAL_BOOL_COLS = ["regime_ban"]  # if exists, must be boolean-like


def _find_latest_scan(results_dir: Path) -> Path:
    scans = sorted(results_dir.glob("hero_scan_*.csv"), key=lambda p: p.stat().st_mtime)
    if not scans:
        raise FileNotFoundError(f"No hero_scan_*.csv found under: {results_dir}")
    return scans[-1]


def _fail(msg: str) -> None:
    print(f"[FAIL] {msg}")
    raise SystemExit(2)


def audit_scan_csv(scan_path: Path) -> None:
    if not scan_path.exists():
        _fail(f"Scan file not found: {scan_path}")

    df = pd.read_csv(scan_path)

    # 1) Required columns exist
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        _fail(f"Missing required columns: {missing}")

    # 2) Basic row sanity
    if df.empty:
        _fail("Scan CSV is empty")

    # 3) Symbol normalization sanity
    sym = df["symbol"].astype(str).str.zfill(6)
    if (sym.str.len() != 6).any():
        _fail("symbol is not 6-digit normalized (zfill(6) expected)")
    df["symbol"] = sym

    # 4) champion_score_norm ∈ [0,1] and not null
    s = pd.to_numeric(df["champion_score_norm"], errors="coerce")
    if s.isna().any():
        _fail("champion_score_norm contains NaN/Non-numeric values")
    if ((s < 0.0) | (s > 1.0)).any():
        bad = df.loc[(s < 0.0) | (s > 1.0), ["symbol", "champion_score_norm"]].head(10)
        _fail(f"champion_score_norm out of [0,1]. sample:\n{bad}")

    # 5) ref_price validity: allow <=0 ONLY if veto=True (SSOT v1.2.0)
    if "ref_price" not in df.columns:
        _fail("missing required column: ref_price")

    p = pd.to_numeric(df["ref_price"], errors="coerce")
    if p.isna().any():
        bad = df.loc[p.isna(), ["symbol", "ref_price", "veto", "veto_reason"]].head(10)
        _fail(f"ref_price contains NaN/non-numeric. sample:\n{bad}")

    # normalize veto to bool
    if "veto" not in df.columns:
        _fail("missing required column: veto")
    
    # helper to normalize veto
    def _to_bool(x):
        s = str(x).lower()
        if s in ("true", "1"): return True
        if s in ("false", "0"): return False
        return bool(x)
    
    veto = df["veto"].map(_to_bool)
    df["veto"] = veto # write back normalized

    invalid_price = (p <= 0)

    # FAIL only if invalid_price and NOT vetoed
    bad_mask = invalid_price & (~veto)
    if bad_mask.any():
        bad = df.loc[bad_mask, ["symbol", "ref_price", "veto", "veto_reason"]].head(10)
        _fail(f"ref_price<=0 must be vetoed (veto=True). sample:\n{bad}")

    # traceability: veto=True must have veto_reason
    if "veto_reason" not in df.columns:
        _fail("missing required column: veto_reason")

    vr = df["veto_reason"].astype(str).fillna("").str.strip()
    bad_vr = veto & (vr == "")
    if bad_vr.any():
        bad = df.loc[bad_vr, ["symbol", "ref_price", "veto", "veto_reason"]].head(10)
        _fail(f"veto=True requires non-empty veto_reason. sample:\n{bad}")

    # optional: report counts (do not fail)
    n_invalid = int(invalid_price.sum())
    n_invalid_vetoed = int((invalid_price & veto).sum())
    # print(f"[INFO] invalid ref_price rows: {n_invalid} (vetoed: {n_invalid_vetoed})")

    # 7) Optional columns: regime_ban must be boolean-like if present
    for c in OPTIONAL_BOOL_COLS:
        if c in df.columns:
            rb = df[c].astype(str).str.lower().map({"true": True, "false": False, "1": True, "0": False})
            if rb.isna().any():
                _fail(f"{c} is present but not boolean-like")
            df[c] = rb.astype(bool)

    # 8) Floor Rule check (if raw is present)
    if "champion_score" in df.columns:
        raw = pd.to_numeric(df["champion_score"], errors="coerce")
        # if raw NaN ignore check, but if numeric then enforce
        mask = raw.notna() & (raw <= 0)
        if mask.any():
            if (s[mask] != 0.0).any():
                bad = df.loc[mask & (s != 0.0), ["symbol", "champion_score", "champion_score_norm"]].head(10)
                _fail(f"Floor Rule violated (raw<=0 => norm must be 0.0). sample:\n{bad}")

    # 9) Veto rule coherence (if ref_price invalid, veto should be true — optional strong enforcement)
    # Here we already enforced ref_price>0, so skip.

    print("[PASS] hero_scan schema/values comply with SSOT v1.2.0")
    print(f"  rows={len(df)} symbols={df['symbol'].nunique()} file={scan_path}")


def main(argv: list[str]) -> int:
    # Usage:
    # python -m scripts.audit_hero_scan_schema [path_to_scan_csv]
    root = Path(__file__).resolve().parent.parent
    results_dir = root / "results"

    if len(argv) >= 2:
        scan_path = Path(argv[1])
        if not scan_path.is_absolute():
            scan_path = (root / scan_path).resolve()
    else:
        scan_path = _find_latest_scan(results_dir)

    audit_scan_csv(scan_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
