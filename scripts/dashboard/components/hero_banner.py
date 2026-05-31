"""
Hero Banner component — Engineering focused summary of network performance.
"""
import streamlit as st
from scripts.dashboard.config import config

def render_hero(gain_milp: float, total_static: float, total_milp: float):
    """Renders the hero section with key performance indicators."""
    
    st.markdown("""
    <style>
    .hero-container {
        background: linear-gradient(135deg, #0f172a 0%, #161e2e 100%);
        border-radius: 12px;
        padding: 30px;
        text-align: center;
        border: 1px solid rgba(0, 212, 170, 0.2);
        margin-bottom: 25px;
    }
    .hero-big-number {
        font-size: 56px;
        font-weight: 800;
        color: #00d4aa;
        line-height: 1;
        margin: 0;
    }
    .hero-label {
        font-size: 16px;
        color: #94a3b8;
        margin-top: 8px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .hero-tech-note {
        font-size: 13px;
        color: #64748b;
        margin-top: 15px;
        padding: 10px;
        background: rgba(0,0,0,0.2);
        border-radius: 6px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown(f"""
        <div class="hero-container">
            <div class="hero-big-number">{gain_milp:.1f}%</div>
            <div class="hero-label">Efficacité de redistribution</div>
            <div class="hero-tech-note">
                📊 <b>Load Shifting :</b> Réduction relative de la surcharge non satisfaite pour le <b>créneau sélectionné</b>.
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        mo_deroutes = total_static - total_milp
        st.markdown(f"""
        <div class="hero-container">
            <div class="hero-big-number">{mo_deroutes/1e3:.1f}k</div>
            <div class="hero-label">Volume de trafic fluidifié (Mo)</div>
            <div class="hero-tech-note">
                ⚡ <b>Throughput Recovery :</b> Volume de données réalloué vers des cellules disponibles pour éviter le bridage.
            </div>
        </div>
        """, unsafe_allow_html=True)
