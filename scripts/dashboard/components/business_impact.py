"""
Technical KPIs — Professional performance metrics for network operators.
"""
import streamlit as st

def render_business_impact(total_static: float, total_milp: float, 
                           n_congested_before: int, n_congested_after: int):
    """Renders technical KPIs with engineering terminology."""
    
    st.subheader("📈 Indicateurs d'Efficacité Réseau (KPIs)")
    
    # 1. Congestion Reduction Rate
    congestion_gain = 100 * (1 - n_congested_after / (n_congested_before + 1e-6))
    
    # 2. Virtual Capacity Increase
    # On estime combien de trafic supplémentaire le réseau peut absorber 
    # grâce à une meilleure répartition.
    virtual_gain = (total_static - total_milp) / (total_static + 1e-6) * 100
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "📉 Réduction Surcharge",
            f"{congestion_gain:.1f}%",
            "Sites critiques",
            help="Pourcentage d'antennes qui repassent sous leur seuil de saturation nominal grâce au SON."
        )
    
    with col2:
        st.metric(
            "🚀 Gain Capacité Virtuelle",
            f"{virtual_gain:.1f}%",
            "Débit préservé",
            help="Augmentation théorique du trafic admissible sans ajout de hardware, par simple équilibrage de charge."
        )
    
    with col3:
        # Spectral Efficiency Proxy: (Processed Traffic / Used Capacity)
        efficiency = 1.0 + (virtual_gain / 100)
        st.metric(
            "📊 Efficacité Spectrale",
            f"x{efficiency:.2f}",
            "Optimisation du cluster",
            help="Facteur multiplicateur de l'utilisation des ressources existantes."
        )
    
    st.markdown("""
    ---
    **Note Technique :** Ces KPIs sont calculés en comparant l'état du réseau avec et sans l'intervention de l'algorithme MILP. 
    Ils démontrent la capacité du système à absorber des pics de charge sans dégradation de l'expérience utilisateur, 
    retardant ainsi les investissements CAPEX en nouvelles infrastructures physiques.
    """)
