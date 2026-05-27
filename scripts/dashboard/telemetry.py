"""
Telemetry and Observability module for the SON Dashboard.
Handles structured logging, latency tracking, and memory monitoring.
"""
import time
import psutil
import streamlit as st
import functools
from loguru import logger
from pathlib import Path
from typing import Dict, Any, List
import numpy as np

# Configure Loguru with rotation and retention
LOG_PATH = Path("logs/dashboard.log")
LOG_PATH.parent.mkdir(exist_ok=True)
logger.add(LOG_PATH, rotation="10 MB", retention=5, level="INFO", compression="zip")

class Telemetry:
    """Tracks system performance and health metrics."""
    
    _instance = None
    MEM_THRESHOLD_MB = 800  # Configurable threshold

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Telemetry, cls).__new__(cls)
        return cls._instance

    def _ensure_metrics(self):
        """Ensures metrics are initialized in the current session state."""
        if 'metrics' not in st.session_state:
            st.session_state.metrics = {
                "latencies": {"io": [], "ml": [], "milp": []},
                "errors": {"milp": 0, "io": 0},
                "calls": {"milp": 0, "io": 0}
            }
        return st.session_state.metrics

    def track_latency(self, category: str):
        """Decorator/Context manager to track execution time."""
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                start = time.perf_counter()
                try:
                    result = func(*args, **kwargs)
                    latency = (time.perf_counter() - start) * 1000 # ms
                    m = self._ensure_metrics()
                    m["latencies"][category].append(latency)
                    # Keep only last 100 measurements
                    m["latencies"][category] = m["latencies"][category][-100:]
                    return result
                except Exception as e:
                    logger.error(f"Error in {func.__name__} ({category}): {e}")
                    raise e
            return wrapper
        return decorator

    def log_error(self, category: str):
        """Increments error count for a specific category."""
        m = self._ensure_metrics()
        m["errors"][category] += 1
        m["calls"][category] += 1

    def log_call(self, category: str):
        """Increments total call count for a specific category."""
        m = self._ensure_metrics()
        m["calls"][category] += 1

    @staticmethod
    def check_memory():
        """Monitor RAM usage and clear cache if threshold exceeded, with 60s cooldown."""
        now = time.time()
        
        # Initialize last_clear if not exists
        if 'last_cache_clear' not in st.session_state:
            st.session_state.last_cache_clear = 0
            
        mem = psutil.Process().memory_info().rss / (1024 * 1024) # MB
        
        if mem > Telemetry.MEM_THRESHOLD_MB:
            # Check cooldown (60s)
            if now - st.session_state.last_cache_clear > 60:
                logger.warning(f"Memory threshold exceeded ({mem:.1f} MB). Clearing cache.")
                st.cache_data.clear()
                st.cache_resource.clear()
                st.session_state.last_cache_clear = now
            else:
                logger.info(f"Memory high ({mem:.1f} MB), but skipping clear due to cooldown.")
        return mem

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Returns summarized metrics for the health dashboard."""
        m = self._ensure_metrics()
        summary = {}
        for cat, values in m["latencies"].items():
            if values:
                summary[cat] = {
                    "p50": np.percentile(values, 50),
                    "p95": np.percentile(values, 95),
                    "p99": np.percentile(values, 99)
                }
            else:
                summary[cat] = {"p50": 0, "p95": 0, "p99": 0}
        
        summary["error_rates"] = {
            cat: (m["errors"][cat] / m["calls"][cat] * 100 if m["calls"][cat] > 0 else 0)
            for cat in m["errors"]
        }
        return summary

telemetry = Telemetry()
