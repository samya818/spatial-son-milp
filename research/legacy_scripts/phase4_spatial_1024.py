import numpy as np
import polars as pl
import json
import yaml
from pathlib import Path

# --- CONFIGURATION ---
GRID_SIZE = 100
PL_EXP = 3.76
DELTA_LEVELS = [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0]

class SpatialTransferSimulator:
    def __init__(self, grid_resolution=30, pl_exp=3.76, grid_size=100):
        self.grid = grid_resolution
        self.pl_exp = pl_exp
        self.grid_size = grid_size

    def precompute_offline(self, coverage, antennas, neighbors, delta_levels):
        records = []
        total_masters = len(coverage)
        curr_master = 0
        
        for master_id, cell_list in coverage.items():
            curr_master += 1
            if curr_master % 20 == 0:
                print(f"Traitement Antenne {curr_master}/{total_masters}...")
                
            ax = antennas[master_id]['x']
            ay = antennas[master_id]['y']
            voisines = neighbors.get(master_id, [])
            
            for square_id in cell_list:
                square_id = int(square_id)
                row = (square_id - 1) // self.grid_size
                col = (square_id - 1) %  self.grid_size
                
                # Discrétisation
                xs = np.linspace(col, col + 1, self.grid)
                ys = np.linspace(row, row + 1, self.grid)
                X, Y = np.meshgrid(xs, ys)
                
                Q_master = -self.pl_exp * np.log10(np.hypot(X - ax, Y - ay) + 1e-6)
                
                if not voisines:
                    for k, delta in enumerate(delta_levels):
                        records.append({
                            'square_id': square_id, 'master_id': master_id,
                            'target_ant': master_id, 'delta_level': k,
                            'delta_dB': delta, 'fraction': 1.0
                        })
                    continue

                best_Q = np.full_like(Q_master, -np.inf)
                best_voisine = np.full(Q_master.shape, '', dtype=object)
                
                for b_id in voisines:
                    bx = antennas[b_id]['x']
                    by = antennas[b_id]['y']
                    Q_b = -self.pl_exp * np.log10(np.hypot(X - bx, Y - by) + 1e-6)
                    mask = Q_b > best_Q
                    best_Q = np.where(mask, Q_b, best_Q)
                    best_voisine = np.where(mask, b_id, best_voisine)
                
                delta_crit = Q_master - best_Q
                
                for k, delta in enumerate(delta_levels):
                    switch_mask = (delta >= delta_crit) & (best_voisine != '')
                    frac_stays = float(np.mean(~switch_mask))
                    records.append({
                        'square_id': square_id, 'master_id': master_id,
                        'target_ant': master_id, 'delta_level': k,
                        'delta_dB': delta, 'fraction': frac_stays
                    })
                    
                    for b_id in voisines:
                        frac_b = float(np.mean(switch_mask & (best_voisine == b_id)))
                        if frac_b > 0:
                            records.append({
                                'square_id': square_id, 'master_id': master_id,
                                'target_ant': b_id, 'delta_level': k,
                                'delta_dB': delta, 'fraction': frac_b
                            })
                            
        return pl.DataFrame(records)

def run_spatial():
    print("Chargement de la topologie Bloc 1024...")
    with open('config/network_topology_1024.yaml', 'r') as f:
        topology = yaml.safe_load(f)
    antennas = topology['antennas']

    with open('data/processed/cell_antenna_map_1024.json', 'r') as f:
        coverage_1024 = json.load(f)

    with open('data/processed/neighbor_graph_1024.json', 'r') as f:
        neighbor_graph = json.load(f)

    print("Précalcul des fractions...")
    sim = SpatialTransferSimulator(grid_resolution=30, pl_exp=PL_EXP, grid_size=GRID_SIZE)
    fractions_df = sim.precompute_offline(coverage_1024, antennas, neighbor_graph, DELTA_LEVELS)

    output_path = Path('offline/fractions_1024.parquet')
    fractions_df.write_parquet(output_path)
    print(f"Précalcul terminé: {len(fractions_df)} lignes dans {output_path}")

if __name__ == "__main__":
    run_spatial()
