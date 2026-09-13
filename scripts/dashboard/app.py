"""
Main entry point for the WiseNet V2.0 Flagship Dashboard.
Features:
- Hexagonal 3GPP Interactive Network Map (Pydeck)
- Dual-Carrier F1 (1.8GHz LTE) & F2 (3.5GHz 5G NR) Layer Toggle
- Before/After MILP Optimization comparison (73.5% peak gain)
- Decision Receipts & Greedy secondary congestion benchmark (ADR-002)
- Live CAMARA Device Location & QoD Safety Net Triggering
- Circuit Breaker Resilience State
"""
import sys
import time
from pathlib import Path
import streamlit as st
import polars as pl
import logging

# Add project root to sys.path
root_path = str(Path(__file__).parents[2])
if root_path not in sys.path:
    sys.path.append(root_path)

from scripts.dashboard.config import config
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
        page_title="WiseNet V2.0 | 3GPP SON & CAMARA Controller",
        page_icon="🛰️",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Global CSS injection for dark telecom theme
    st.markdown(f"""
    <style>
        .main {{background-color: {config.BACKGROUND_COLOR};}}
        h1, h2, h3, h4 {{color: #f8fafc !important; font-family: 'Inter', sans-serif;}}
        .stMetric label {{color: #94a3b8 !important; font-size: 13px !important;}}
        .stMetric div[data-testid="stMetricValue"] {{color: #f8fafc !important; font-weight: 700 !important;}}
        div[data-testid="stExpander"] {{border: 1px solid #334155; border-radius: 8px; background: rgba(15, 23, 42, 0.4);}}
        .badge-green {{background-color: #00d4aa; color: #000; padding: 3px 8px; border-radius: 12px; font-size: 11px; font-weight: bold;}}
    </style>
    """, unsafe_allow_html=True)

    # 1. SIDEBAR & CONTROLS
    state = render_sidebar()

    # 2. DATA LOADING (Cached)
    with st.spinner("🛰️ Ingestion des Actifs Réseau (Milan 1024 / 756 cellules)..."):
        traffic_df = load_traffic_data()
        topology = load_topology()
        fractions = load_fractions()
        nominal_caps = load_nominal_capacities()

    actual_slot = state.selected_slot

    # 3. ROUTING
    tabs = st.tabs(["🛰️ Contrôleur Live (3GPP Hex Map & CAMARA)", "📖 Architecture Scientifique & Justification"])
    
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
    ⚠️ **Note d'Intégrité Scientifique** : Dataset Telecom Italia Milan (Novembre-Décembre 2013). 
    Topologie 3GPP déterministe avec ISD 750m conforme aux spécifications Ericsson AIR et licences TIM Italy.
    Filet de sécurité CAMARA validé sur la sandbox officielle GSMA Open Gateway / Vodafone.
    """)

    # Auto-play tick logic
    if st.session_state.get("is_playing", False):
        time.sleep(1.0)
        next_slot = (state.selected_slot + 1) % 48
        state.update(selected_slot=next_slot)
        st.rerun()

if __name__ == "__main__":
    main()
