"""
Main entry point for the modular SON Dashboard - Recruiter Edition.
Focused on high-impact demonstration and scientific integrity.
"""
import sys
from pathlib import Path
import streamlit as st
import polars as pl
import logging

# Add project root to sys.path
try:
    root_path = str(Path(__file__).parents[2])
    if root_path not in sys.path:
        sys.path.append(root_path)

    from scripts.dashboard.config import config
    config.validate_paths()
except Exception as e:
    st.error(f"Configuration failure: {e}")
    st.stop()

from scripts.dashboard.data_loader import (
    load_traffic_data, load_topology, load_fractions, 
    load_nominal_capacities
)
from scripts.dashboard.components.sidebar import render_sidebar
from scripts.dashboard.pages import overview, concepts
from scripts.dashboard.telemetry import telemetry

def main():
    """Main application loop."""
    st.set_page_config(
        page_title="SON 4G/LTE Demo | Recruiter Edition",
        page_icon="🛰️",
        layout="wide"
    )

    # Global CSS injection
    st.markdown(f"""
    <style>
        .main {{background-color: {config.BACKGROUND_COLOR};}}
        h1, h2, h3 {{color: #f8fafc !important;}}
        .stMetric label {{color: #94a3b8 !important;}}
        .expert-badge {{background-color: #f59e0b; color: #000; padding: 2px 8px; border-radius: 10px; font-size: 10px; font-weight: bold;}}
    </style>
    """, unsafe_allow_html=True)

    # 1. SIDEBAR & CONTROLS
    state = render_sidebar()

    # 2. DATA LOADING (Cached)
    with st.spinner("🛰️ Loading Industrial Assets (1024 cells)..."):
        traffic_df = load_traffic_data()
        topology = load_topology()
        fractions = load_fractions()
        nominal_caps = load_nominal_capacities()
        
    # Map index 0-47 to real timestamps (base on first day)
    if not traffic_df.is_empty():
        base_slot = traffic_df["slot_30m"].min()
        actual_slot = int(base_slot + (state.selected_slot * 1800))
    else:
        actual_slot = state.selected_slot

    telemetry.check_memory()
        
    # 3. ROUTING
    tabs = st.tabs(["🏠 Live Demo", "📖 Why It Works"])
    
    with tabs[0]:
        overview.render(
            traffic_df, 
            topology, 
            fractions, 
            nominal_caps, 
            actual_slot, 
            state.threshold, 
            state.threshold_factor
        )

    with tabs[1]:
        concepts.render()

    # Global Disclaimer
    st.markdown("---")
    st.caption("""
    ⚠️ **Industrial Disclaimer**: Users (`n_users`) are simulated with 10% Gaussian noise. 
    Gains of 73.5% were validated under peak congestion scenarios. 
    In production, real-time RRC counters replace simulated inputs.
    """)

if __name__ == "__main__":
    main()
