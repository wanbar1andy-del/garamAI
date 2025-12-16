# scripts/check_data_availability.py
"""
Data Availability Checker (READ-ONLY)

Uses gate_environment to get correct data paths.
Does NOT modify any files.
"""
import argparse
from pathlib import Path
import pandas as pd
from datetime import datetime
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from garam_core.health.gate import gate_environment


def check_availability(universe_path: str, limit: int = None) -> dict:
    """
    Check data availability for symbols using gate_environment.
    
    Args:
        universe_path: Path to universe CSV
        limit: Optional limit on symbols to check
    
    Returns:
        dict with 'available', 'missing', 'errors'
    """
    if not Path(universe_path).exists():
        raise FileNotFoundError(f"Universe file not found: {universe_path}")
    
    df_universe = pd.read_csv(universe_path, dtype={"symbol": str})
    if "symbol" not in df_universe.columns:
        raise ValueError(f"Universe CSV must have 'symbol' column")
    
    # FIX: 0-padding to 6 digits (e.g., "5930" -> "005930")
    symbols = [str(s).strip().zfill(6) for s in df_universe["symbol"]]
    if limit:
        symbols = symbols[:limit]
    
    # Get paths via gate_environment
    # SSOT v2: CWD is project_root (execution location)
    project_root = Path.cwd()
    paths = gate_environment(project_root)
    data_root = paths.data_root
    
    available = []
    missing = []
    errors = []
    
    # SSOT v2: Output COMPUTED and RESOLVED
    print(f"\n[Data Availability Check - SSOT v2]")
    print(f"PROJECT_ROOT_COMPUTED: {paths.project_root}")
    print(f"DATA_ROOT_COMPUTED: {data_root}")
    
    # RESOLVED for logging only (may show G:\ in GDrive sync)
    try:
        data_root_resolved = data_root.resolve()
    except Exception:
        data_root_resolved = "N/A (resolve failed)"
    print(f"DATA_ROOT_RESOLVED: {data_root_resolved}")
    print(f"Checking {len(symbols)} symbols...\n")
    
    for i, symbol in enumerate(symbols, 1):
        # Construct minute CSV path
        csv_path = data_root / "history" / "minute" / f"{symbol}.csv"
        
        if csv_path.exists():
            try:
                # Verify it's readable
                test_df = pd.read_csv(csv_path, nrows=1)
                available.append(symbol)
                if i % 10 == 0:
                    print(f"  [{i}/{len(symbols)}] ✓")
            except Exception as e:
                errors.append({
                    "symbol": symbol,
                    "path": str(csv_path),
                    "reason": f"Read error: {e}"
                })
        else:
            missing.append({
                "symbol": symbol,
                "path": str(csv_path),
                "reason": "File not found"
            })
    
    return {
        "data_root": str(data_root),
        "available": available,
        "missing": missing,
        "errors": errors
    }


def main():
    parser = argparse.ArgumentParser(description="Check data availability (READ-ONLY)")
    parser.add_argument("--universe", default="data/universe_400.csv")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--out", default=None, help="Output file for missing symbols")
    
    args = parser.parse_args()
    
    result = check_availability(args.universe, args.limit)
    
    print(f"\n{'='*60}")
    print(f"  Results")
    print(f"{'='*60}")
    print(f"Data Root: {result['data_root']}")
    print(f"Available: {len(result['available'])}")
    print(f"Missing: {len(result['missing'])}")
    print(f"Errors: {len(result['errors'])}")
    
    if result['available']:
        print(f"\n[Available Symbols]")
        for sym in result['available'][:10]:
            print(f"  ✓ {sym}")
    
    if result['missing']:
        print(f"\n[Missing Symbols]")
        for item in result['missing'][:10]:
            print(f"  ✗ {item['symbol']}")
            print(f"    Expected: {item['path']}")
        
        if len(result['missing']) > 10:
            print(f"  ... and {len(result['missing']) - 10} more")
    
    if result['errors']:
        print(f"\n[Read Errors]")
        for item in result['errors'][:5]:
            print(f"  ! {item['symbol']}: {item['reason']}")
    
    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(f"# Data Availability Check - {datetime.now()}\n")
            f.write(f"# Data Root: {result['data_root']}\n\n")
            f.write(f"[Available - {len(result['available'])}]\n")
            for sym in result['available']:
                f.write(f"{sym}\n")
            f.write(f"\n[Missing - {len(result['missing'])}]\n")
            for item in result['missing']:
                f.write(f"{item['symbol']}: {item['path']}\n")
            f.write(f"\n[Errors - {len(result['errors'])}]\n")
            for item in result['errors']:
                f.write(f"{item['symbol']}: {item['reason']}\n")
        
        print(f"\n[Output] {out_path}")
    
    print(f"\n{'='*60}\n")
    
    return 0 if len(result['missing']) == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
