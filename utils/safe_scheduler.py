"""
Safe Scheduler Utility

Provides safeguards for infinite loop prevention in long-running scripts.
Key features:
- Max iterations limit
- Max runtime limit  
- Graceful SIGINT (Ctrl+C) handling
- Health check mechanism
"""

import signal
import logging
from datetime import datetime, timedelta
from typing import Optional, Callable

logger = logging.getLogger(__name__)


class SafeScheduler:
    """
    Safe wrapper for infinite loop schedulers with multiple exit conditions.
    
    Usage:
        scheduler = SafeScheduler(max_iterations=100, max_runtime_hours=24)
        
        while scheduler.should_continue():
            # Do work
            do_something()
            
            # Tick at end of each iteration
            scheduler.tick()
        
        logger.info("Scheduler stopped gracefully")
    """
    
    def __init__(
        self, 
        max_iterations: Optional[int] = None,
        max_runtime_hours: Optional[float] = None,
        health_check_func: Optional[Callable[[], bool]] = None,
        name: str = "SafeScheduler"
    ):
        """
        Initialize SafeScheduler.
        
        Args:
            max_iterations: Maximum number of iterations (None = unlimited)
            max_runtime_hours: Maximum runtime in hours (None = unlimited)
            health_check_func: Optional function that returns True if healthy, False to stop
            name: Name for logging purposes
        """
        self.max_iterations = max_iterations
        self.max_runtime_hours = max_runtime_hours
        self.health_check_func = health_check_func
        self.name = name
        
        self.start_time = datetime.now()
        self.iteration_count = 0
        self.should_stop = False
        self.stop_reason = None
        
        # Register SIGINT handler
        signal.signal(signal.SIGINT, self._signal_handler)
        
        logger.info(f"{self.name} initialized: max_iter={max_iterations}, max_hours={max_runtime_hours}")
    
    def _signal_handler(self, signum, frame):
        """Handle SIGINT (Ctrl+C) gracefully"""
        logger.info(f"{self.name} received SIGINT, will stop after current iteration")
        self.should_stop = True
        self.stop_reason = "SIGINT"
    
    def should_continue(self) -> bool:
        """
        Check if scheduler should continue running.
        
        Returns:
            bool: True if should continue, False if should stop
        """
        # Check manual stop flag
        if self.should_stop:
            logger.info(f"{self.name} stopping: {self.stop_reason}")
            return False
        
        # Check max iterations
        if self.max_iterations is not None and self.iteration_count >= self.max_iterations:
            logger.info(f"{self.name} stopping: reached max iterations ({self.max_iterations})")
            self.stop_reason = "MAX_ITERATIONS"
            return False
        
        # Check max runtime
        if self.max_runtime_hours is not None:
            elapsed = datetime.now() - self.start_time
            max_duration = timedelta(hours=self.max_runtime_hours)
            if elapsed >= max_duration:
                logger.info(f"{self.name} stopping: reached max runtime ({self.max_runtime_hours}h)")
                self.stop_reason = "MAX_RUNTIME"
                return False
        
        # Check health
        if self.health_check_func is not None:
            try:
                if not self.health_check_func():
                    logger.warning(f"{self.name} stopping: health check failed")
                    self.stop_reason = "HEALTH_CHECK_FAILED"
                    return False
            except Exception as e:
                logger.error(f"{self.name} health check error: {e}")
                self.stop_reason = "HEALTH_CHECK_ERROR"
                return False
        
        return True
    
    def tick(self):
        """Increment iteration counter and log progress periodically"""
        self.iteration_count += 1
        
        # Log every 100 iterations or every hour, whichever comes first
        if self.iteration_count % 100 == 0:
            elapsed = datetime.now() - self.start_time
            logger.info(
                f"{self.name} progress: iteration {self.iteration_count}, "
                f"elapsed {elapsed.total_seconds()/3600:.2f}h"
            )
    
    def get_stats(self) -> dict:
        """Get current scheduler statistics"""
        elapsed = datetime.now() - self.start_time
        return {
            "name": self.name,
            "iteration_count": self.iteration_count,
            "elapsed_seconds": elapsed.total_seconds(),
            "elapsed_hours": elapsed.total_seconds() / 3600,
            "stop_reason": self.stop_reason,
            "is_stopped": self.should_stop
        }


def create_daily_scheduler(
    target_hour: int = 15,
    target_minute: int = 35,
    max_days: int = 1,
    name: str = "DailyScheduler"
) -> SafeScheduler:
    """
    Create a scheduler that runs once per day at a specific time.
    
    Args:
        target_hour: Hour to run (0-23)
        target_minute: Minute to run (0-59)
        max_days: Maximum number of days to run
        name: Scheduler name
        
    Returns:
        SafeScheduler configured for daily execution
    """
    # Calculate max iterations based on max_days
    # Each day has ~2880 30-second intervals (24h * 60min * 2)
    # We'll set max_iterations to be safe
    max_iterations = max_days * 3000 if max_days else None
    
    # Convert max_days to hours
    max_runtime_hours = max_days * 24 if max_days else None
    
    return SafeScheduler(
        max_iterations=max_iterations,
        max_runtime_hours=max_runtime_hours,
        name=name
    )
