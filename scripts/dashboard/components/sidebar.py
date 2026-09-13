"""
WiseNet V2.0 - Sidebar Component with 5 Core Pillars
Controls:
- Time Navigation: 24h Slider (00:00 - 23:30) with Play/Stop Animation
- Frequency Toggle (F1_1800 LTE, F2_3500 5G NR, ALL Dual-Band)
- Policy Comparison View (Side-by-Side, Overlay, Delta)
- Stress-Test Capacity Slider
- Circuit Breaker Live Status Pill
"""
import time
import streamlit as st
from scripts.dashboard.config import config
from scripts.dashboard.state import DemoState
from scripts.dashboard.resilience import milp_cb

def render_sidebar():
    """Renders comprehensive, recruiter & jury ready sidebar."""
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
        
        # ── 1. CIRCUIT BREAKER RESILIENCE PILL ──────────────────────
        cb_state = milp_cb.state
        if cb_state == "CLOSED":
            cb_badge = "<span style='background:rgba(0, 212, 170, 0.2); color:#00d4aa; border:1px solid #00d4aa; padding:4px 10px; border-radius:12px; font-weight:bold; font-size:12px;'>🛡️ Circuit Breaker: CLOSED (Nominal)</span>"
        elif cb_state == "HALF-OPEN":
            cb_badge = "<span style='background:rgba(245, 158, 11, 0.2); color:#f59e0b; border:1px solid #f59e0b; padding:4px 10px; border-radius:12px; font-weight:bold; font-size:12px;'>⚠️ Circuit Breaker: HALF-OPEN (Testing)</span>"
        else:
            cb_badge = "<span style='background:rgba(239, 68, 68, 0.2); color:#ef4444; border:1px solid #ef4444; padding:4px 10px; border-radius:12px; font-weight:bold; font-size:12px;'>🚨 Circuit Breaker: OPEN (Fallback)</span>"
        
        st.markdown(cb_badge, unsafe_allow_html=True)
        st.caption("Résilience du contrôleur face aux instabilités du solveur")
        
        st.markdown("---")
        
        # ── 2. TEMPORAL SLIDER & AUTO-PLAY (24H = 48 SLOTS) ────────
        st.subheader("⏱️ Navigation Temporelle (24h)")
        
        def format_slot(slot_idx):
            h = slot_idx // 2
            m = "00" if slot_idx % 2 == 0 else "30"
            return f"{h:02d}:{m}"

        current_slot = getattr(state, "selected_slot", 26) % 48
        
        selected_slot_idx = st.select_slider(
            "Créneau 30 min",
            options=list(range(48)),
            value=current_slot,
            format_func=format_slot,
            help="Sélectionnez un instant T pour analyser la saturation et la réponse MILP."
        )
        
        # Auto-Play Simulation Feature
        col_play, col_stop = st.columns(2)
        with col_play:
            if st.button("▶️ Lecture Auto", use_container_width=True):
                st.session_state["is_playing"] = True
        with col_stop:
            if st.button("⏸️ Pause", use_container_width=True):
                st.session_state["is_playing"] = False
                
        # Contextual Traffic Peak Card
        hour = selected_slot_idx // 2
        anecdotes = {
            range(0, 6): ("🌙 Nuit Calme", "Charge minime (~350 Go/h). Les porteuses F2 peuvent être mises en veille."),
            range(6, 9): ("🌅 Réveil Milanais & Navetteurs", "Forte croissance pendulaire. Premiers transferts A3 actifs."),
            range(9, 13): ("🏢 Business Peak (Porta Nuova)", "Saturations localisées. Le MILP équilibre les flux bureautiques."),
            range(13, 15): ("🍽️ Pause Déjeuner & Pic Maximal", "Pic absolu du dataset (2.62 To/h). Déclenchement du filet QoD."),
            range(15, 18): ("💼 Après-midi Soutenu", "Volume élevé stable. Aucun débordement secondaire grâce au MILP."),
            range(18, 21): ("🌆 Soirée & Heure de Pointe", "Saturation résidentielle et grands axes de transport."),
            range(21, 24): ("🏟️ Détente & Événements", "Forte consommation streaming / vidéo.")
        }
        
        c_title, c_desc = "Trafic Nominal", "Réseau équilibré"
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
        
        # ── 3. COUCHE RADIO (TOGGLE FRÉQUENCE) ──────────────────────
        st.subheader("📶 Couche Spectrale (Multi-Porteuses)")
        freq_option = st.radio(
            "Sélection de la fréquence",
            options=["F1_1800", "F2_3500", "ALL"],
            format_func=lambda x: {
                "F1_1800": "📡 F1 : 1.8 GHz (LTE Macro 20MHz)",
                "F2_3500": "🚀 F2 : 3.5 GHz (5G NR n78 80MHz)",
                "ALL": "🌐 Dual-Carrier (Couverture + Capacité)"
            }[x],
            index=2,
            help="Basculez entre LTE et 5G pour visualiser les transferts verticaux."
        )
        
        st.markdown("---")
        
        # ── 4. PARAMÈTRES AVANCÉS & STRESS TEST ─────────────────────
        with st.expander("⚙️ Paramètres Ingénieur & Stress Test", expanded=False):
            st.markdown("**Seuil d'activation A3 ($\delta$ Max) :**")
            delta_val = st.slider("Offset CIO max (dB)", 0.5, 3.0, 2.0, 0.5)
            
            st.markdown("**Facteur de Stress Réseau :**")
            stress_val = st.slider("Capacité résiduelle des antennes", 0.4, 1.2, 0.85, 0.05,
                                  help="Simule des pannes partielles ou une météo dégradée")
                                  
            st.caption("Plafond budgétaire CAMARA QoD : 15 sessions / slot")
            
        state.update(
            selected_slot=selected_slot_idx,
            threshold=delta_val,
            threshold_factor=stress_val,
            freq_view=freq_option
        )
        
        # Footer
        st.markdown("---")
        st.caption("WiseNet Final Edition | Politecnico di Milano & TIM Data")
        st.caption("GSMA Open Gateway / CAMARA Compliant")
        
    return state
