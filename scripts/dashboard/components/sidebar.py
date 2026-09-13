"""
WiseNet V2.0 - Sidebar Component with 5 Core Pillars
Controls:
- Time Navigation: 24h Slider (00:00 - 23:30) with Auto-Play / Pause Animation
- Frequency Toggle (F1_1800 LTE, F2_3500 5G NR, ALL Dual-Carrier)
- Advanced Stress-Test Capacity Slider
- Circuit Breaker Live Status Badge
"""
import time
import streamlit as st
from scripts.dashboard.config import config
from scripts.dashboard.state import DemoState
from scripts.dashboard.resilience import milp_cb

def render_sidebar():
    """Renders comprehensive, recruiter & jury ready sidebar in English."""
    state = DemoState.get_instance()
    
    with st.sidebar:
        # Header Branding
        col_logo, col_txt = st.columns([1, 3])
        with col_logo:
            st.image("https://img.icons8.com/fluency/96/satellite.png", width=64)
        with col_txt:
            st.markdown("<h2 style='margin-bottom:0; color:#f8fafc;'>WiseNet V2.0</h2>", unsafe_allow_html=True)
            st.caption("3GPP SON & CAMARA Controller")
            
        st.markdown("---")
        
        # ── 1. CIRCUIT BREAKER RESILIENCE BADGE ──────────────────────
        cb_state = milp_cb.state
        if cb_state == "CLOSED":
            cb_badge = "<span style='background:rgba(0, 212, 170, 0.2); color:#00d4aa; border:1px solid #00d4aa; padding:4px 10px; border-radius:12px; font-weight:bold; font-size:12px;'>🛡️ Circuit Breaker: CLOSED (Nominal)</span>"
        elif cb_state == "HALF-OPEN":
            cb_badge = "<span style='background:rgba(245, 158, 11, 0.2); color:#f59e0b; border:1px solid #f59e0b; padding:4px 10px; border-radius:12px; font-weight:bold; font-size:12px;'>⚠️ Circuit Breaker: HALF-OPEN (Testing)</span>"
        else:
            cb_badge = "<span style='background:rgba(239, 68, 68, 0.2); color:#ef4444; border:1px solid #ef4444; padding:4px 10px; border-radius:12px; font-weight:bold; font-size:12px;'>🚨 Circuit Breaker: OPEN (Fallback)</span>"
        
        st.markdown(cb_badge, unsafe_allow_html=True)
        st.caption("Controller resilience protecting against solver latency spikes")
        
        st.markdown("---")
        
        # ── 2. TEMPORAL SLIDER & AUTO-PLAY (24H = 48 SLOTS) ────────
        st.subheader("⏱️ Temporal Navigation (24h)")
        
        def format_slot(slot_idx):
            h = slot_idx // 2
            m = "00" if slot_idx % 2 == 0 else "30"
            return f"{h:02d}:{m}"

        current_slot = getattr(state, "selected_slot", 26) % 48
        
        selected_slot_idx = st.select_slider(
            "30-min Time Interval",
            options=list(range(48)),
            value=current_slot,
            format_func=format_slot,
            help="Select time instant T to analyze congestion patterns and the MILP balancing response."
        )
        
        # Auto-Play Simulation Feature
        col_play, col_stop = st.columns(2)
        with col_play:
            if st.button("▶️ Auto Play", use_container_width=True):
                st.session_state["is_playing"] = True
        with col_stop:
            if st.button("⏸️ Pause", use_container_width=True):
                st.session_state["is_playing"] = False
                
        # Contextual Traffic Peak Card
        hour = selected_slot_idx // 2
        anecdotes = {
            range(0, 6): ("🌙 Quiet Night Hours", "Minimal background traffic (~350 GB/h). High-capacity F2 carriers can enter sleep mode."),
            range(6, 9): ("🌅 Morning Commute & Wake-Up", "Steep commuter surge. Initial A3 handover offloading triggers."),
            range(9, 13): ("🏢 Business Peak (Porta Nuova)", "Localized commercial core saturation. MILP balances dense enterprise flows."),
            range(13, 15): ("🍽️ Lunch Rush & Peak Demand", "Maximum daily traffic spike (2.62 TB/h). CAMARA QoD safety net active."),
            range(15, 18): ("💼 Sustained Afternoon", "Stable high volume. Zero secondary cascading congestion under MILP."),
            range(18, 21): ("🌆 Evening Commute & Rush Hour", "Residential core and transit hub saturation safely redistributed."),
            range(21, 24): ("🏟️ Leisure & Entertainment", "Heavy video streaming and event traffic.")
        }
        
        c_title, c_desc = "Nominal Traffic", "Balanced Network"
        for r, (t, d) in anecdotes.items():
            if hour in r:
                c_title, c_desc = t, d
                break
                
        st.markdown(f"""
        <div style="background:rgba(15, 23, 42, 0.6); border-left:4px solid #00d4aa; padding:10px; border-radius:6px; margin-top:8px;">
            <strong style="color:#00d4aa; font-size:13px;">{c_title}</strong><br>
            <span style="font-size:12px; color:#94a3b8;">{c_desc}</span>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # ── 3. RADIO LAYER (FREQUENCY TOGGLE) ──────────────────────
        st.subheader("📶 Spectrum Layer (Multi-Carrier)")
        freq_option = st.radio(
            "Carrier Selection",
            options=["ALL", "F1_1800", "F2_3500"],
            format_func=lambda x: {
                "ALL": "🌐 Dual-Carrier (Coverage + Capacity)",
                "F1_1800": "📡 F1: 1.8 GHz (LTE Macro 20MHz)",
                "F2_3500": "🚀 F2: 3.5 GHz (5G NR n78 80MHz)"
            }[x],
            index=0,
            help="Toggle between LTE coverage and 5G capacity to observe vertical offload dynamics."
        )
        
        st.markdown("---")
        
        # ── 4. ADVANCED PARAMETERS & STRESS TEST ─────────────────────
        with st.expander("⚙️ Engineering Controls & Stress Test", expanded=False):
            st.markdown(r"**A3 Handover Trigger Bound ($\delta$ Max):**")
            delta_val = st.slider("Max CIO Offset (dB)", 0.5, 3.0, 2.0, 0.5)
            
            st.markdown("**Network Stress Factor:**")
            stress_val = st.slider("Antenna Residual Capacity", 0.4, 1.2, 0.85, 0.05,
                                  help="Simulates adverse weather, physical degradation, or partial base station outages")
                                  
            st.caption("CAMARA QoD Allocation Budget: 15 sessions / slot")
            
        state.update(
            selected_slot=selected_slot_idx,
            threshold=delta_val,
            threshold_factor=stress_val,
            freq_view=freq_option
        )
        
        # Footer
        st.markdown("---")
        st.caption("WiseNet Flagship Edition | Politecnico di Milano & TIM Data")
        st.caption("GSMA Open Gateway / CAMARA Compliant")
        
    return state
