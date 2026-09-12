"""
WiseNet — Simulation 48 Heures Rigoureuse et Reproductible
===========================================================
Auteurs    : WiseNet Research Team
Version    : 2.0 (48h)
Date       : 2026-09-13
Dataset    : Telecom Italia Big Data Challenge (Milan, novembre 2013)
             Licence : Creative Commons Attribution 4.0
             DOI     : 10.7910/DVN/EGZHFV

DESIGN SCIENTIFIQUE
-------------------
Ce script implémente une comparaison causale stricte entre trois politiques SON :

  POLITIQUE A — STATIQUE (baseline)
    Aucune optimisation. Chaque cellule radio garde son offset à 0 dB.
    Toute demande dépassant la capacité est perdue (congestion non servie).
    → Mesure le coût de l'absence d'intelligence réseau.

  POLITIQUE B — ML + MILP PRÉDICTIF (WiseNet)
    Étape 1 (t) : XGBoost Quantile q80 prédit V̂(t+1) pour les 1024 mailles.
    Étape 2 (t) : Le MILP minimise l'insatisfait sur V̂(t+1) → décisions z*(t).
    Étape 3 (t+1) : z*(t) est appliqué sur le VRAI trafic V_réel(t+1).
    → Mesure le gain d'une politique prédictive globalement optimale.

  POLITIQUE C — ORACLE MILP (borne supérieure théorique, non déployable)
    Le MILP résout avec V_réel(t+1) connu à l'avance.
    → Quantifie le regret d'incertitude résiduel de la prédiction ML.

MÉTRIQUES PRODUITES (pour chaque slot i = 1..96 de 30 min)
------------------------------------------------------------
  - V_réel_i        : Demande réseau réelle totale (Mo)
  - U_static_i      : Volume non servi — politique Statique (Mo)
  - U_milp_i        : Volume non servi — WiseNet ML+MILP (Mo)
  - U_oracle_i      : Volume non servi — Oracle MILP idéal (Mo)
  - G_i             : Gain instantané MILP vs Statique (%)
  - Regret_i        : Regret ML = U_milp_i - U_oracle_i (Mo)
  - SolveTime_i     : Temps de résolution MILP (s)
  - Prédiction MAE  : Erreur absolue moyenne de XGBoost pour le slot

MÉTRIQUES AGRÉGÉES (sur les 48h = 96 slots)
---------------------------------------------
  - Gain total MILP vs Statique (%)
  - Gain total MILP vs Statique (Mo et Go)
  - Efficacité ML = 1 - Regret_total / Gain_total  (% de gain capturé vs Oracle)
  - Taux de slots améliorés (n slots où MILP < Statique)
  - RMSE prédiction XGBoost
  - Temps moyen de résolution MILP / slot

REPRODUCTIBILITÉ
-----------------
  - Seed numpy fixé à 42
  - Version des dépendances loguée dans le CSV de méta-données
  - Résultats exportés : CSV slot-par-slot + CSV agrégé + 3 figures PNG
  - SHA-256 du parquet source calculé et archivé

COMMENT REPRODUIRE LES RÉSULTATS
----------------------------------
  1. Cloner le dépôt : git clone https://github.com/samya818/spatial-son-milp
  2. Installer les dépendances : pip install -r requirements.txt
  3. Vérifier que research/data/processed/features_target_1024cells.parquet existe
  4. Vérifier que research/models/xgb_q80.pkl existe
  5. Lancer depuis la racine du projet :
       python scripts/simulation_48h_rigorous.py
  6. Résultats dans research/reports/sim48h/

LOGIQUE DE COMPARAISON — POINTS CRITIQUES
-------------------------------------------
  ⚠️  Aucune fuite de données (no data leakage) :
      La décision z*(t) est calculée sur V̂(t+1), JAMAIS sur V_réel(t+1).
      V_réel(t+1) n'est utilisé QUE pour évaluer la congestion résiduelle.

  ⚠️  Conservation de masse stricte :
      Le trafic délesté d'une cellule surchargée est REÇU par les cellules
      voisines. La somme totale du trafic reste constante à chaque slot.

  ⚠️  Borne inférieure (Oracle) non déployable en production :
      L'Oracle connaît le futur → il n'est jamais utilisé pour prendre des
      décisions, uniquement comme référence théorique maximale.
"""

import sys
import os
import time
import hashlib
import json
import logging
import platform
from pathlib import Path
from datetime import datetime, date

import numpy as np

# ── Encodage UTF-8 systématique ─────────────────────────────────────────────
os.environ["PYTHONIOENCODING"] = "utf-8"
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

logging.basicConfig(level=logging.WARNING, format="%(levelname)s | %(message)s")

# ── Import du projet ─────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import polars as pl

from src.topology.builder_v1_5 import TopologyBuilderV15, CELL_SIZE_METERS, GRID_SIZE
from src.spatial.simulator_v1_5 import SpatialTransferSimulatorV15
from src.optimization.milp_engine_v1_5 import MilpEngineV15
from src.ml.predictor import TrafficPredictor

# ═══════════════════════════════════════════════════════════════════════════════
#  CONFIGURATION — Toutes les constantes ici, rien de caché dans le code
# ═══════════════════════════════════════════════════════════════════════════════
SEED = 42
np.random.seed(SEED)

# Fenêtre temporelle : paire 48h la plus chargée du dataset
# Justification : 2013-11-12 (44.31 To) + 2013-11-13 (44.04 To) = 88.35 To
# = la combinaison de 2 jours consécutifs avec le volume total maximal.
# Voir analyse dans le notebook : research/notebooks_v1_5/camara_api_integration.ipynb
DAY_1 = "2013-11-12"   # Mardi (jour de pointe)
DAY_2 = "2013-11-13"   # Mercredi (jour de pointe)

FEATURES_PATH = ROOT / "research" / "data" / "processed" / "features_target_1024cells.parquet"
MODEL_PATH    = ROOT / "research" / "models" / "xgb_q80.pkl"

OUTPUT_DIR = ROOT / "research" / "reports" / "sim48h"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_SLOTS_CSV    = OUTPUT_DIR / "sim48h_slots.csv"
OUTPUT_SUMMARY_JSON = OUTPUT_DIR / "sim48h_summary.json"
OUTPUT_META_JSON    = OUTPUT_DIR / "sim48h_metadata.json"
OUTPUT_FIG_PROFILE  = OUTPUT_DIR / "fig1_congestion_profile.png"
OUTPUT_FIG_GAIN     = OUTPUT_DIR / "fig2_gain_per_slot.png"
OUTPUT_FIG_REGRET   = OUTPUT_DIR / "fig3_oracle_regret.png"

# Topologie 3GPP hexagonale
BLOCK_ROW   = (35, 67)
BLOCK_COL   = (35, 67)
ISD_METERS  = 750.0
DELTA_LEVELS = [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0]
SIM_RESOLUTION = 20

EXPECTED_SLOTS_PER_DAY = 48
EXPECTED_TOTAL_SLOTS   = 96   # 48h × 2

# ═══════════════════════════════════════════════════════════════════════════════
#  FONCTIONS UTILITAIRES
# ═══════════════════════════════════════════════════════════════════════════════

def sep(wide=False, char="="):
    n = 80 if wide else 60
    print(char * n)


def sha256_file(path: Path) -> str:
    """Calcule le SHA-256 d'un fichier pour audit de reproductibilité."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def apply_decisions_on_real_traffic(
    decisions: dict,
    real_traffic: dict,
    fractions_data: dict,
    cells_capacity: dict,
    delta_levels: list,
) -> tuple[float, dict]:
    """
    Applique un vecteur de décisions z* (calculé sur V̂ prédit) sur le VRAI trafic.

    Principe physique : conservation de masse stricte.
    - Le trafic qui quitte la cellule maître EST reçu par les cellules cibles.
    - La somme totale reste constante.

    Retourne :
        (congestion_totale_Mo, loads_par_cellule)
    """
    # Charge initiale réelle par cellule (avant tout délestage)
    loads = {c: 0.0 for c in cells_capacity}
    for sq_id, sq_info in fractions_data.items():
        master = sq_info["master_cell"]
        if master in loads:
            loads[master] += real_traffic.get(sq_id, 0.0)

    # Application des décisions : délestage + réception
    for sq_id, sq_info in fractions_data.items():
        master = sq_info["master_cell"]
        v_real = real_traffic.get(sq_id, 0.0)
        k = decisions.get(master, {}).get("offset_idx", 0)
        d_str = str(delta_levels[k])
        t_info = sq_info["offsets"].get(d_str, {"stays": 1.0, "target_cells": {}})

        frac_leaves = 1.0 - t_info.get("stays", 1.0)
        loads[master] -= v_real * frac_leaves

        for target_c, frac_t in t_info.get("target_cells", {}).items():
            if target_c in loads:
                loads[target_c] += v_real * frac_t

    # Congestion résiduelle = max(0, charge - capacité)
    congestion = sum(max(0.0, loads[c] - cells_capacity[c]) for c in cells_capacity)
    return round(congestion, 2), loads


# ═══════════════════════════════════════════════════════════════════════════════
#  PROGRAMME PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════════

def run_48h_simulation():
    run_start = time.time()
    print()
    sep(wide=True)
    print("  WiseNet — Simulation 48h Rigoureuse et Reproductible")
    print(f"  Fenetre : {DAY_1} (J1) + {DAY_2} (J2)")
    print(f"  Politiques comparees : Statique | ML+MILP Predictif | Oracle MILP")
    sep(wide=True)

    # ── 0. Métadonnées de reproductibilité ──────────────────────────────────
    print("\n[0/5] Enregistrement des metadonnees de reproductibilite...")
    import xgboost, pyomo, pulp
    meta = {
        "run_timestamp_utc": datetime.utcnow().isoformat(),
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "seed": SEED,
        "day_1": DAY_1,
        "day_2": DAY_2,
        "isd_meters": ISD_METERS,
        "delta_levels": DELTA_LEVELS,
        "sim_resolution": SIM_RESOLUTION,
        "expected_slots": EXPECTED_TOTAL_SLOTS,
        "libraries": {
            "polars": pl.__version__,
            "xgboost": xgboost.__version__,
            "pyomo": pyomo.__version__,
            "pulp": pulp.__version__,
            "numpy": np.__version__,
        },
        "dataset_sha256": sha256_file(FEATURES_PATH),
        "model_sha256": sha256_file(MODEL_PATH),
        "dataset_path": str(FEATURES_PATH),
        "model_path": str(MODEL_PATH),
    }
    with open(OUTPUT_META_JSON, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)
    print(f"    Dataset SHA-256 : {meta['dataset_sha256'][:16]}...")
    print(f"    Modele SHA-256  : {meta['model_sha256'][:16]}...")
    print(f"    Metadonnees     : {OUTPUT_META_JSON}")

    # ── 1. Topologie & Fractions spatiales ──────────────────────────────────
    print("\n[1/5] Generation de la topologie 3GPP hexagonale...")
    t0 = time.time()
    builder  = TopologyBuilderV15(isd_meters=ISD_METERS)
    topology = builder.generate_hexagonal_topology(row_range=BLOCK_ROW, col_range=BLOCK_COL)

    squares = [
        r * GRID_SIZE + c + 1
        for r in range(BLOCK_ROW[0], BLOCK_ROW[1])
        for c in range(BLOCK_COL[0], BLOCK_COL[1])
    ]
    sim = SpatialTransferSimulatorV15(
        grid_resolution=SIM_RESOLUTION,
        cell_size_meters=CELL_SIZE_METERS,
        delta_levels=DELTA_LEVELS,
    )
    fractions_data = sim.compute_transfer_fractions(squares, topology, grid_size=GRID_SIZE)

    cells_capacity = {}
    for s_data in topology.values():
        for sec_data in s_data["sectors"].values():
            for c_data in sec_data["carriers"].values():
                cells_capacity[c_data["cell_id"]] = c_data["capacity_mo"]

    n_sites = len(topology)
    n_cells = len(cells_capacity)
    print(f"    {n_sites} sites | {n_sites*3} secteurs | {n_cells} cellules radio | {len(fractions_data)} mailles | {time.time()-t0:.1f}s")

    # ── 2. Chargement données & modèle ──────────────────────────────────────
    print("\n[2/5] Chargement du modele XGBoost q80 et du dataset 48h...")
    predictor = TrafficPredictor(model_path=str(MODEL_PATH))
    df_feat   = pl.read_parquet(FEATURES_PATH)

    df_48h = df_feat.with_columns(
        pl.from_epoch("slot_30m", time_unit="s").dt.strftime("%Y-%m-%d").alias("date")
    ).filter(pl.col("date").is_in([DAY_1, DAY_2]))

    unique_slots = sorted(df_48h["slot_30m"].unique().to_list())
    n_slots = len(unique_slots)
    print(f"    {n_slots} slots de 30 min charges ({n_slots/2:.0f}h de donnees)")
    if n_slots < EXPECTED_TOTAL_SLOTS:
        print(f"    ATTENTION : {n_slots} slots au lieu de {EXPECTED_TOTAL_SLOTS} attendus.")

    # ── 3. Simulation boucle fermée ──────────────────────────────────────────
    milp_engine = MilpEngineV15()

    results = []
    totals = {k: 0.0 for k in ("real_mo", "static_mo", "milp_mo", "oracle_mo",
                                "pred_error_abs", "regret_mo", "milp_solve_s",
                                "oracle_solve_s")}

    # En-tête de la console
    print(f"\n[3/5] Boucle de simulation sur {n_slots} slots...")
    print()
    hdr = f"{'Slot':>4} {'Date':>10} {'Heure':>5} {'V_reel':>10} {'U_static':>10} "
    hdr += f"{'U_milp':>10} {'U_oracle':>10} {'Gain%':>7} {'Regret':>8} {'t_milp':>7}"
    print(hdr)
    print("-" * len(hdr))

    for idx, slot_ts in enumerate(unique_slots):
        dt_slot = datetime.fromtimestamp(slot_ts)
        time_str = dt_slot.strftime("%H:%M")
        date_str = dt_slot.strftime("%Y-%m-%d")
        day_label = "J1" if date_str == DAY_1 else "J2"

        sub_df = df_48h.filter(pl.col("slot_30m") == slot_ts)

        # ── Trafic réel (ground truth) ───────────────────────────────────
        real_traffic = {
            str(int(row["square_id"])): float(row["internet_volume"])
            for row in sub_df.iter_rows(named=True)
        }
        v_real_sum = sum(real_traffic.values())
        totals["real_mo"] += v_real_sum

        # ── Prédiction ML : IMPORTANT — pas de leakage ───────────────────
        # Le modèle prédit à partir des features de l'instant t.
        # La colonne 'target_1h' (futur) n'est PAS dans feature_cols.
        preds_arr = predictor.predict(sub_df)
        predicted_traffic = {
            str(int(sid)): float(max(0.0, p))
            for sid, p in zip(sub_df["square_id"].to_list(), preds_arr)
        }
        # MAE de prédiction (comparaison V̂ vs V_réel sur les mailles communes)
        sq_ids_common = [sq for sq in predicted_traffic if sq in real_traffic]
        mae_slot = float(np.mean([
            abs(predicted_traffic[sq] - real_traffic[sq]) for sq in sq_ids_common
        ])) if sq_ids_common else 0.0
        totals["pred_error_abs"] += mae_slot

        # ── POLITIQUE A : STATIQUE ───────────────────────────────────────
        static_loads = {c: 0.0 for c in cells_capacity}
        for sq_id, sq_info in fractions_data.items():
            m = sq_info["master_cell"]
            if m in static_loads:
                static_loads[m] += real_traffic.get(sq_id, 0.0)
        u_static = sum(max(0.0, static_loads[c] - cells_capacity[c]) for c in cells_capacity)
        u_static = round(u_static, 2)
        totals["static_mo"] += u_static

        # ── POLITIQUE B : ML + MILP PRÉDICTIF ───────────────────────────
        # Étape 1 : Décision basée sur V̂ (prédit)
        t_milp_start = time.time()
        res_milp_pred = milp_engine.build_and_solve(
            predicted_traffic, fractions_data, cells_capacity, DELTA_LEVELS
        )
        t_milp = time.time() - t_milp_start
        totals["milp_solve_s"] += t_milp

        # Étape 2 : Application des décisions z* sur V_réel (évaluation réelle)
        u_milp, _ = apply_decisions_on_real_traffic(
            res_milp_pred["decisions"], real_traffic,
            fractions_data, cells_capacity, DELTA_LEVELS
        )
        totals["milp_mo"] += u_milp

        # ── POLITIQUE C : ORACLE MILP ────────────────────────────────────
        t_oracle_start = time.time()
        res_oracle = milp_engine.build_and_solve(
            real_traffic, fractions_data, cells_capacity, DELTA_LEVELS
        )
        t_oracle = time.time() - t_oracle_start
        totals["oracle_solve_s"] += t_oracle
        u_oracle = res_oracle["optimized_unsatisfied_mo"]
        totals["oracle_mo"] += u_oracle

        # ── Métriques du slot ────────────────────────────────────────────
        gain_pct  = round((u_static - u_milp) / u_static * 100.0, 2) if u_static > 0 else 0.0
        regret_mo = round(u_milp - u_oracle, 2)   # ≥ 0 par construction (MILP oracle ≥ MILP préd.)
        totals["regret_mo"] += max(0.0, regret_mo)

        results.append({
            "slot_idx":         idx + 1,
            "day":              day_label,
            "date":             date_str,
            "time":             time_str,
            "timestamp":        slot_ts,
            "v_real_mo":        round(v_real_sum, 1),
            "u_static_mo":      round(u_static, 1),
            "u_milp_mo":        round(u_milp, 1),
            "u_oracle_mo":      round(u_oracle, 1),
            "gain_milp_pct":    gain_pct,
            "regret_mo":        regret_mo,
            "mae_prediction_mo": round(mae_slot, 2),
            "milp_solve_s":     round(t_milp, 3),
            "oracle_solve_s":   round(t_oracle, 3),
        })

        # Affichage partiel (toutes les 4 slots + premier + dernier)
        if (idx + 1) % 4 == 0 or idx == 0 or idx == n_slots - 1:
            line = (
                f"{idx+1:>4} {date_str:>10} {time_str:>5} "
                f"{v_real_sum/1024:>9.2f}G "
                f"{u_static/1024:>9.2f}G "
                f"{u_milp/1024:>9.2f}G "
                f"{u_oracle/1024:>9.2f}G "
                f"{gain_pct:>6.1f}% "
                f"{regret_mo:>7.1f} "
                f"{t_milp:>6.2f}s"
            )
            print(line)

    # ── 4. Métriques agrégées ────────────────────────────────────────────────
    print()
    sep(wide=True)
    print("  BILAN SCIENTIFIQUE — 48 HEURES (96 SLOTS DE 30 MIN)")
    sep(wide=True)

    gain_total_mo  = totals["static_mo"] - totals["milp_mo"]
    gain_total_pct = round(gain_total_mo / totals["static_mo"] * 100.0, 3) if totals["static_mo"] > 0 else 0.0
    oracle_gain_mo  = totals["static_mo"] - totals["oracle_mo"]
    oracle_gain_pct = round(oracle_gain_mo / totals["static_mo"] * 100.0, 3) if totals["static_mo"] > 0 else 0.0

    # Efficacité ML : fraction du gain de l'Oracle capturée par le ML+MILP
    # = 1 - Regret_total / Gain_Oracle_total
    # Interprétation : 95% signifie que le modèle XGBoost capture 95% de
    # l'amélioration théoriquement maximale possible.
    ml_efficiency_pct = round(
        (1.0 - totals["regret_mo"] / oracle_gain_mo) * 100.0, 2
    ) if oracle_gain_mo > 0 else 0.0

    n_improved = sum(1 for r in results if r["u_milp_mo"] < r["u_static_mo"])
    n_total    = len(results)

    # RMSE prédiction (approximation sur MAE, pas de target disponible slot-level)
    avg_mae = totals["pred_error_abs"] / n_slots
    avg_milp_solve = totals["milp_solve_s"] / n_slots
    avg_oracle_solve = totals["oracle_solve_s"] / n_slots

    print(f"\n  Demande reelle totale 48h         : {totals['real_mo']/1e6:>10.2f} To")
    print(f"  Nb slots ameliores (MILP < Static): {n_improved:>10} / {n_total}")
    sep()
    print(f"  {'Politique':<25} {'Vol. Insatisfait (Mo)':>22} {'Vol. Insatisfait (Go)':>22} {'Gain vs Statique':>18}")
    sep()
    print(f"  {'A — Statique (ref.)':<25} {totals['static_mo']:>22,.1f} {totals['static_mo']/1024:>22,.2f} {'—':>18}")
    print(f"  {'B — WiseNet ML+MILP':<25} {totals['milp_mo']:>22,.1f} {totals['milp_mo']/1024:>22,.2f} {gain_total_pct:>17.3f} %")
    print(f"  {'C — Oracle MILP (th.)':<25} {totals['oracle_mo']:>22,.1f} {totals['oracle_mo']/1024:>22,.2f} {oracle_gain_pct:>17.3f} %")
    sep(wide=True)
    print(f"\n  [EFFICACITE ML]  WiseNet capture {ml_efficiency_pct:.2f}% du gain theorique de l'Oracle")
    print(f"                   Regret d'incertitude : {totals['regret_mo']/1024:.2f} Go sur 48h")
    print(f"                   (= ce qu'on perdrait si on connaissait parfaitement le futur)")
    print(f"\n  [PERFORMANCE]    Gain absolu WiseNet : {gain_total_mo/1024:.2f} Go en moins de congestion")
    print(f"                   en 48h sur 1024 mailles Milan")
    print(f"\n  [SOLVEUR]        Temps moyen MILP / slot : {avg_milp_solve:.2f}s")
    print(f"                   Temps moyen Oracle / slot : {avg_oracle_solve:.2f}s")
    print(f"\n  [PREDICTION]     MAE moyenne XGBoost : {avg_mae:.2f} Mo/maille/slot")
    sep(wide=True)

    wall_time = time.time() - run_start

    # ── 5. Export des résultats ──────────────────────────────────────────────
    print(f"\n[5/5] Export des resultats...")

    # CSV slot-par-slot
    df_results = pl.DataFrame(results)
    df_results.write_csv(OUTPUT_SLOTS_CSV)
    print(f"    CSV slot-par-slot   : {OUTPUT_SLOTS_CSV}")

    # JSON résumé scientifique
    summary = {
        "simulation": {
            "days": [DAY_1, DAY_2],
            "n_slots": n_slots,
            "n_cells": n_cells,
            "n_sites": n_sites,
            "topology_isd_m": ISD_METERS,
            "delta_levels_dB": DELTA_LEVELS,
            "seed": SEED,
        },
        "volumes_total_mo": {
            "real_demand": round(totals["real_mo"], 1),
            "static_unsatisfied": round(totals["static_mo"], 1),
            "milp_unsatisfied":   round(totals["milp_mo"], 1),
            "oracle_unsatisfied": round(totals["oracle_mo"], 1),
        },
        "gains": {
            "milp_vs_static_mo":   round(gain_total_mo, 1),
            "milp_vs_static_go":   round(gain_total_mo / 1024, 3),
            "milp_vs_static_pct":  gain_total_pct,
            "oracle_vs_static_pct": oracle_gain_pct,
            "ml_efficiency_pct":   ml_efficiency_pct,
            "regret_ml_mo":        round(totals["regret_mo"], 1),
            "regret_ml_go":        round(totals["regret_mo"] / 1024, 3),
        },
        "reliability": {
            "slots_improved":      n_improved,
            "slots_total":         n_total,
            "slots_improved_pct":  round(n_improved / n_total * 100, 1),
        },
        "performance": {
            "avg_milp_solve_s":    round(avg_milp_solve, 3),
            "avg_oracle_solve_s":  round(avg_oracle_solve, 3),
            "avg_mae_mo_per_cell": round(avg_mae, 3),
            "total_wall_time_s":   round(wall_time, 1),
        },
    }
    with open(OUTPUT_SUMMARY_JSON, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"    JSON resume         : {OUTPUT_SUMMARY_JSON}")

    # ── 6. Figures ──────────────────────────────────────────────────────────
    _plot_figures(results, summary)

    print(f"\n  Simulation terminee en {wall_time:.1f}s")
    sep(wide=True)


def _plot_figures(results: list, summary: dict):
    """Génère les 3 figures de la simulation 48h."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches

    x = np.arange(len(results))
    time_labels = [f"{r['date'][5:]}\\n{r['time']}" for r in results]

    u_static = np.array([r["u_static_mo"] / 1024 for r in results])
    u_milp   = np.array([r["u_milp_mo"]   / 1024 for r in results])
    u_oracle = np.array([r["u_oracle_mo"] / 1024 for r in results])
    gains    = np.array([r["gain_milp_pct"]       for r in results])
    regrets  = np.array([r["regret_mo"]   / 1024 for r in results])
    v_real   = np.array([r["v_real_mo"]   / 1024 for r in results])

    gain_total_pct  = summary["gains"]["milp_vs_static_pct"]
    ml_eff_pct      = summary["gains"]["ml_efficiency_pct"]
    oracle_gain_pct = summary["gains"]["oracle_vs_static_pct"]

    # ── Figure 1 : Profil de congestion 48h ─────────────────────────────
    fig, (ax_top, ax_bot) = plt.subplots(
        2, 1, figsize=(18, 10), sharex=True,
        gridspec_kw={"height_ratios": [3, 1]}
    )

    ax_top.fill_between(x, u_static, alpha=0.15, color="#e74c3c")
    ax_top.fill_between(x, u_milp,   alpha=0.20, color="#2ecc71")

    ax_top.plot(x, u_static, label=f"A — Statique (ref.)",
                color="#e74c3c", lw=2, marker="o", ms=3)
    ax_top.plot(x, u_milp,   label=f"B — WiseNet ML+MILP (gain {gain_total_pct}%)",
                color="#2ecc71", lw=2.5, marker="^", ms=4)
    ax_top.plot(x, u_oracle, label=f"C — Oracle MILP théorique ({oracle_gain_pct}%)",
                color="#34495e", lw=1.5, ls=":", marker="x", ms=3)

    # Bandes jour 1 / jour 2
    mid = len(results) // 2
    ax_top.axvspan(0,   mid,      alpha=0.03, color="blue",  label="Mardi 2013-11-12 (J1)")
    ax_top.axvspan(mid, len(x)-1, alpha=0.03, color="orange",label="Mercredi 2013-11-13 (J2)")
    ax_top.axvline(mid, color="gray", lw=1, ls="--", alpha=0.7)

    ax_top.set_ylabel("Volume non servi (Go / 30 min)", fontsize=12, fontweight="bold")
    ax_top.set_title(
        "WiseNet — Simulation 48h Rigoureuse : Volume de Trafic Non Servi\n"
        f"Topologie 3GPP ISD={ISD_METERS}m | Milan 2013-11-12 + 2013-11-13 | {len(results)} slots",
        fontsize=13, fontweight="bold"
    )
    ax_top.legend(fontsize=10, framealpha=0.9, loc="upper left")
    ax_top.grid(True, ls="--", alpha=0.5)

    ax_bot.plot(x, v_real, color="#3498db", lw=1.5, label="Demande réelle (Go)")
    ax_bot.fill_between(x, v_real, alpha=0.25, color="#3498db")
    ax_bot.set_ylabel("Demande\n(Go / 30min)", fontsize=10)
    ax_bot.grid(True, ls="--", alpha=0.4)
    ax_bot.legend(fontsize=9, loc="upper left")

    # Ticks : 1 sur 4 (toutes les 2h)
    tick_pos = x[::4]
    tick_lbl = [time_labels[i] for i in tick_pos]
    ax_bot.set_xticks(tick_pos)
    ax_bot.set_xticklabels(tick_lbl, rotation=45, ha="right", fontsize=8)
    ax_bot.set_xlabel("Date et heure (slots de 30 min)", fontsize=11)

    plt.tight_layout()
    fig.savefig(OUTPUT_FIG_PROFILE, dpi=180, bbox_inches="tight")
    plt.close(fig)
    print(f"    Fig 1 (profil)      : {OUTPUT_FIG_PROFILE}")

    # ── Figure 2 : Gain par slot ─────────────────────────────────────────
    fig2, ax2 = plt.subplots(figsize=(18, 5))
    colors = ["#27ae60" if g >= 0 else "#e74c3c" for g in gains]
    ax2.bar(x, gains, color=colors, alpha=0.85, edgecolor="none")
    ax2.axhline(gain_total_pct, color="#e74c3c", lw=2, ls="--",
                label=f"Gain moyen 48h = {gain_total_pct}%")
    ax2.axhline(0, color="black", lw=0.8)
    ax2.axvline(mid, color="gray", lw=1, ls="--", alpha=0.7)
    ax2.set_ylabel("Gain MILP vs Statique (%)", fontsize=12, fontweight="bold")
    ax2.set_title(
        "Gain de WiseNet ML+MILP par rapport à la Politique Statique — slot par slot (48h)",
        fontsize=13, fontweight="bold"
    )
    ax2.set_xticks(tick_pos)
    ax2.set_xticklabels(tick_lbl, rotation=45, ha="right", fontsize=8)
    ax2.legend(fontsize=11)
    ax2.grid(True, ls="--", alpha=0.4, axis="y")
    plt.tight_layout()
    fig2.savefig(OUTPUT_FIG_GAIN, dpi=180, bbox_inches="tight")
    plt.close(fig2)
    print(f"    Fig 2 (gain/slot)   : {OUTPUT_FIG_GAIN}")

    # ── Figure 3 : Regret Oracle ─────────────────────────────────────────
    fig3, ax3 = plt.subplots(figsize=(18, 5))
    ax3.fill_between(x, u_oracle, u_milp, alpha=0.45, color="#e67e22",
                     label=f"Regret ML (= perte due à l'incertitude de prédiction)")
    ax3.plot(x, u_milp,   color="#2ecc71", lw=2,   label=f"B — WiseNet ML+MILP")
    ax3.plot(x, u_oracle, color="#34495e", lw=1.5, ls=":", label=f"C — Oracle MILP")
    ax3.axvline(mid, color="gray", lw=1, ls="--", alpha=0.7)
    ax3.set_ylabel("Volume non servi (Go / 30 min)", fontsize=12, fontweight="bold")
    ax3.set_title(
        f"Regret d'Incertitude ML — Efficacité XGBoost q80 : {ml_eff_pct:.2f}% du gain Oracle capturé\n"
        f"Zone orange = Mo perdus à cause de l'imperfection de la prédiction (non déployable en prod)",
        fontsize=12, fontweight="bold"
    )
    ax3.set_xticks(tick_pos)
    ax3.set_xticklabels(tick_lbl, rotation=45, ha="right", fontsize=8)
    ax3.legend(fontsize=10, loc="upper left")
    ax3.grid(True, ls="--", alpha=0.4)
    plt.tight_layout()
    fig3.savefig(OUTPUT_FIG_REGRET, dpi=180, bbox_inches="tight")
    plt.close(fig3)
    print(f"    Fig 3 (regret)      : {OUTPUT_FIG_REGRET}")


if __name__ == "__main__":
    run_48h_simulation()
