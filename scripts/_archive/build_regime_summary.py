from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root.parent))

from garam.config import PATHS
from garam.research.regime.summary_builder import RegimeSummaryBuilder

def main():
    # Data directory (G: drive history)
    data_dir = PATHS.DATA_ROOT / "history"
    
    # Config path (Strategy Matrix)
    config_path = PATHS.CONFIG_DIR / "regime_strategy_matrix.yaml"
    
    # Output path (Regime Summary JSON)
    output_path = PATHS.EXPERIMENTS_DIR / "regime_lab" / "regime_summary.json"
    
    builder = RegimeSummaryBuilder(data_dir, config_path)
    
    # We use KOSPI as the representative index for the summary
    target_file = "labeled_KR_KOSPI_daily_20y.csv"
    
    print(f"Building regime summary from {target_file}...")
    print(f"Data Directory: {data_dir}")
    print(f"Output Path: {output_path}")
    
    builder.build_summary(target_file, output_path)

if __name__ == "__main__":
    main()
