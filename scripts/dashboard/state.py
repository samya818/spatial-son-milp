"""
Unified State Management for the SON Dashboard - Final V2.0 Edition.
"""
import streamlit as st
from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass
class DemoState:
    """Centralized state for the demo session."""
    scenario: str = "Peak Lunch Rush (13h-14h)"
    selected_slot: int = 26
    threshold: float = 2.0
    threshold_factor: float = 0.85
    expert_mode: bool = False
    freq_view: str = "ALL"
    active_sector: Optional[str] = "site_023_sec1"
    last_simulation_results: Optional[Dict[str, Any]] = None

    @classmethod
    def get_instance(cls):
        """Retrieves or initializes the state in session_state."""
        if 'demo_state' not in st.session_state:
            st.session_state.demo_state = cls()
        return st.session_state.demo_state

    def update(self, **kwargs):
        """Updates multiple state attributes at once."""
        for key, value in kwargs.items():
            setattr(self, key, value)
        st.session_state.demo_state = self
