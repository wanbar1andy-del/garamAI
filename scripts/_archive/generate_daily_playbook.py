from pathlib import Path
import sys
import datetime as dt

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root.parent))

from garam.config import PATHS
from garam.research.regime.playbook_generator import RegimePlaybookGenerator

def main():
    # Data directory
    data_dir = PATHS.DATA_ROOT / "history"
    
    # Summary path
    summary_path = PATHS.EXPERIMENTS_DIR / "regime_lab" / "regime_summary.json"
    
    # Output directory (Docs)
    # Using G: drive docs folder
    docs_dir = Path("g:/내 드라이브/garam/docs")
    
    generator = RegimePlaybookGenerator(data_dir, summary_path)
    
    # Target file for current regime detection
    target_file = "labeled_KR_KOSPI_daily_20y.csv"
    
    print(f"Generating daily playbook based on {target_file}...")
    print(f"Summary Path: {summary_path}")
    print(f"Output Directory: {docs_dir}")
    
    generator.generate_markdown(target_file, docs_dir)

if __name__ == "__main__":
    main()
