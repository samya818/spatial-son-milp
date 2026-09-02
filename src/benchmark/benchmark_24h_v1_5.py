"""
WiseNet V1.5 — 24-Hour Benchmark Runner (48 Time Slots of 30 Minutes)
Évaluation temporelle complète sur 24 heures consécutives de trafic réel Telecom Italia Milan :
  - Date de référence : 2013-11-07 (Journée de trafic de pointe : 44.6 To de demande)
  - 48 slots temporels consécutifs de 30 minutes (00:00 à 23:30)
  - Topologie 3GPP hexagonale (ISD=750m, 126 sites, 378 secteurs, 756 cellules radio)
  - Comparaison rigoureuse : Statique vs Greedy vs MILP
  - Génération des métriques agrégées et du graphique de profil journalier
"""

import sys
import os
import time
from pathlib import Path
from datetime import datetime
import polars as pl
import numpy as np
import matplotlib.pyplot as plt
import logging

# Encodage UTF-8
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

logging.basicConfig(level=logging.WARNING, format="%(levelname)s | %(message)s")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.topology.builder_v1_5 import TopologyBuilderV15, CELL_SIZE_METERS, GRID_SIZE
from src.spatial.simulator_v1_5 import SpatialTransferSimulatorV15
from src.optimization.milp_engine_v1_5 import MilpEngineV15
from src.optimization.greedy_engine_v1_5 import GreedyEngineV15

# Configuration
BLOCK_ROW = (35, 67)
BLOCK_COL = (35, 67)
ISD_METERS = 750.0
DELTA_LEVELS = [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0]
SIM_RESOLUTION = 20
TARGET_DATE = "2013-11-07"
PARQUET_PATH = Path("research/data/processed/work_1024cells.parquet")
OUTPUT_FIG_PATH = Path("research/reports/figures/v1_5_24h_benchmark.png")
OUTPUT_CSV_PATH = Path("research/reports/v1_5_24h_results.csv")

def sep(wide=False):
    print("=" * 70 if wide else "-" * 70)

def run_24h_benchmark():
    print()
    sep(wide=True)
    print("  WiseNet V1.5 -- Benchmark 24 Heures (48 Slots de 30 min)")
    print(f"  Données réelles Telecom Italia Milan | Date : {TARGET_DATE}")
    sep(wide=True)

    # 1. Topologie 3GPP Hexagonale
    print("\n[1/4] Génération de la topologie 3GPP hexagonale...")
    t0 = time.time()
    builder = TopologyBuilderV15(isd_meters=ISD_METERS)
    topology = builder.generate_hexagonal_topology(row_range=BLOCK_ROW, col_range=BLOCK_COL)
    n_sites = len(topology)
    n_cells = n_sites * 6
    print(f"      {n_sites} sites, {n_sites*3} secteurs, {n_cells} cellules radio (s, f) en {time.time()-t0:.2f}s")

    # 2. Simulation Spatiale RSRP 3GPP
    squares = [
        r * GRID_SIZE + c + 1
        for r in range(BLOCK_ROW[0], BLOCK_ROW[1])
        for c in range(BLOCK_COL[0], BLOCK_COL[1])
    ]
    print(f"\n[2/4] Précalcul spatial RSRP 3GPP sur {len(squares)} mailles...")
    t0 = time.time()
    sim = SpatialTransferSimulatorV15(grid_resolution=SIM_RESOLUTION, cell_size_meters=CELL_SIZE_METERS, delta_levels=DELTA_LEVELS)
    fractions_data = sim.compute_transfer_fractions(squares, topology, grid_size=GRID_SIZE)
    print(f"      Matrices calculées en {time.time()-t0:.2f}s")

    # 3. Extraction des 48 slots du jour cible
    print(f"\n[3/4] Extraction des 48 créneaux de 30 min pour le {TARGET_DATE}...")
    df = pl.read_parquet(PARQUET_PATH)
    
    # Filtrer sur la date cible
    df_day = df.with_columns(
        pl.col('slot_30m').map_elements(lambda ts: datetime.fromtimestamp(ts).strftime('%Y-%m-%d'), return_dtype=pl.String).alias('date')
    ).filter(pl.col('date') == TARGET_DATE)
    
    unique_slots = sorted(df_day['slot_30m'].unique().to_list())
    if len(unique_slots) != 48:
        print(f"Attention : {len(unique_slots)} slots trouvés au lieu de 48. Utilisation des slots disponibles.")

    cells_capacity = {}
    for s_data in topology.values():
        for sec_data in s_data['sectors'].values():
            for c_data in sec_data['carriers'].values():
                cells_capacity[c_data['cell_id']] = c_data['capacity_mo']

    greedy_engine = GreedyEngineV15()
    milp_engine = MilpEngineV15()

    slot_results = []
    total_static_mo = 0.0
    total_greedy_mo = 0.0
    total_milp_mo = 0.0
    total_demand_mo = 0.0
    total_milp_time = 0.0

    print(f"\n[4/4] Exécution de l'optimisation sur les 48 créneaux temporels...")
    print(f"      {'Slot':<5} {'Heure':<6} {'Demande (Mo)':>14} {'Statique (Mo)':>14} {'Greedy (Mo)':>13} {'MILP (Mo)':>13} {'Gain MILP':>10}")
    print("      " + "-" * 80)

    for idx, slot_ts in enumerate(unique_slots):
        slot_time_str = datetime.fromtimestamp(slot_ts).strftime('%H:%M')
        sub_df = df_day.filter(pl.col('slot_30m') == slot_ts)
        
        predicted_traffic = {
            str(int(row['square_id'])): float(row['internet_volume'])
            for row in sub_df.iter_rows(named=True)
        }
        slot_demand = sum(predicted_traffic.values())
        total_demand_mo += slot_demand

        # Statique
        cell_traffic = {c: 0.0 for c in cells_capacity}
        for sq_id, sq_info in fractions_data.items():
            m = sq_info['master_cell']
            if m in cell_traffic:
                cell_traffic[m] += predicted_traffic.get(sq_id, 0.0)
        static_unsat = sum(max(0.0, cell_traffic[c] - cap) for c, cap in cells_capacity.items())

        # Greedy
        res_greedy = greedy_engine.solve(predicted_traffic, fractions_data, cells_capacity, DELTA_LEVELS)
        greedy_unsat = res_greedy['optimized_unsatisfied_mo']

        # MILP
        t_start = time.time()
        res_milp = milp_engine.build_and_solve(predicted_traffic, fractions_data, cells_capacity, DELTA_LEVELS)
        t_solve = time.time() - t_start
        milp_unsat = res_milp['optimized_unsatisfied_mo']
        total_milp_time += t_solve

        gain_pct = round(((static_unsat - milp_unsat) / static_unsat * 100.0), 2) if static_unsat > 0 else 0.0

        total_static_mo += static_unsat
        total_greedy_mo += greedy_unsat
        total_milp_mo += milp_unsat

        slot_results.append({
            'slot_idx': idx + 1,
            'time_str': slot_time_str,
            'timestamp': slot_ts,
            'demand_mo': round(slot_demand, 1),
            'static_unsatisfied_mo': round(static_unsat, 1),
            'greedy_unsatisfied_mo': round(greedy_unsat, 1),
            'milp_unsatisfied_mo': round(milp_unsat, 1),
            'gain_percentage': gain_pct,
            'solve_time_s': round(t_solve, 3)
        })

        if (idx + 1) % 4 == 0 or idx == 0 or idx == len(unique_slots) - 1:
            print(f"      {idx+1:<5} {slot_time_str:<6} {slot_demand:>14,.0f} {static_unsat:>14,.0f} {greedy_unsat:>13,.0f} {milp_unsat:>13,.0f} {gain_pct:>9.1f} %")

    # Bilan Global 24h
    total_gain_greedy = round(((total_static_mo - total_greedy_mo) / total_static_mo * 100.0), 2) if total_static_mo > 0 else 0.0
    total_gain_milp = round(((total_static_mo - total_milp_mo) / total_static_mo * 100.0), 2) if total_static_mo > 0 else 0.0
    diff_milp_greedy_mo = total_greedy_mo - total_milp_mo

    print()
    sep(wide=True)
    print(f"  BILAN GLOBAL 24 HEURES — {TARGET_DATE} (48 CRÉNEAUX DE 30 MIN)")
    sep(wide=True)
    print(f"  Demande totale sur 24h     : {total_demand_mo:>16,.1f} Mo  ({total_demand_mo/1024:.2f} Go)")
    print(f"  Temps moyen solveur MILP   : {total_milp_time/len(unique_slots):>16.3f} s / slot")
    sep()
    print(f"  {'Approche':<15} {'Volume Insatisfait (Mo)':>25} {'Volume Insatisfait (Go)':>25} {'Gain 24h':>12}")
    sep()
    print(f"  {'Statique':<15} {total_static_mo:>25,.1f} {total_static_mo/1024:>25,.2f} {'---':>12}")
    print(f"  {'Greedy':<15} {total_greedy_mo:>25,.1f} {total_greedy_mo/1024:>25,.2f} {total_gain_greedy:>11.2f} %")
    print(f"  {'WiseNet MILP':<15} {total_milp_mo:>25,.1f} {total_milp_mo/1024:>25,.2f} {total_gain_milp:>11.2f} %")
    sep(wide=True)
    print(f"  [PREUVE] Sur 24 heures, le MILP livre {diff_milp_greedy_mo:,.1f} Mo (+{diff_milp_greedy_mo/1024:.2f} Go)")
    print(f"           de trafic supplémentaire par rapport au Glouton sur les mêmes 1024 cellules.")
    sep(wide=True)

    # Sauvegarde des résultats en CSV
    OUTPUT_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    res_df = pl.DataFrame(slot_results)
    res_df.write_csv(OUTPUT_CSV_PATH)
    print(f"\nRésultats CSV 24h sauvegardés dans : {OUTPUT_CSV_PATH}")

    # Génération du Graphique 24h
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 9), sharex=True)
    
    time_labels = [r['time_str'] for r in slot_results]
    x_indices = np.arange(len(time_labels))
    
    # Graphe 1 : Profil temporel de congestion
    ax1.plot(x_indices, [r['static_unsatisfied_mo']/1024 for r in slot_results], label='Statique (0 dB)', color='#e74c3c', linewidth=2, marker='o', markersize=3)
    ax1.plot(x_indices, [r['greedy_unsatisfied_mo']/1024 for r in slot_results], label=f'Greedy (Gain 24h: {total_gain_greedy}%)', color='#f39c12', linewidth=2, linestyle='--', marker='s', markersize=3)
    ax1.plot(x_indices, [r['milp_unsatisfied_mo']/1024 for r in slot_results], label=f'WiseNet V1.5 MILP (Gain 24h: {total_gain_milp}%)', color='#2ecc71', linewidth=2.5, marker='^', markersize=4)
    ax1.set_ylabel('Volume Non Servi (Go / 30 min)', fontsize=11, fontweight='bold')
    ax1.set_title(f'WiseNet V1.5 — Profil Journalier de Congestion sur 24h (Telecom Italia Milan - {TARGET_DATE})', fontsize=12, fontweight='bold')
    ax1.grid(True, linestyle='--', alpha=0.6)
    ax1.legend(loc='upper right', fontsize=10, framealpha=0.9)
    
    # Graphe 2 : Gain horaire du MILP (%)
    gains = [r['gain_percentage'] for r in slot_results]
    ax2.bar(x_indices, gains, color='#3498db', alpha=0.8, edgecolor='#2980b9')
    ax2.axhline(total_gain_milp, color='#e74c3c', linestyle='--', linewidth=1.5, label=f'Gain Moyen 24h ({total_gain_milp}%)')
    ax2.set_xlabel('Heure de la Journée (Créneaux de 30 minutes)', fontsize=11, fontweight='bold')
    ax2.set_ylabel('Réduction de Congestion (%)', fontsize=11, fontweight='bold')
    ax2.set_title('Taux de Réduction de la Congestion par Créneau (Gain MILP vs Statique)', fontsize=11, fontweight='bold')
    ax2.set_xticks(x_indices[::2])
    ax2.set_xticklabels(time_labels[::2], rotation=45, ha='right')
    ax2.grid(True, linestyle='--', alpha=0.6)
    ax2.legend(loc='upper right', fontsize=10)

    plt.tight_layout()
    OUTPUT_FIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(OUTPUT_FIG_PATH, dpi=180, bbox_inches='tight')
    plt.close()
    print(f"Graphique 24h sauvegardé dans : {OUTPUT_FIG_PATH}")

if __name__ == "__main__":
    run_24h_benchmark()
