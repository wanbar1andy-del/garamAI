import argparse
from datetime import date
from pathlib import Path
import sys

# Add project root to path to ensure imports work if run as script
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from garam.monitoring.regime_playbook import (
    build_regime_playbook,
    save_playbook_json,
    save_playbook_markdown,
)
from garam.config import PATHS

def main():
    parser = argparse.ArgumentParser(description="Generate Regime Playbook (daily).")
    parser.add_argument("--date", type=str, default=None,
                        help="YYYY-MM-DD (default: today)")
    parser.add_argument("--out-dir", type=str,
                        default=None,
                        help="Output directory for playbook files. Defaults to garamdata/reports.")
    args = parser.parse_args()

    if args.date:
        as_of = date.fromisoformat(args.date)
    else:
        as_of = date.today()

    print(f"Generating Regime Playbook for {as_of}...")

    try:
        pb = build_regime_playbook(as_of=as_of)
        
        if args.out_dir:
            out_dir = Path(args.out_dir)
        else:
            # Default to garamdata/reports
            out_dir = PATHS.DATA_ROOT / "reports"
        
        json_path = save_playbook_json(pb, out_dir)
        md_path = save_playbook_markdown(pb, out_dir)

        print(f"[Success] Playbook generated:")
        print(f"  JSON: {json_path}")
        print(f"  MD  : {md_path}")
        
    except Exception as e:
        print(f"[Error] Failed to generate playbook: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
