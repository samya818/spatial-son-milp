"""
Sidebar control component for the SON Dashboard - Recruiter Edition.
Focused on interactive time navigation and technical parameters.
"""
import streamlit as st
from scripts.dashboard.config import config
from scripts.dashboard.state import DemoState

def threshold_to_offset_index(threshold: float) -> int:
    """
    Mapping explicite du seuil vers l'index d'offset (0-6).
    {0.5: 0, 0.6: 1, ..., 1.5: 6} -> Correspond à {0.0, 0.5, ..., 3.0} dB
    """
    return int(round((threshold - 0.5) * 6))

def render_sidebar():
    """Renders global dashboard controls with time slider and technical parameters."""
    state = DemoState.get_instance()
    
    with st.sidebar:
        st.image("https://img.icons8.com/fluency/150/satellite.png", width=80)
        st.title("🛰️ SON Optimizer")
        st.caption("v7.1 | Engineering Edition")
        
        st.divider()
        st.subheader("🕒 Sélection du Snapshot")
        st.info("""
        **Données :** Vendredi 1er Nov. 2013
        **Dualité d'Analyse :**
        - **Graphe 24h** : Vue d'ensemble de la performance.
        - **Sélecteur d'Heure** : Zoom opérationnel à l'instant T.
        """)
        st.caption("Sélectionnez un intervalle pour tester l'impact de vos paramètres sur un scénario précis.")
        
        # 1. Slider Temps (00:00 à 23:30)
        current_slot = state.selected_slot % 48
        
        def format_slot(slot_idx):
            h = slot_idx // 2
            m = "00" if slot_idx % 2 == 0 else "30"
            return f"{h:02d}:{m}"

        selected_slot_idx = st.select_slider(
            "Heure de la journée",
            options=list(range(48)),
            value=current_slot,
            format_func=format_slot,
            help="Analyse ponctuelle du réseau."
        )
        
        # Marqueurs visuels
        st.markdown("""
        <div style="display: flex; justify-content: space-between; font-size: 14px; margin-top: -10px; color: #94a3b8;">
            <span>🌅 07h</span>
            <span>🏢 09h</span>
            <span>🌆 18h</span>
            <span>🏟️ 20h</span>
        </div>
        """, unsafe_allow_html=True)
        
        # 2. Carte Contextuelle
        st.markdown("---")
        hour = selected_slot_idx // 2
        
        anecdotes = {
            range(0, 6): ("🌙 Nuit Calme", "Trafic minimal, ressources sous-utilisées."),
            range(6, 9): ("🌅 Réveil Milanais", "Montée progressive de la charge (commuters)."),
            range(9, 12): ("🏢 Business Peak", "Forte demande data (Quartiers d'affaires)."),
            range(12, 14): ("🍽️ Pause Déjeuner", "Pics localisés (Zones commerciales/Navigli)."),
            range(14, 17): ("💼 Après-midi Productif", "Trafic soutenu et stable."),
            range(17, 20): ("🌆 Heure de Pointe", "Saturation critique du bloc 1024."),
            range(20, 22): ("🏟️ Event Peak", "Concentrations massives (San Siro/Events)."),
            range(22, 24): ("🌙 Soirée Résidentielle", "Déplacement de la charge vers le domestique.")
        }
        
        context_title, context_text = "Détente", "Trafic nominal."
        for r, (title, text) in anecdotes.items():
            if hour in r:
                context_title, context_text = title, text
                break
                
        st.markdown(f"""
        <div style="background: rgba(0, 212, 170, 0.1); border-left: 4px solid #00d4aa; padding: 15px; border-radius: 5px;">
            <strong style="color: #00d4aa;">{context_title}</strong><br>
            <span style="font-size: 13px; color: #cbd5e1;">{context_text}</span>
        </div>
        """, unsafe_allow_html=True)
        
        st.divider()
        
        # 4. Expert Mode
        expert_mode = st.toggle("⚙️ Paramètres de Contrôle (Ingénieur)", value=state.expert_mode)
        
        if expert_mode:
            st.subheader("🛠️ Variables de Décision")
            
            st.markdown("""
            **δ (Intensité de délestage) :**
            Définit l'amplitude maximale de l'offset de puissance (en dB). 
            Plus δ est élevé, plus l'antenne peut 'pousser' ses utilisateurs vers les voisins.
            """)
            threshold = st.slider("Seuil δ (dB Offset Max)", 0.5, 1.5, state.threshold, 0.1)
            
            st.markdown("""
            **Scaling Capacité :**
            Simule une réduction de la capacité physique (ex: panne ou interférences). 
            Utile pour tester la résilience du SON sous stress extrême.
            """)
            factor = st.slider("Facteur de Capacité (Stress Test)", 0.3, 1.5, state.threshold_factor, 0.1)
            
            st.caption(f"Index MILP: {threshold_to_offset_index(threshold)} (δ: {threshold:.1f} dB)")
        else:
            threshold = 1.0
            if hour in [18, 19, 20, 21]: factor = 0.65
            elif hour in [8, 9, 10, 11]: factor = 0.8
            else: factor = 1.0

        # Update State
        state.update(
            selected_slot=selected_slot_idx,
            threshold=threshold,
            threshold_factor=factor,
            expert_mode=expert_mode
        )
        
        st.divider()
        st.caption("👥 Loukili Samya & Kenza El Khaniri")
        st.caption("📍 Milan Dense Block (1024 cells)")
        
        return state
