"""
WiseNet V2.0 - Concepts & Scientific Transparency Page
Explains the 3GPP SON A3 event, Lucas critique immunity, MILP vs Greedy, and CAMARA QoD.
"""
import streamlit as st

def render():
    st.header("🧠 Architecture Scientifique & Explicabilité WiseNet V2.0")
    st.caption("Dossier Technique pour Jury & Recruteurs Télécom")
    
    t_son, t_camara, t_lucas, t_jury = st.tabs([
        "📡 1. Mécanisme 3GPP A3 & Dual-Carrier",
        "🌐 2. CAMARA & GSMA Open Gateway",
        "⚖️ 3. Immunité à la Critique de Lucas",
        "🎯 4. Guide des Arguments Clés (Jury)"
    ])
    
    with t_son:
        st.subheader("Le Déclenchement A3 et l'Offset CIO")
        st.markdown("""
        Dans les réseaux mobiles 4G/5G, le changement d'antenne (handover) d'un équipement mobile est régi par **l'événement A3** (3GPP TS 38.331) :
        """)
        st.latex(r"RSRP_{Cible} + CIO_{Cible} > RSRP_{Serveuse} + CIO_{Serveuse} + Hyst")
        st.markdown("""
        - **$** : Reference Signal Received Power (Puissance du signal radio en dBm)
        - **$ (Cell Individual Offset / $\delta$)** : L'offset de puissance manipulé par le contrôleur SON (de 0 à 3.0 dB).
        - **$** : Hystérésis pour éviter le phénomène d'oscillation 'ping-pong' entre cellules.
        
        #### Dual-Carrier : Déplacement Horizontal vs. Vertical
        1. **Transfert Horizontal (Intra-Fréquence)** : Déplacement de la charge vers les secteurs physiques adjacents (azimut 0°, 120°, 240°).
        2. **Transfert Vertical (Inter-Fréquence)** : Déchargement de la porteuse macro **F1 (1.8 GHz LTE)** vers la porteuse capacitaire **F2 (3.5 GHz 5G NR)** sur le même site radio, soulageant instantanément la bande de couverture.
        """)
        
    with t_camara:
        st.subheader("Intégration Standard GSMA Open Gateway / CAMARA")
        st.markdown("""
        WiseNet est le premier contrôleur SON à intégrer la chaîne complète de 3 APIs de l'initiative GSMA :
        
        1. **Vodafone Analytics Footfall (QK17 / Population Density)** :
           Mesure exogène du nombre de visiteurs par maille géographique, servant à calibrer la demande réelle sans dépendre des biais de reporting des antennes.
        2. **CAMARA Device Location Verification (/location-verification/v1/verify)** :
           Vérifie physiquement par géolocalisation réseau si les véhicules d'urgence (SAMU, Police) sont sous l'emprise géographique d'une cellule saturée.
        3. **CAMARA Quality on Demand (/quality-on-demand/v1/sessions)** :
           Alloue chirurgicalement une tranche prioritaire 5QI=1 (QOS_E) ou 5QI=3 (QOS_L) pour garantir la survie des flux vitaux lors des saturations résiduelles.
        """)
        
    with t_lucas:
        st.subheader("Immunité à la Critique de Lucas")
        st.markdown("""
        Dans beaucoup d'articles académiques de SON, les chercheurs commettent l'erreur d'ajuster les prédictions en fonction des décisions de délestage passées :
        """)
        st.latex(r"\frac{\partial \text{Demande}}{\partial \delta} = 0")
        st.markdown("""
        WiseNet garantit l'immunité à la critique de Lucas : **la demande des utilisateurs sur une zone géographique est exogène et indépendante des réglages d'antennes**.
        Le délestage réoriente les connexions mais ne crée ni ne détruit magiquement des mégaoctets d'utilisateurs.
        """)
        
    with t_jury:
        st.subheader("Fiche Récapitulative des Arguments Clés")
        st.markdown("""
        | Critère | Heuristique Gloutonne (Greedy) | WiseNet (MILP Global + CAMARA) |
        |---|---|---|
        | **Vision du Réseau** | Locale (1 cellule isolée) | Globale (126 sites / 756 cellules) |
        | **Congestion Secondaire** | Fréquente (sature les voisins) | Strictement prévenue par contraintes MILP |
        | **Temps de Calcul** | < 0.1 s | 0.58 s (Compatible boucle 30 min) |
        | **Gain d'Absorption** | ~10 - 14% | **+16.8% à +25.3% (jusqu'à 73.5% en pic)** |
        | **Protection des Urgences** | Aucune (Best-effort) | Filet de sécurité chirurgical QoD CAMARA |
        | **Tolérance aux Pannes** | Non instrumentée | Circuit Breaker intégré (CLOSED/HALF/OPEN) |
        """)
