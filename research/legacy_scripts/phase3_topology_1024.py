import numpy as np
import json
import yaml
import polars as pl
from pathlib import Path
from scipy.spatial import cKDTree
from collections import defaultdict

# --- CONFIGURATION ---
GRID_SIZE = 100
SEED = 42
rng = np.random.default_rng(SEED)

# Profils calibrés sur densité Milan (ARPA 2025)
# Note : Les Micros ont un SINR supérieur aux Macros (20dB vs 15dB), 
# ce qui leur donne une capacité ~32% supérieure à BW égale.
ANTENNA_PROFILES = {
    'macro':     {'bw_mhz': 20, 'sinr_db': 15, 'tx_power_dBm': 46, 'height_m': 25, 'coverage_radius_grid': 3.5},
    'micro':     {'bw_mhz': 20, 'sinr_db': 20, 'tx_power_dBm': 37, 'height_m': 8,  'coverage_radius_grid': 0.9},
    'smallcell': {'bw_mhz': 10, 'sinr_db': 25, 'tx_power_dBm': 24, 'height_m': 4,  'coverage_radius_grid': 0.2},
}

# Bloc 35-66, 35-66
BLOC_ROWS = (35, 67)
BLOC_COLS = (35, 67)

def capacity_from_radio(bw_mhz, sinr_db, spectral_eff=0.6, utilization=0.6, duration_s=1800):
    bw_hz     = bw_mhz * 1e6
    sinr_lin  = 10 ** (sinr_db / 10)
    cap_bps   = bw_hz * np.log2(1 + sinr_lin) * spectral_eff
    volume_mo = (cap_bps * duration_s * utilization) / (8 * 1e6)
    return round(volume_mo, 1)

def generate_bloc_topology(rng):
    antennas = {}
    idx = 0
    placed_positions = []
    
    # On utilise la densité 'center' pour tout le bloc car c'est au centre
    density = 0.22
    type_proba = {'macro': 0.3, 'micro': 0.45, 'smallcell': 0.25}
    jitter = 2.0
    
    r0, r1 = BLOC_ROWS
    c0, c1 = BLOC_COLS
    area = (r1 - r0) * (c1 - c0)
    n_ant = int(area * density)
    print(f"Génération de {n_ant} antennes pour le bloc {area} cellules...")
    
    for _ in range(n_ant):
        r = rng.uniform(r0, r1)
        c = rng.uniform(c0, c1)
        
        # Éviter les superpositions strictes
        too_close = any(np.hypot(r-pr, c-pc) < 0.5 for pr, pc in placed_positions)
        if too_close: continue
        
        types = list(type_proba.keys())
        probas = list(type_proba.values())
        ant_type = rng.choice(types, p=probas)
        profile = ANTENNA_PROFILES[ant_type]
        
        base_capacity = capacity_from_radio(profile['bw_mhz'], profile['sinr_db'])
        capacity_mo = float(base_capacity * (1 + rng.normal(0, 0.1)))
        
        antennas[f'A{idx:03d}'] = {
            'x': float(c), 'y': float(r), 'type': str(ant_type), 'zone': 'center',
            'capacity_mo': float(round(capacity_mo, 1)),
            'bw_mhz': int(profile['bw_mhz']), 'sinr_db': int(profile['sinr_db']),
            'tx_power_dBm': int(profile['tx_power_dBm']), 'height_m': int(profile['height_m']),
            'coverage_radius': float(profile['coverage_radius_grid']),
        }
        placed_positions.append((r, c)); idx += 1
    return antennas

def build_neighbor_graph(antennas, threshold=8.0):
    ant_ids = list(antennas.keys())
    coords = np.array([[antennas[a]['y'], antennas[a]['x']] for a in ant_ids])
    tree = cKDTree(coords)
    neighbors = {}
    for i, a_id in enumerate(ant_ids):
        idx_neighbors = tree.query_ball_point(coords[i], r=threshold)
        neighbors[a_id] = [ant_ids[j] for j in idx_neighbors if ant_ids[j] != a_id]
    return neighbors

def assign_bloc_cells(antennas):
    bloc_cells = [(i, j) for i in range(BLOC_ROWS[0], BLOC_ROWS[1]) 
                          for j in range(BLOC_COLS[0], BLOC_COLS[1])]
    cell_centers = np.array([(i + 0.5, j + 0.5) for i, j in bloc_cells])
    ant_ids = list(antennas.keys())
    ant_coords = np.array([[antennas[a]['y'], antennas[a]['x']] for a in ant_ids])
    tree = cKDTree(ant_coords)
    _, nearest_idx = tree.query(cell_centers, k=1)
    
    coverage = defaultdict(list)
    for (i, j), ant_idx in zip(bloc_cells, nearest_idx):
        square_id = i * 100 + j + 1
        coverage[ant_ids[ant_idx]].append(int(square_id))
    return dict(coverage)

def run_topology():
    print("Génération de la topologie Bloc 1024...")
    antennas = generate_bloc_topology(rng)
    print(f"{len(antennas)} antennes générées.")

    print("Calcul du graphe de voisinage...")
    neighbor_graph = build_neighbor_graph(antennas)

    print("Assignation des 1024 cellules...")
    coverage_1024 = assign_bloc_cells(antennas)

    # Sauvegarde
    with open('config/network_topology_1024.yaml', 'w') as f:
        yaml.dump({'antennas': antennas}, f)
    with open('data/processed/cell_antenna_map_1024.json', 'w') as f:
        json.dump(coverage_1024, f)
    with open('data/processed/neighbor_graph_1024.json', 'w') as f:
        json.dump(neighbor_graph, f)
    print("Phase 3 terminée.")

if __name__ == "__main__":
    run_topology()
