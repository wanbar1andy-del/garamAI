"""
Step 1: Pre-Flight Check (renamed for import compatibility)
Validate system environment before startup.
"""

import sys
import os
from pathlib import Path
import logging
from datetime import datetime
import subprocess

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config import PATHS

# Setup logging
log_dir = PATHS.LOGS_DIR / "startup"
log_dir.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / f"preflight_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PreFlightCheck:
    """Pre-flight system validation"""
    
    def __init__(self):
        self.checks = []
        self.passed = 0
        self.failed = 0
        
    def check(self, name: str, condition: bool, error_msg: str = ""):
        """Run a single check"""
        status = "[PASS]" if condition else "[FAIL]"
        logger.info(f"{status} - {name}")
        
        if condition:
            self.passed += 1
        else:
            self.failed += 1
            if error_msg:
                logger.error(f"  └─ {error_msg}")
        
        self.checks.append({
            'name': name,
            'passed': condition,
            'error': error_msg if not condition else None
        })
        
        return condition
    
    def check_python_version(self):
        """Check Python version >= 3.10"""
        version = sys.version_info
        is_valid = version.major == 3 and version.minor >= 10
        
        self.check(
            "Python Version",
            is_valid,
            f"Python 3.10+ required, found {version.major}.{version.minor}"
        )
        
    def check_required_packages(self):
        """Check required packages installed"""
        required = [
            ('pandas', 'pandas'),
            ('numpy', 'numpy'),
            ('pykiwoom', 'pykiwoom'),
            ('flask', 'flask'),
            ('yaml', 'pyyaml')  # yaml is the import name for pyyaml
        ]
        
        for import_name, package_name in required:
            try:
                __import__(import_name)
                self.check(f"Package: {package_name}", True)
            except ImportError:
                self.check(
                    f"Package: {package_name}",
                    False,
                    f"Install with: pip install {package_name}"
                )
    
    def check_directories(self):
        """Check required directories exist"""
        required_dirs = [
            PATHS.DATA_ROOT,
            PATHS.LOGS_DIR,
            PATHS.EXPERIMENTS_DIR,
            PATHS.CONFIG_DIR
        ]
        
        for dir_path in required_dirs:
            exists = dir_path.exists()
            self.check(
                f"Directory: {dir_path.name}",
                exists,
                f"Create directory: {dir_path}"
            )
            
            if exists:
                # Check write permission
                test_file = dir_path / ".write_test"
                try:
                    test_file.touch()
                    test_file.unlink()
                    self.check(f"Write permission: {dir_path.name}", True)
                except Exception as e:
                    self.check(
                        f"Write permission: {dir_path.name}",
                        False,
                        f"No write permission: {e}"
                    )
    
    def check_config_files(self):
        """Check configuration files exist"""
        config_files = [
            PATHS.CONFIG_DIR / "cost_config.yaml"
        ]
        
        for config_file in config_files:
            exists = config_file.exists()
            self.check(
                f"Config: {config_file.name}",
                exists,
                f"Missing config file: {config_file}"
            )
    
    def check_disk_space(self):
        """Check available disk space"""
        import shutil
        
        try:
            total, used, free = shutil.disk_usage(PATHS.DATA_ROOT)
            free_gb = free / (1024**3)
            
            # Require at least 1GB free
            self.check(
                f"Disk space: {free_gb:.1f} GB free",
                free_gb >= 1.0,
                f"Low disk space: {free_gb:.1f} GB"
            )
        except Exception as e:
            self.check("Disk space", False, str(e))
    
    def run_all_checks(self):
        """Run all pre-flight checks"""
        logger.info("=" * 60)
        logger.info("GARAM PRE-FLIGHT CHECK")
        logger.info("=" * 60)
        
        self.check_python_version()
        self.check_required_packages()
        self.check_directories()
        self.check_config_files()
        self.check_disk_space()
        
        logger.info("=" * 60)
        logger.info(f"RESULTS: {self.passed} passed, {self.failed} failed")
        logger.info("=" * 60)
        
        if self.failed > 0:
            logger.error("[FAIL] PRE-FLIGHT CHECK FAILED")
            logger.error("Fix errors above before proceeding")
            return False
        else:
            logger.info("[PASS] PRE-FLIGHT CHECK PASSED")
            logger.info("System ready for startup")
            return True

def main():
    """Run pre-flight check"""
    checker = PreFlightCheck()
    success = checker.run_all_checks()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
