"""
Unified State Management for the SON Dashboard - Recruiter Edition.
"""
import streamlit as st
from dataclasses import dataclass
from typing import Optional, Dict

@dataclass
class DemoState:
    """Centralized state for the demo session."""
    scenario: str = "Rush Hour (18h)"
    selected_slot: int = 36
    threshold: float = 1.0
    threshold_factor: float = 0.7
    expert_mode: bool = False
    last_simulation_results: Optional[Dict] = None

    @classmethod
    def get_instance(cls):
        """Retrieves or initializes the state in session_state."""
        if 'demo_state' not in st.session_state:
            st.session_state.demo_state = cls()
        return st.session_state.demo_state

    def update(self, **kwargs):
        """Updates multiple state attributes at once."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        st.session_state.demo_state = self
