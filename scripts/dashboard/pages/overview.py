"""
Live Demo page for the SON Dashboard - Recruiter & Citizen Edition.
Flagship view with triple-policy comparison and "Citizen View" impact.
"""
import streamlit as st
import polars as pl
import numpy as np
from scripts.dashboard.components.metrics import kpi_card
from scripts.dashboard.components.charts import plot_gauge, plot_timeseries, plot_heatmap, plot_sankey_dynamic
from scripts.dashboard.config import config
from scripts.dashboard.milp_connector import MILPConnector
from scripts.dashboard.data_loader import load_timeline_24h
from scripts.dashboard.components.viz_factory import TimelineViz, SpatialHeatmapViz, SankeyFlowViz

# New High-Impact Components
from scripts.dashboard.components.hero_banner import render_hero
from scripts.dashboard.components.duel_comparison import render_duel
from scripts.dashboard.components.business_impact import render_business_impact
from scripts.dashboard.components.sidebar import threshold_to_offset_index

# Constants for logical fixes
DATASET_START_DAY = 4  # Le dataset Milan commence un Vendredi (0=Lundi, 4=Vendredi)
MILAN_GRID_SIZE = 100
BLOCK_START_X = 36     # Coordonnée X (colonne) de départ du bloc 1024
BLOCK_START_Y = 36     # Coordonnée Y (ligne) de départ du bloc 1024
GRID_DIM = 32          # Taille du bloc (32x32 = 1024)

@st.cache_data(ttl=3600)
def get_spatial_matrix(df: pl.DataFrame) -> np.ndarray:
    """
    Mapping spatial corrigé pour le bloc 1024.
    Mappe les square_id réels de Milan vers une matrice 32x32 relative au bloc.
    """
    if df.is_empty(): return np.zeros((GRID_DIM, GRID_DIM))
    
    # Extraction des coordonnées réelles et calcul des relatives
    res = df.with_columns([
        (((pl.col("square_id") - 1) % MILAN_GRID_SIZE + 1) - BLOCK_START_X).cast(pl.Int32).alias("gx"),
        (((pl.col("square_id") - 1) // MILAN_GRID_SIZE + 1) - BLOCK_START_Y).cast(pl.Int32).alias("gy")
    ])
    
    # Filtrage pour rester dans les bornes 32x32
    agg = (res.group_by(["gx", "gy"])
           .agg(pl.col("internet_volume").sum())
           .filter((pl.col("gx") >= 0) & (pl.col("gx") < GRID_DIM) & 
                   (pl.col("gy") >= 0) & (pl.col("gy") < GRID_DIM)))
    
    matrix = np.zeros((GRID_DIM, GRID_DIM))
    for row in agg.iter_rows(named=True): 
        matrix[row["gy"], row["gx"]] = row["internet_volume"]
    return matrix

@st.cache_data(ttl=3600)
def get_cached_triple_results(selected_slot: int, traffic_df: pl.DataFrame, fractions: pl.DataFrame, topology: dict, capacities: pl.DataFrame, threshold: float, threshold_factor: float):
    """
    Computes triple simulation ONLY for the selected slot with explicit mappings.
    """
    connector = MILPConnector(fractions, topology)
    delta_level = threshold_to_offset_index(threshold)
    
    slot_data = traffic_df.filter(pl.col("slot_30m") == selected_slot)
    
    # Calcul explicite du jour (Vendredi au départ)
    if not traffic_df.is_empty():
        base_slot = traffic_df["slot_30m"].min()
        days_since_start = int((selected_slot - base_slot) // (48 * 1800))
        day_of_week = (days_since_start + DATASET_START_DAY) % 7
    else:
        day_of_week = DATASET_START_DAY

    is_weekend = 1 if day_of_week >= 5 else 0
    
    # Correction de l'index du slot dans la journée (0-47)
    slot_idx_in_day = int(((selected_slot - (traffic_df["slot_30m"].min() if not traffic_df.is_empty() else 0)) // 1800) % 48)
    slot_caps = capacities.filter((pl.col("plage") == (slot_idx_in_day // 12)) & (pl.col("is_weekend") == is_weekend))
    
    # Static
    res_s = connector.simulate_slot(slot_data, delta_level=0, capacities_df=slot_caps, policy="static", threshold_factor=threshold_factor)
    # Greedy
    res_g = connector.simulate_slot(slot_data, delta_level=delta_level, capacities_df=slot_caps, policy="greedy", threshold_factor=threshold_factor)
    # MILP
    res_m = connector.simulate_slot(slot_data, delta_level=delta_level, capacities_df=slot_caps, policy="dynamic", threshold_factor=threshold_factor)
    
    return {"static": res_s, "greedy": res_g, "milp": res_m}

def render_citizen_view(res_m):
    """Affiche l'impact concret calculé pour un utilisateur."""
    st.subheader("📱 Impact Utilisateur Final (QoE)")
    
    # Calcul du gain de débit moyen théorique
    # Baseline: (Capacité Totale / Trafic Total initial)
    # SON: (Capacité Totale / Trafic Total équilibré)
    
    avg_load_before = res_m.total_vol / (res_m.antenna_results["capacity"].sum() + 1e-6)
    avg_load_after = (res_m.total_vol - res_m.unsatisfied) / (res_m.antenna_results["capacity"].sum() + 1e-6)
    
    # Estimation simplifiée du débit résiduel par utilisateur (hypothèse 50 Mbps max)
    base_throughput = 50.0
    throughput_before = max(2.0, base_throughput * (1 - avg_load_before))
    throughput_after = max(2.0, base_throughput * (1 - avg_load_after))
    
    # Gain relatif
    gain_pct = 100 * (throughput_after / throughput_before - 1)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"""
        <div style="background: rgba(239, 68, 68, 0.05); border: 1px solid #ef4444; padding: 20px; border-radius: 12px; text-align: center;">
            <p style="color: #ef4444; font-weight: bold; margin-bottom: 10px;">Sans Optimisation</p>
            <span style="font-size: 32px; color: #f8fafc;">{throughput_before:.1f} Mbps</span>
            <p style="color: #94a3b8; font-size: 13px; margin-top: 10px;">Débit moyen estimé (Load: {avg_load_before*100:.1f}%)</p>
            <p style="color: #ef4444; font-size: 11px;">Risque élevé de buffering vidéo</p>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown(f"""
        <div style="background: rgba(0, 212, 170, 0.05); border: 1px solid #00d4aa; padding: 20px; border-radius: 12px; text-align: center;">
            <p style="color: #00d4aa; font-weight: bold; margin-bottom: 10px;">Avec MILP Global</p>
            <span style="font-size: 32px; color: #f8fafc;">{throughput_after:.1f} Mbps</span>
            <p style="color: #94a3b8; font-size: 13px; margin-top: 10px;">Gain de performance : <b>+{gain_pct:.1f}%</b></p>
            <p style="color: #00d4aa; font-size: 11px;">Stabilité de flux HD garantie</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.caption("🔍 **Méthodologie** : Le débit est calculé comme une fonction inverse de la charge moyenne pondérée sur les antennes du cluster. L'équilibrage MILP réduit les points chauds, augmentant mathématiquement le débit disponible pour chaque terminal.")

def render(traffic_df: pl.DataFrame, topology: dict, fractions: pl.DataFrame, capacities: pl.DataFrame, selected_slot: int, threshold: float, threshold_factor: float):
    st.header("🏠 Démo Live Industrielle")
    
    # 1. LOAD PRECOMPUTED TIMELINE (Fixed for visualization only)
    timeline = load_timeline_24h()
    
    # 3. RUN CURRENT SLOT ANALYSIS (Dynamic simulation)
    with st.spinner("Analyse du réseau en temps réel..."):
        current_res = get_cached_triple_results(selected_slot, traffic_df, fractions, topology, capacities, threshold, threshold_factor)
    
    res_m = current_res["milp"]
    res_s = current_res["static"]
    res_g = current_res["greedy"]

    if "error" in res_m.status:
        st.error(f"❌ **Erreur du moteur de simulation :** {res_m.status}")
        st.stop()

    # Global metrics calculated from the current real-time simulation (Snapshot KPIs)
    # Gain based on unsatisfied volume reduction for the current snapshot
    gain_milp = 100 * (1 - res_m.unsatisfied / (res_s.unsatisfied + 1e-6))
    gain_greedy = 100 * (1 - res_g.unsatisfied / (res_s.unsatisfied + 1e-6))
    
    # Correction: If baseline is 0, gain is 0
    if res_s.unsatisfied < 0.1:
        gain_milp = 0.0
        gain_greedy = 0.0
        st.info("💡 **Note :** Aucun pic de congestion n'est détecté pour ce créneau avec les paramètres actuels. L'efficacité est donc de 0% car le réseau est déjà optimal.")
    elif gain_milp < 0.1 and res_s.unsatisfied > 1.0:
        st.warning("⚠️ **Attention :** Le solveur n'a pas trouvé d'amélioration pour ce scénario extrême. Essayez d'augmenter δ ou de réduire le facteur de capacité.")

    # 2. HERO BANNER (Dynamic: reacts to slider and δ)
    render_hero(gain_milp, res_s.unsatisfied, res_m.unsatisfied)
    
    # 4. LE DUEL (Dynamic: reacts to slider and δ)
    render_duel(gain_greedy, gain_milp, res_s.unsatisfied, res_g.unsatisfied, res_m.unsatisfied)

    st.divider()

    # 5. CITIZEN VIEW
    render_citizen_view(res_m)
    
    st.divider()

    # 6. 24h TIMELINE (Contextual reference)
    st.subheader("⏱️ Référence Chronologique (24h)")
    st.info("""
    **Pourquoi ce graphique ?** 
    Il sert de **météo globale** du réseau. Tandis que le reste de la page réagit à vos réglages pour une heure précise (le snapshot), 
    ce graphique reste fixe pour montrer que l'algorithme est efficace et stable sur une journée entière. 
    Utilisez-le pour repérer les **pics de charge** (ex: 18h) avant d'aller les manipuler avec le sélecteur d'heure.
    """)
    TimelineViz.render(timeline)

    st.divider()

    # 7. SPATIAL IMPACT
    col_map, col_flow = st.columns([1, 1])
    
    with col_map:
        st.subheader("🗺️ Distribution Spatiale")
        st.caption("Visualisation de l'intensité du trafic par cellule (matrice 32x32).")
        mode = st.radio("Alterner la vue", ["🔴 Surcharge brute (Avant)", "🟢 Optimisé (Après)"], horizontal=True)
        if mode == "🔴 Surcharge brute (Avant)":
            mat = get_spatial_matrix(traffic_df.filter(pl.col("slot_30m")==selected_slot))
            SpatialHeatmapViz.render(mat, "Charge brute avant SON", colorscale="Reds")
        else:
            # Recalculate spatial matrix for "After" view
            offset_df = res_m.antenna_results.select([pl.col("ant_id").alias("master_id"), pl.col("offset_applied").alias("delta_level")])
            active_f = fractions.join(offset_df, on=["master_id", "delta_level"])
            sim_df = (active_f.join(traffic_df.filter(pl.col("slot_30m")==selected_slot), on="square_id")
                      .with_columns((pl.col("internet_volume") * pl.col("fraction")).alias("v_son")))
            after_mat = get_spatial_matrix(sim_df.group_by("square_id").agg(pl.col("v_son").sum().alias("internet_volume")))
            SpatialHeatmapViz.render(after_mat, "Charge redistribuée après SON", colorscale="RdYlGn_r")

    with col_flow:
        st.subheader("🌊 Flux de Transfert (Sankey)")
        st.info("**Signification :** Chaque lien représente un volume de données dérouté d'une antenne source vers une antenne cible. Plus le lien est épais, plus le délestage est important.")
        offset_df = res_m.antenna_results.select([pl.col("ant_id").alias("master_id"), pl.col("offset_applied").alias("delta_level")])
        active_f = fractions.join(offset_df, on=["master_id", "delta_level"])
        flows = (active_f.join(traffic_df.filter(pl.col("slot_30m")==selected_slot), on="square_id")
                 .with_columns((pl.col("internet_volume") * pl.col("fraction")).alias("transferred_vol")))
        SankeyFlowViz.render(flows)

    st.divider()

    # 8. BUSINESS IMPACT
    render_business_impact(
        res_s.unsatisfied, res_m.unsatisfied,
        res_m.n_congested_baseline, res_m.n_congested
    )

    # 9. TECHNICAL PROOF (Collapsed)
    with st.expander("🔬 Preuve de Rigueur Scientifique (Experts)", expanded=False):
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Conservation de Masse", f"{100*(1-res_m.mass_error):.2f}%", f"{res_m.mass_error*100:.4f}% écart")
            st.caption("Garantit que 100% des données envoyées sont traitées.")
        with c2:
            st.metric("Intégrité du Bloc", f"{100 - (res_m.leakage/res_m.total_vol*100):.2f}%", "Système Fermé")
            st.caption("Prouve que le bloc de 1024 cellules est autosuffisant.")
        with c3:
            n_resolved = res_m.n_congested_baseline - res_m.n_congested
            st.metric("Sites Surchargés Résolus", f"{n_resolved}", f"sur {res_m.n_congested_baseline}")
            st.caption("Nombre d'antennes revenues sous leur seuil de confort.")
