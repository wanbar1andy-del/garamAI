import argparse
from pathlib import Path
import sys
import os
import logging

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from garam.research.ai.model_trainer import TrainerConfig, RegimeModelTrainer
from garam.config import PATHS

logging.basicConfig(level=logging.INFO)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    cfg = TrainerConfig(
        dataset_path=Path(args.dataset),
        output_dir=Path(args.out),
    )
    
    trainer = RegimeModelTrainer(cfg)
    
    # Note: We are not passing a loader here, so it will use dummy labels.
    # This is intended for the verification phase where we might not have full history access.
    # In production, we would pass a real loader or ensure the dataset has labels.
    trainer.train_all()
    trainer.save_models()

if __name__ == "__main__":
    main()
