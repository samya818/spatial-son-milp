"""
Security and Compliance module for the SON Dashboard.
Handles ID masking, input sanitization, and audit logging.
"""
import hashlib
import hmac
import streamlit as st
from typing import Any
from loguru import logger
from pathlib import Path
from datetime import datetime
from scripts.dashboard.config import config

# Configure Audit Logger
AUDIT_PATH = Path("logs/audit.log")
AUDIT_PATH.parent.mkdir(exist_ok=True)
audit_logger = logger.bind(audit=True)
logger.add(AUDIT_PATH, filter=lambda record: "audit" in record["extra"], format="{time} | {message}")

class Security:
    """Provides security primitives for the dashboard."""
    
    @staticmethod
    def mask_id(raw_id: str, salt: str = "SON_SECRET_2026") -> str:
        """Hashes sensitive antenna IDs using HMAC-SHA256."""
        if not raw_id: return "UNKNOWN"
        return hmac.new(salt.encode(), raw_id.encode(), hashlib.sha256).hexdigest()[:12]

    @staticmethod
    def sanitize_float(val: Any, min_v: float, max_v: float, default: float) -> float:
        """Sanitizes and bounds float inputs."""
        try:
            f_val = float(val)
            return max(min_v, min(max_v, f_val))
        except (ValueError, TypeError):
            return default

    @staticmethod
    def audit_log(user: str, action: str, details: str):
        """Logs user actions to the audit trail."""
        message = f"USER: {user} | ACTION: {action} | DETAILS: {details}"
        audit_logger.info(message)

    @staticmethod
    def check_rate_limit(user_id: str, limit: int = 10, window: int = 60) -> bool:
        """Rate limiting par session Streamlit. 
        WARNING: En production multi-serveur, remplacer st.session_state par Redis/DB."""
        now = datetime.now().timestamp()
        
        # Improved session + IP key to avoid collisions
        client_ip = st.session_state.get('client_ip', 'unknown_ip')
        unique_key = hashlib.md5(f"{user_id}_{client_ip}".encode()).hexdigest()[:16]

        if 'rate_limits' not in st.session_state:
            st.session_state.rate_limits = {}
        
        user_calls = st.session_state.rate_limits.get(unique_key, [])
        # Filter calls in window
        user_calls = [c for c in user_calls if now - c < window]
        
        if len(user_calls) >= limit:
            logger.warning(f"Rate limit exceeded for user key {unique_key}")
            return False
        
        user_calls.append(now)
        st.session_state.rate_limits[unique_key] = user_calls
        return True

security = Security()
