"""
Duel Comparison — Technical comparison between Greedy and MILP optimization.
"""
import streamlit as st
from scripts.dashboard.config import config

def render_duel(gain_greedy: float, gain_milp: float, total_static: float, 
                total_greedy: float, total_milp: float):
    """Renders a technical comparison between local heuristic and global optimization."""
    
    st.markdown("""
    <style>
    .duel-container {
        background: #0f172a;
        border-radius: 12px;
        padding: 20px;
        border: 1px solid #334155;
        height: 100%;
    }
    .duel-bar-bg {
        background: #1e293b;
        height: 24px;
        border-radius: 12px;
        margin-top: 10px;
        overflow: hidden;
    }
    .duel-bar {
        height: 100%;
        transition: width 1s ease-out;
    }
    .duel-greedy { background: #4b8ef5; }
    .duel-milp { background: #00d4aa; }
    </style>
    """, unsafe_allow_html=True)
    
    st.subheader("⚖️ Analyse Comparative des Algorithmes")
    
    col1, col2 = st.columns(2)
    
    with col1:
        greedy_pct = 100 * (1 - total_greedy / (total_static + 1e-6))
        st.markdown(f"""
        <div class="duel-container">
            <h5 style="margin-top:0; color:#4b8ef5;">Heuristique Greedy (D-SON)</h5>
            <div style="display:flex; justify-content:space-between; margin-bottom:5px;">
                <span style="color:#94a3b8; font-size:14px;">Gain vs Baseline</span>
                <span style="color:#4b8ef5; font-weight:bold;">{greedy_pct:.1f}%</span>
            </div>
            <div class="duel-bar-bg">
                <div class="duel-bar duel-greedy" style="width:{greedy_pct}%;"></div>
            </div>
            <p style="color:#64748b; font-size:12px; margin-top:10px;">
                Optimisation locale par site. Chaque antenne réagit à sa propre congestion sans coordination, 
                ce qui peut entraîner des effets de 'ping-pong' ou saturer les voisins immédiats.
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="duel-container" style="border-color:#00d4aa;">
            <h5 style="margin-top:0; color:#00d4aa;">MILP Global (Coordinateur)</h5>
            <div style="display:flex; justify-content:space-between; margin-bottom:5px;">
                <span style="color:#94a3b8; font-size:14px;">Gain vs Baseline</span>
                <span style="color:#00d4aa; font-weight:bold;">{gain_milp:.1f}%</span>
            </div>
            <div class="duel-bar-bg">
                <div class="duel-bar duel-milp" style="width:{gain_milp}%;"></div>
            </div>
            <p style="color:#64748b; font-size:12px; margin-top:10px;">
                Résolution par Programmation Linéaire. Minimise l'excès de trafic à l'échelle du cluster. 
                Gain supplémentaire de <b>{gain_milp - greedy_pct:.1f}%</b> grâce à la coordination multi-sites.
            </p>
        </div>
        """, unsafe_allow_html=True)
