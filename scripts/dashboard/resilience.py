"""
Resilience and Fault Tolerance module for the SON Dashboard.
Implements Circuit Breaker, Retries, and Fallback patterns.
"""
import time
import functools
import polars as pl
from loguru import logger
from typing import Callable, Any, Optional

def retry(retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """Exponential backoff retry decorator."""
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            m_delay = delay
            for i in range(retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if i == retries - 1:
                        logger.error(f"Final retry failed for {func.__name__}: {e}")
                        raise e
                    logger.warning(f"Retry {i+1}/{retries} for {func.__name__} after {m_delay}s: {e}")
                    time.sleep(m_delay)
                    m_delay *= backoff
            return func(*args, **kwargs)
        return wrapper
    return decorator

class CircuitBreaker:
    """Simple Circuit Breaker pattern to prevent cascading failures."""
    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 30.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failures = 0
        self.last_failure_time = 0
        self.state = "CLOSED" # CLOSED, OPEN, HALF-OPEN

    def call(self, func: Callable, fallback: Callable, *args, **kwargs) -> Any:
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "HALF-OPEN"
                logger.info(f"Circuit Breaker HALF-OPEN for {func.__name__}")
            else:
                return fallback(*args, **kwargs)

        try:
            result = func(*args, **kwargs)
            if self.state == "HALF-OPEN":
                self.state = "CLOSED"
                self.failures = 0
                logger.info(f"Circuit Breaker CLOSED for {func.__name__}")
            return result
        except Exception as e:
            self.failures += 1
            self.last_failure_time = time.time()
            logger.error(f"Circuit Breaker failure {self.failures}/{self.failure_threshold} for {func.__name__}: {e}")
            
            if self.failures >= self.failure_threshold:
                self.state = "OPEN"
                logger.critical(f"Circuit Breaker OPEN for {func.__name__}")
            
            return fallback(*args, **kwargs)

# Global Circuit Breakers for specific components
milp_cb = CircuitBreaker(failure_threshold=3, recovery_timeout=60)
heatmap_cb = CircuitBreaker(failure_threshold=5, recovery_timeout=30)
sankey_cb = CircuitBreaker(failure_threshold=5, recovery_timeout=30)

def milp_fallback(*args, **kwargs):
    """Fallback for MILP: Returns a dummy SimulationResult with error status."""
    logger.error("MILP Fallback triggered.")
    from src.simulation.engine import SimulationResult
    
    return SimulationResult(
        policy="fallback",
        status="ERROR: Solver Failed",
        unsatisfied=0.0,
        unsatisfied_baseline=0.0,
        n_congested=0,
        n_congested_baseline=0,
        mass_error=0.0,
        leakage=0.0,
        decisions=0,
        antenna_results=pl.DataFrame(),
        total_vol=0.0
    )
