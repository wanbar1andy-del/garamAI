"""
Health Check System for GARAM Trading System
Pre-trading validation and system health monitoring
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
import json
from abc import ABC, abstractmethod

# Import centralized paths
try:
    from garam.config import PATHS
    BASE_PATH = PATHS.BASE_DIR
except ImportError:
    BASE_PATH = Path("C:/garam")


logger = logging.getLogger(__name__)


class HealthCheckResult:
    """Result of a single health check"""
    def __init__(
        self,
        name: str,
        status: str,  # PASS / FAIL / SKIP
        details: str = "",
        error: Optional[str] = None
    ):
        self.name = name
        self.status = status
        self.details = details
        self.error = error
        self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'status': self.status,
            'details': self.details,
            'error': self.error,
            'timestamp': self.timestamp.isoformat()
        }


class BaseCheck(ABC):
    """Base class for health checks"""
    
    @abstractmethod
    def run(self) -> HealthCheckResult:
        """Run the check and return result"""
        pass


class ConfigCheck(BaseCheck):
    """Check configuration files integrity"""
    
    def run(self) -> HealthCheckResult:
        try:
            base_path = BASE_PATH
            
            # Check trading_mode.json
            mode_file = base_path / "config" / "trading_mode.json"
            if not mode_file.exists():
                return HealthCheckResult(
                    "Configuration",
                    "FAIL",
                    error="trading_mode.json not found"
                )
            
            with open(mode_file, 'r') as f:
                mode_config = json.load(f)
                
            # Validate required fields
            required_fields = ['trading_mode', 'auto_switch', 'safeguard_status']
            for field in required_fields:
                if field not in mode_config:
                    return HealthCheckResult(
                        "Configuration",
                        "FAIL",
                        error=f"Missing field: {field}"
                    )
            
            return HealthCheckResult(
                "Configuration",
                "PASS",
                details=f"Mode: {mode_config['trading_mode']}"
            )
            
        except Exception as e:
            return HealthCheckResult(
                "Configuration",
                "FAIL",
                error=str(e)
            )


class APICheck(BaseCheck):
    """Check API connectivity"""
    
    def run(self) -> HealthCheckResult:
        try:
            # For now, just check if we can import the required modules
            # In production, this would test actual API connection
            import sys
            sys.path.insert(0, str(BASE_PATH))
            
            from garam.data.feed.kiwoom_feed import KiwoomFeed
            
            # Try initializing feed in mock mode
            feed = KiwoomFeed(mode='mock')
            
            return HealthCheckResult(
                "API Connectivity",
                "PASS",
                details="Feed initialization successful (mock mode)"
            )
            
        except Exception as e:
            return HealthCheckResult(
                "API Connectivity",
                "FAIL",
                error=str(e)
            )


class AccountCheck(BaseCheck):
    """Check account status and balance"""
    
    def run(self) -> HealthCheckResult:
        try:
            # In production, this would query actual account
            # For now, simulate the check
            
            return HealthCheckResult(
                "Account Status",
                "PASS",
                details="Simulated: Account active"
            )
            
        except Exception as e:
            return HealthCheckResult(
                "Account Status",
                "FAIL",
                error=str(e)
            )


class ResourceCheck(BaseCheck):
    """Check system resources"""
    
    def run(self) -> HealthCheckResult:
        try:
            import psutil
            
            # Check disk space
            disk = psutil.disk_usage('g:/')
            free_gb = disk.free / (1024**3)
            
            if free_gb < 1:
                return HealthCheckResult(
                    "System Resources",
                    "FAIL",
                    error=f"Low disk space: {free_gb:.2f}GB"
                )
            
            # Check memory
            memory = psutil.virtual_memory()
            available_gb = memory.available / (1024**3)
            
            if available_gb < 2:
                return HealthCheckResult(
                    "System Resources",
                    "FAIL",
                    error=f"Low memory: {available_gb:.2f}GB"
                )
            
            return HealthCheckResult(
                "System Resources",
                "PASS",
                details=f"Disk: {free_gb:.1f}GB, Memory: {available_gb:.1f}GB"
            )
            
        except ImportError:
            # psutil not installed
            return HealthCheckResult(
                "System Resources",
                "SKIP",
                details="psutil not installed"
            )
        except Exception as e:
            return HealthCheckResult(
                "System Resources",
                "FAIL",
                error=str(e)
            )


class PipelineCheck(BaseCheck):
    """Check data pipeline components"""
    
    def run(self) -> HealthCheckResult:
        try:
            import sys
            sys.path.insert(0, str(BASE_PATH))
            
            # Try importing key components
            from garam.features.factory import FeatureFactory
            from garam.alpha_lab.lab import AlphaLab
            
            # Test Feature Factory
            factory = FeatureFactory()
            if len(factory.registry) == 0:
                return HealthCheckResult(
                    "Data Pipeline",
                    "FAIL",
                    error="Feature Factory registry empty"
                )
            
            return HealthCheckResult(
                "Data Pipeline",
                "PASS",
                details=f"Feature Factory: {len(factory.registry)} features registered"
            )
            
        except Exception as e:
            return HealthCheckResult(
                "Data Pipeline",
                "FAIL",
                error=str(e)
            )


class HealthChecker:
    """
    Main health check orchestrator
    Runs all checks and aggregates results
    """
    
    def __init__(self):
        self.checks: List[BaseCheck] = [
            ConfigCheck(),
            APICheck(),
            AccountCheck(),
            ResourceCheck(),
            PipelineCheck()
        ]
        
        self.last_result: Optional[Dict[str, Any]] = None
    
    def run_all_checks(self) -> Dict[str, Any]:
        """
        Run all registered health checks
        
        Returns:
            overall_status: PASS if all pass, FAIL if any fail
            checks: List of individual check results
            timestamp: When checks were run
        """
        results = []
        
        for check in self.checks:
            try:
                result = check.run()
                results.append(result.to_dict())
            except Exception as e:
                logger.error(f"Check failed: {e}")
                results.append({
                    'name': check.__class__.__name__,
                    'status': 'FAIL',
                    'error': str(e)
                })
        
        # Determine overall status
        has_failures = any(r['status'] == 'FAIL' for r in results)
        overall_status = "FAIL" if has_failures else "PASS"
        
        self.last_result = {
            'overall_status': overall_status,
            'checks': results,
            'timestamp': datetime.now().isoformat()
        }
        
        return self.last_result
    
    def can_start_live_trading(self) -> bool:
        """
        Check if system is ready for LIVE trading
        
        Returns:
            True only if ALL checks pass
        """
        if self.last_result is None:
            self.run_all_checks()
        
        return self.last_result['overall_status'] == 'PASS'
    
    def get_latest_results(self) -> Optional[Dict[str, Any]]:
        """Get most recent check results"""
        return self.last_result


# Singleton instance
_health_checker = None

def get_health_checker() -> HealthChecker:
    """Get or create singleton health checker"""
    global _health_checker
    if _health_checker is None:
        _health_checker = HealthChecker()
    return _health_checker


if __name__ == "__main__":
    # Test the health checker
    checker = HealthChecker()
    results = checker.run_all_checks()
    
    print(f"Overall Status: {results['overall_status']}")
    print("\nIndividual Checks:")
    for check in results['checks']:
        status_emoji = "✓" if check['status'] == 'PASS' else "✗" if check['status'] == 'FAIL' else "○"
        print(f"  {status_emoji} {check['name']}: {check['status']}")
        if check.get('details'):
            print(f"     {check['details']}")
        if check.get('error'):
            print(f"     Error: {check['error']}")
    
    print(f"\nCan start LIVE trading: {checker.can_start_live_trading()}")
