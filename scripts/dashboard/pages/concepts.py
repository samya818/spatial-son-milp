"""
Pedagogical page explaining core network and optimization concepts.
Dual-layer approach: Simple Metaphors vs. Technical Details.
"""
import streamlit as st

def render():
    st.header("🧠 Comprendre le Système SON")
    st.markdown("""
    Bienvenue dans les coulisses de l'optimisation. Choisissez votre niveau de lecture pour découvrir comment nous fluidifions le réseau de Milan.
    """)

    tab_simple, tab_engineer = st.tabs(["💡 Explication Simple", "🔬 Pour les Ingénieurs"])

    with tab_simple:
        st.subheader("La Métaphore de l'Autoroute (Le Handover)")
        st.markdown("""
        Imaginez une autoroute à deux voies (deux antennes). La voie de gauche est totalement bouchée, tandis que la voie de droite est vide.
        
        Normalement, les conducteurs ne changent de voie que si le GPS leur dit que c'est *vraiment* plus rapide. Notre système agit comme un GPS intelligent : il dit aux conducteurs de la voie bouchée : *"Hé, la voie d'à côté est libre, vous pouvez y aller dès maintenant !"*
        
        En changeant la règle (l'offset $\delta$), nous ouvrons des **bretelles virtuelles**. Les utilisateurs ne disparaissent pas, ils sont juste **mieux répartis** sur le bitume disponible.
        """)
        
        st.info("💡 **Honnêteté scientifique** : Nous ne supprimons pas le trafic, nous utilisons les places vides chez les voisins.")

        st.divider()

        st.subheader("Le Manager de Supermarché (Le MILP)")
        st.markdown("""
        Optimiser 1024 cellules, c'est comme gérer un immense supermarché à l'heure de pointe :
        - **Standard Industrie (Greedy)** : Chaque caissière regarde sa propre file. Si elle est longue, elle essaie d'envoyer ses clients vers la caisse d'à côté sans savoir si celle-ci est aussi débordée. Résultat : on déplace souvent le problème.
        - **Notre approche (MILP Global)** : Un manager survole tout le magasin. Il voit toutes les files d'attente en même temps et prend une décision globale : *"Toi, ouvre ta caisse, toi, dévie 10 clients vers l'allée 4"*.
        
        C'est cette **vision d'ensemble** qui nous permet d'être 73% plus efficaces que les méthodes classiques.
        """)

        st.divider()

        st.subheader("Le Système Fermé (Le Bloc 1024)")
        st.markdown("""
        Pour prouver que notre système marche, nous travaillons sur un bloc compact de 1024 cellules (32x32). C'est comme tester un nouveau système de circulation dans un quartier fermé : on vérifie que chaque voiture qui sort d'une rue entre bien dans une autre, et qu'aucune ne 's'évapore' mystérieusement.
        """)

    with tab_engineer:
        st.subheader("📡 1. Le Mécanisme de Handover (L'Événement A3)")
        st.markdown("""
        Dans un réseau mobile, le passage d'un utilisateur d'une antenne source ($S$) vers une antenne cible ($T$) est régi par l'événement **A3**. 
        Physiquement, le téléphone mesure la puissance du signal (**RSRP**) et déclenche le basculement selon l'inéquation suivante :
        """)
        
        st.latex(r"RSRP_{T} > RSRP_{S} + \delta + Hys")
        
        st.markdown("""
        Où :
        - **$RSRP$** : Reference Signal Received Power (dBm).
        - **$\delta$ (A3 Offset)** : Notre variable de contrôle (CIO - Cell Individual Offset). 
        - **$Hys$** : Hystérésis (évite l'effet 'ping-pong').

        **Stratégie** : En diminuant $\delta$ pour une antenne saturée, nous forçons un délestage précoce vers les cellules voisines.
        """)

        st.divider()

        st.subheader("🤖 2. Le MILP : Optimisation Combinatoire Globale")
        st.markdown("""
        Le **MILP** (*Mixed-Integer Linear Programming*) résout le problème de l'assignation des offsets à l'échelle du cluster.
        
        **Espace de recherche** : Pour $N=201$ antennes et $K=7$ niveaux d'offsets, l'espace est de $7^{201}$ combinaisons. Le MILP utilise l'algorithme *Branch & Cut* pour converger vers l'optimum en quelques secondes.
        """)
        
        st.latex(r"\min \sum_{a \in Cluster} \text{UnsatisfiedDemand}_a")
        st.markdown("Sous contrainte de conservation de flux et de capacité physique :")
        st.latex(r"V_{a}^{final} = V_{a}^{initial} - \sum \text{OutFlow}(a, \delta_a) + \sum \text{InFlow}(v, \delta_{v}) \le C_a")

        st.divider()

        st.subheader("⚖️ 3. Conservation de la Masse")
        st.markdown("""
        Nous validons l'intégrité du modèle en vérifiant que la somme des volumes entrants et sortants est nulle à l'échelle du bloc Milan-1024.
        """)
        st.latex(r"\Delta_{Masse} = \sum V_{initial} - \sum V_{final} \approx 0")

        st.divider()

        st.subheader("📈 4. Prédiction Quantile $q_{80}$")
        st.markdown("""
        L'optimiseur ne travaille pas sur la moyenne, mais sur une borne supérieure de sécurité (Quantile 80) via XGBoost/LightGBM.
        """)
        st.latex(r"L(y, \hat{y}) = \max(\tau(y-\hat{y}), (1-\tau)(\hat{y}-y))")
        st.markdown("""
        Cela garantit que l'optimisation reste robuste même en cas de pic de trafic imprévu.
        """)

    st.markdown("---")
    st.caption("Projet SON - Milan 1024 Cells | Ingénierie Télécom & Optimisation Globale")
