import numpy as np
import polars as pl
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class SpatialTransferSimulator:
    """
    Simulateur de transfert spatial radio pour 4G/LTE.
    Calcule les fractions de trafic délesté en fonction des offsets A3 (delta_dB).
    """
    def __init__(self, grid_resolution: int = 30, pl_exp: float = 3.76, grid_size: int = 100):
        self.grid = grid_resolution
        self.pl_exp = pl_exp
        self.grid_size = grid_size

    def precompute_offline(self, coverage: dict, antennas: dict, neighbors: dict, delta_levels: list[float]) -> pl.DataFrame:
        """
        Précalcule la matrice de transfert (fractions) pour un cluster donné.
        """
        records = []
        total_masters = len(coverage)
        curr_master = 0
        
        for master_id, cell_list in coverage.items():
            curr_master += 1
            if curr_master % 50 == 0:
                logger.info(f"Processing Antenna {curr_master}/{total_masters}...")
                
            ax, ay = antennas[master_id]['x'], antennas[master_id]['y']
            voisines = neighbors.get(master_id, [])
            
            for square_id in cell_list:
                square_id = int(square_id)
                row, col = (square_id - 1) // self.grid_size, (square_id - 1) %  self.grid_size
                
                # Discrétisation spatiale de la cellule
                xs = np.linspace(col, col + 1, self.grid)
                ys = np.linspace(row, row + 1, self.grid)
                X, Y = np.meshgrid(xs, ys)
                
                # Atténuation vers le maître
                Q_master = -self.pl_exp * np.log10(np.hypot(X - ax, Y - ay) + 1e-6)
                
                if not voisines:
                    for delta in delta_levels:
                        records.append({
                            'square_id': square_id, 'master_id': master_id,
                            'target_ant': master_id, 'delta_dB': delta, 'fraction': 1.0
                        })
                    continue

                # Recherche du meilleur voisin pour chaque point de la grille
                best_Q = np.full_like(Q_master, -np.inf)
                best_voisine = np.full(Q_master.shape, '', dtype=object)
                
                for b_id in voisines:
                    bx, by = antennas[b_id]['x'], antennas[b_id]['y']
                    Q_b = -self.pl_exp * np.log10(np.hypot(X - bx, Y - by) + 1e-6)
                    mask = Q_b > best_Q
                    best_Q = np.where(mask, Q_b, best_Q)
                    best_voisine = np.where(mask, b_id, best_voisine)
                
                # Critère de délestage : Q_master + delta < Q_neighbor => switch
                delta_crit = Q_master - best_Q
                
                for delta in delta_levels:
                    switch_mask = (delta >= delta_crit) & (best_voisine != '')
                    frac_stays = float(np.mean(~switch_mask))
                    records.append({
                        'square_id': square_id, 'master_id': master_id,
                        'target_ant': master_id, 'delta_dB': delta, 'fraction': frac_stays
                    })
                    
                    for b_id in voisines:
                        frac_b = float(np.mean(switch_mask & (best_voisine == b_id)))
                        if frac_b > 0:
                            records.append({
                                'square_id': square_id, 'master_id': master_id,
                                'target_ant': b_id, 'delta_dB': delta, 'fraction': frac_b
                            })
                            
        return pl.DataFrame(records)
