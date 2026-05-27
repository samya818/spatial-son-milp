import numpy as np
import json
import yaml
import polars as pl
from pathlib import Path
from scipy.spatial import cKDTree
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

# --- CONFIGURATION ---
GRID_SIZE = 100
SEED = 42
rng = np.random.default_rng(SEED)

ANTENNA_PROFILES = {
    'macro':     {'bw_mhz': 20, 'sinr_db': 15, 'tx_power_dBm': 46, 'height_m': 25, 'coverage_radius_grid': 3.5},
    'micro':     {'bw_mhz': 20, 'sinr_db': 20, 'tx_power_dBm': 37, 'height_m': 8,  'coverage_radius_grid': 0.9},
    'smallcell': {'bw_mhz': 10, 'sinr_db': 25, 'tx_power_dBm': 24, 'height_m': 4,  'coverage_radius_grid': 0.2},
}

def capacity_from_radio(bw_mhz, sinr_db, spectral_eff=0.6, utilization=0.6, duration_s=1800):
    bw_hz     = bw_mhz * 1e6
    sinr_lin  = 10 ** (sinr_db / 10)
    cap_bps   = bw_hz * np.log2(1 + sinr_lin) * spectral_eff
    volume_mo = (cap_bps * duration_s * utilization) / (8 * 1e6)
    return round(volume_mo, 1)

class TopologyBuilder:
    def __init__(self, rng=rng):
        self.rng = rng

    def generate_bloc_topology(self, row_range=(35, 67), col_range=(35, 67), density=0.22):
        """
        Génère une topologie d'antennes hétérogènes pour un bloc géographique.
        """
        antennas = {}
        idx = 0
        placed_positions = []
        type_proba = {'macro': 0.3, 'micro': 0.45, 'smallcell': 0.25}
        
        r0, r1 = row_range
        c0, c1 = col_range
        area = (r1 - r0) * (c1 - c0)
        n_ant = int(area * density)
        
        logger.info(f"Generating {n_ant} antennas for {area} cells...")
        
        for _ in range(n_ant):
            r = self.rng.uniform(r0, r1)
            c = self.rng.uniform(c0, c1)
            
            if any(np.hypot(r-pr, c-pc) < 0.5 for pr, pc in placed_positions):
                continue
            
            ant_type = self.rng.choice(list(type_proba.keys()), p=list(type_proba.values()))
            profile = ANTENNA_PROFILES[ant_type]
            
            base_capacity = capacity_from_radio(profile['bw_mhz'], profile['sinr_db'])
            capacity_mo = float(base_capacity * (1 + self.rng.normal(0, 0.1)))
            
            antennas[f'A{idx:03d}'] = {
                'x': float(c), 'y': float(r), 'type': str(ant_type),
                'capacity_mo': float(round(capacity_mo, 1)),
                'bw_mhz': int(profile['bw_mhz']), 'sinr_db': int(profile['sinr_db']),
                'coverage_radius': float(profile['coverage_radius_grid']),
            }
            placed_positions.append((r, c)); idx += 1
        return antennas

    def build_neighbor_graph(self, antennas, threshold=8.0):
        if not antennas: return {}
        ant_ids = list(antennas.keys())
        coords = np.array([[antennas[a]['y'], antennas[a]['x']] for a in ant_ids])
        tree = cKDTree(coords)
        neighbors = {}
        for i, a_id in enumerate(ant_ids):
            idx_neighbors = tree.query_ball_point(coords[i], r=threshold)
            neighbors[a_id] = [ant_ids[j] for j in idx_neighbors if ant_ids[j] != a_id]
        return neighbors

    def assign_cells(self, antennas, row_range=(35, 67), col_range=(35, 67)):
        if not antennas: return {}
        cells = [(i, j) for i in range(row_range[0], row_range[1]) 
                         for j in range(col_range[0], col_range[1])]
        cell_centers = np.array([(i + 0.5, j + 0.5) for i, j in cells])
        ant_ids = list(antennas.keys())
        ant_coords = np.array([[antennas[a]['y'], antennas[a]['x']] for a in ant_ids])
        tree = cKDTree(ant_coords)
        _, nearest_idx = tree.query(cell_centers, k=1)
        
        coverage = defaultdict(list)
        for (i, j), ant_idx in zip(cells, nearest_idx):
            square_id = i * 100 + j + 1
            coverage[ant_ids[ant_idx]].append(int(square_id))
        return dict(coverage)
