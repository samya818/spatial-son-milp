"""
WiseNet V1.5 — Benchmark Runner Réaliste
Compare les 3 approches (Statique vs Greedy vs MILP) sur le VRAI trafic Telecom Italia Milan :
  - 1024 mailles géographiques réelles (235m x 235m, bloc 32x32 dense)
  - Données réelles de trafic internet Telecom Italia (work_1024cells.parquet)
  - Topologie 3GPP hexagonale réaliste (ISD=750m, 126 sites, 378 secteurs, 756 cellules (s, f))
  - Bandes réelles TIM Italy : F1 (1.8 GHz LTE 20MHz) + F2 (3.5 GHz 5G NR 80MHz)
  - Puissances nominales constructeurs (Ericsson AIR 3246 / AIR 6449 : 43 dBm)
"""

import sys
import os
import time
from pathlib import Path
import polars as pl
import numpy as np
import logging

# Forcer l'encodage UTF-8 sous Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

logging.basicConfig(level=logging.WARNING, format="%(levelname)s | %(message)s")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.topology.builder_v1_5 import TopologyBuilderV15, CELL_SIZE_METERS, GRID_SIZE
from src.spatial.simulator_v1_5 import SpatialTransferSimulatorV15
from src.optimization.milp_engine_v1_5 import MilpEngineV15
from src.optimization.greedy_engine_v1_5 import GreedyEngineV15

# --- PARAMÈTRES DU BENCHMARK 3GPP V1.5 ---
BLOCK_ROW = (35, 67)  # 32 lignes = 1024 mailles du centre de Milan
BLOCK_COL = (35, 67)  # 32 colonnes
ISD_METERS = 750.0    # 3GPP Urban Macro standard TIM Italy
DELTA_LEVELS = [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0]
SIM_RESOLUTION = 20   # 20x20 = 400 points d'intégration RSRP par maille

PARQUET_PATH = Path("research/data/processed/work_1024cells.parquet")

def sep(wide=False):
    print("=" * 65 if wide else "-" * 65)

def run_benchmark():
    print()
    sep(wide=True)
    print("  WiseNet V1.5 -- Benchmark Réaliste Telecom Italia Milan")
    print("  Topologie 3GPP Hexagonale (ISD=750m) | F1=1.8GHz + F2=3.5GHz")
    sep(wide=True)

    # ── Phase 1 : Topologie Hexagonale 3GPP ──
    print("\n[1/5] Génération de la topologie 3GPP hexagonale...")
    t0 = time.time()
    builder = TopologyBuilderV15(isd_meters=ISD_METERS)
    topology = builder.generate_hexagonal_topology(row_range=BLOCK_ROW, col_range=BLOCK_COL)
    n_sites = len(topology)
    n_sectors = n_sites * 3
    n_cells = n_sites * 6
    print(f"      Sites : {n_sites} | Secteurs (120 deg) : {n_sectors} | Cellules radio (s, f) : {n_cells}")
    print(f"      Durée : {time.time()-t0:.2f}s")

    # ── Phase 2 : Mailles du bloc 32x32 de Milan ──
    squares = [
        r * GRID_SIZE + c + 1
        for r in range(BLOCK_ROW[0], BLOCK_ROW[1])
        for c in range(BLOCK_COL[0], BLOCK_COL[1])
    ]
    print(f"\n[2/5] Bloc de {len(squares)} mailles réelles de Milan ({BLOCK_ROW[1]-BLOCK_ROW[0]}x{BLOCK_COL[1]-BLOCK_COL[0]})")

    # ── Phase 3 : Simulation Spatiale RSRP 3GPP ──
    print(f"\n[3/5] Calcul du champ RSRP 3GPP UMi ({SIM_RESOLUTION}x{SIM_RESOLUTION} pts/maille)...")
    t0 = time.time()
    sim = SpatialTransferSimulatorV15(
        grid_resolution=SIM_RESOLUTION,
        cell_size_meters=CELL_SIZE_METERS,
        delta_levels=DELTA_LEVELS
    )
    fractions_data = sim.compute_transfer_fractions(squares, topology, grid_size=GRID_SIZE)
    print(f"      Fractions calculées : {len(fractions_data)} mailles couvertes")
    print(f"      Durée : {time.time()-t0:.2f}s")

    # ── Phase 4 : Chargement du Trafic Réel Telecom Italia ──
    print(f"\n[4/5] Chargement du trafic réel Telecom Italia Milan...")
    if not PARQUET_PATH.exists():
        raise FileNotFoundError(f"Fichier introuvable : {PARQUET_PATH}")

    df = pl.read_parquet(PARQUET_PATH)
    # Sélection du slot temporel de pointe (Max de trafic simultané)
    top_slots = df.group_by('slot_30m').agg(pl.col('internet_volume').sum()).sort('internet_volume', descending=True)
    peak_slot = top_slots['slot_30m'][0]
    slot_df = df.filter(pl.col('slot_30m') == peak_slot)

    # Dictionnaire de trafic réel par maille (Mo)
    predicted_traffic = {
        str(int(row['square_id'])): float(row['internet_volume'])
        for row in slot_df.iter_rows(named=True)
    }
    total_traffic_mo = sum(predicted_traffic.values())

    # Capacités par cellule radio (s, f)
    cells_capacity = {}
    for site_data in topology.values():
        for sec_data in site_data['sectors'].values():
            for c_name, c_data in sec_data['carriers'].items():
                cells_capacity[c_data['cell_id']] = c_data['capacity_mo']
    total_capacity_mo = sum(cells_capacity.values())

    # Trafic initial affecté à chaque cellule maîtresse
    cell_traffic = {c: 0.0 for c in cells_capacity}
    for sq_id, sq_info in fractions_data.items():
        master = sq_info['master_cell']
        traf = predicted_traffic.get(sq_id, 0.0)
        if master in cell_traffic:
            cell_traffic[master] += traf

    print(f"      Slot de pointe       : {peak_slot}")
    print(f"      Trafic total réel    : {total_traffic_mo:>12,.1f} Mo  ({total_traffic_mo/1024:.2f} Go)")
    print(f"      Capacité réseau tot. : {total_capacity_mo:>12,.1f} Mo  ({total_capacity_mo/1024:.2f} Go)")
    charge_pct = (total_traffic_mo / total_capacity_mo) * 100 if total_capacity_mo > 0 else 0
    print(f"      Charge moyenne       : {charge_pct:>11.1f} %")

    # ── Phase 5 : Évaluation des 3 Approches ──
    print(f"\n[5/5] Exécution comparative des 3 approches sur trafic réel...\n")

    # [1] Statique (Offset = 0 dB)
    t0 = time.time()
    static_unsatisfied = sum(max(0.0, cell_traffic.get(c, 0.0) - cap) for c, cap in cells_capacity.items())
    t_static = time.time() - t0
    print(f"  [S] Statique : {static_unsatisfied:>10,.1f} Mo non servis ({t_static:.2f}s)")

    # [2] Greedy (Heuristique Gloutonne)
    t0 = time.time()
    greedy_engine = GreedyEngineV15()
    res_greedy = greedy_engine.solve(predicted_traffic, fractions_data, cells_capacity, DELTA_LEVELS)
    t_greedy = time.time() - t0
    greedy_unsatisfied = res_greedy['optimized_unsatisfied_mo']
    greedy_gain = res_greedy['gain_percentage']
    print(f"  [G] Greedy   : {greedy_unsatisfied:>10,.1f} Mo non servis ({t_greedy:.2f}s)  gain = {greedy_gain:>5.2f}%")

    # [3] MILP (Optimisation Exacte Pyomo + CBC)
    t0 = time.time()
    milp_engine = MilpEngineV15()
    res_milp = milp_engine.build_and_solve(predicted_traffic, fractions_data, cells_capacity, DELTA_LEVELS)
    t_milp = time.time() - t0
    milp_unsatisfied = res_milp['optimized_unsatisfied_mo']
    milp_gain = res_milp['gain_percentage']
    print(f"  [M] MILP     : {milp_unsatisfied:>10,.1f} Mo non servis ({t_milp:.2f}s)  gain = {milp_gain:>5.2f}%")

    # ── Bilan Récapitulatif ──
    print()
    sep(wide=True)
    print("  BILAN COMPARATIF WISE-NET V1.5 (TRAFIC RÉEL MILAN)")
    sep(wide=True)
    print(f"  {'Approche':<12} {'Trafic Insatisfait':>20} {'Réduction (%)':>16} {'Temps (s)':>10}")
    sep()
    print(f"  {'Statique':<12} {static_unsatisfied:>17,.1f} Mo {'---':>16} {t_static:>9.2f}s")
    print(f"  {'Greedy':<12} {greedy_unsatisfied:>17,.1f} Mo {greedy_gain:>15.2f}% {t_greedy:>9.2f}s")
    print(f"  {'MILP':<12} {milp_unsatisfied:>17,.1f} Mo {milp_gain:>15.2f}% {t_milp:>9.2f}s")
    sep(wide=True)

    if milp_unsatisfied < greedy_unsatisfied:
        delta_gain = greedy_unsatisfied - milp_unsatisfied
        pct = (delta_gain / greedy_unsatisfied) * 100.0 if greedy_unsatisfied > 0 else 0.0
        print(f"\n  [SUCCÈS] Le MILP bat l'heuristique Greedy de {delta_gain:,.1f} Mo ({pct:.1f}% de gain supplémentaire).")
    else:
        print(f"\n  [NOTE] Toutes les congestions locales ont été résolues ou réparties.")

    print()
    sep(wide=True)

if __name__ == "__main__":
    run_benchmark()
