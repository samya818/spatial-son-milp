"""
WiseNet V1.5 - Spatial Transfer Simulator (3GPP RSRP with Sectors & Carriers)
- Modèle 3GPP UMi Path-Loss dépendant de la fréquence (f_GHz)
- Diagramme d'antenne sectoriel 3GPP (3 secteurs 120°, ouverture 65°)
- Calcul point par point du RSRP (Reference Signal Received Power)
- Matrices de transfert par cellule radio élémentaire (secteur, porteuse) (s, f)
"""

import numpy as np
import json
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class SpatialTransferSimulatorV15:
    """
    Simulateur de propagation radio RSRP 3GPP vectorisé multi-secteurs et multi-porteuses.
    """
    def __init__(self, grid_resolution: int = 30, cell_size_meters: float = 235.0, delta_levels: list[float] = None):
        self.res = grid_resolution
        self.cell_size = cell_size_meters
        self.delta_levels = delta_levels or [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0]

    @staticmethod
    def antenna_gain_3gpp(theta_deg: np.ndarray, azimuth_deg: float, beamwidth_deg: float = 65.0, max_att_db: float = 30.0) -> np.ndarray:
        """
        Gain d'antenne directionnel 3GPP TR 38.901 :
        G(d_theta) = -min(12 * (d_theta / beamwidth)^2, max_att_db)
        """
        diff = np.abs(theta_deg - azimuth_deg) % 360.0
        delta_theta = np.where(diff > 180.0, 360.0 - diff, diff)
        attenuation = np.minimum(12.0 * ((delta_theta / beamwidth_deg) ** 2), max_att_db)
        return -attenuation

    @staticmethod
    def path_loss_3gpp_umi(dist_meters: np.ndarray, freq_ghz: float) -> np.ndarray:
        """
        Affaiblissement de parcours 3GPP UMi (Urban Micro) NLOS :
        PL(d, f) = 32.4 + 36.7 * log10(d) + 20 * log10(f)
        """
        d_safe = np.maximum(dist_meters, 5.0)  # Distance minimale 5m
        return 32.4 + 36.7 * np.log10(d_safe) + 20.0 * np.log10(freq_ghz)

    def compute_rsrp_field(self, X_m: np.ndarray, Y_m: np.ndarray, site_x: float, site_y: float, azimuth_deg: float, freq_ghz: float, tx_power_dbm: float) -> np.ndarray:
        """
        Calcule le RSRP reçu en chaque point (X, Y) pour une cellule radio (secteur, porteuse).
        RSRP = P_tx - PL(d, f) + G(d_theta)
        """
        dx = X_m - site_x
        dy = Y_m - site_y
        dist = np.hypot(dx, dy)
        
        # Angle géographique par rapport au Nord (0° Nord, sens horaire)
        angle_deg = (np.degrees(np.arctan2(dx, dy)) + 360.0) % 360.0
        
        gain = self.antenna_gain_3gpp(angle_deg, azimuth_deg)
        pl = self.path_loss_3gpp_umi(dist, freq_ghz)
        
        return tx_power_dbm - pl + gain

    def compute_transfer_fractions(self, cell_squares: list[int], topology: dict, grid_size: int = 100) -> dict:
        """
        Précalcule les fractions de transfert de trafic pour chaque cellule géographique et chaque niveau d'offset.
        """
        logger.info(f"[V1.5 Spatial] Précalcul des matrices RSRP sur {len(cell_squares)} mailles...")
        results = {}
        
        # Construction de la liste des cellules radio disponibles
        radio_cells = []
        for site_id, s_data in topology.items():
            sx, sy = s_data['x_meters'], s_data['y_meters']
            for sec_id, sec_data in s_data['sectors'].items():
                azimuth = sec_data['azimuth_deg']
                for c_name, c_data in sec_data['carriers'].items():
                    radio_cells.append({
                        'cell_id': c_data['cell_id'],
                        'site_id': site_id,
                        'sector_id': sec_id,
                        'carrier_name': c_name,
                        'freq_ghz': c_data['freq_ghz'],
                        'tx_power_dBm': c_data['tx_power_dBm'],
                        'azimuth_deg': azimuth,
                        'site_x': sx,
                        'site_y': sy
                    })

        for sq_id in cell_squares:
            row = (sq_id - 1) // grid_size
            col = (sq_id - 1) % grid_size
            
            # Grille fine de points dans la maille (en mètres)
            xs = np.linspace(col * self.cell_size, (col + 1) * self.cell_size, self.res)
            ys = np.linspace(row * self.cell_size, (row + 1) * self.cell_size, self.res)
            X, Y = np.meshgrid(xs, ys)
            
            # Calcul du RSRP de chaque cellule radio sur cette maille
            rsrp_maps = {}
            for rc in radio_cells:
                # Filtrer les sites trop éloignés (> 3km) pour vitesse
                site_dist = np.hypot((col + 0.5)*self.cell_size - rc['site_x'], (row + 0.5)*self.cell_size - rc['site_y'])
                if site_dist > 2500.0:
                    continue
                
                rsrp = self.compute_rsrp_field(
                    X, Y, rc['site_x'], rc['site_y'], 
                    rc['azimuth_deg'], rc['freq_ghz'], rc['tx_power_dBm']
                )
                rsrp_maps[rc['cell_id']] = rsrp
                
            if not rsrp_maps:
                continue
                
            # Cellule maîtresse = cellule radio avec le meilleur RSRP moyen
            best_master = max(rsrp_maps.keys(), key=lambda k: np.mean(rsrp_maps[k]))
            master_rsrp = rsrp_maps[best_master]
            
            # Recherche de la meilleure cellule voisine pour chaque point
            other_cells = [k for k in rsrp_maps.keys() if k != best_master]
            if not other_cells:
                continue
                
            best_neighbor_rsrp = np.full_like(master_rsrp, -np.inf)
            best_neighbor_id = np.full(master_rsrp.shape, '', dtype=object)
            
            for oc in other_cells:
                oc_rsrp = rsrp_maps[oc]
                mask = oc_rsrp > best_neighbor_rsrp
                best_neighbor_rsrp = np.where(mask, oc_rsrp, best_neighbor_rsrp)
                best_neighbor_id = np.where(mask, oc, best_neighbor_id)
                
            # Calcul des fractions pour chaque niveau d'offset
            square_fractions = {}
            delta_crit = master_rsrp - best_neighbor_rsrp
            
            for delta in self.delta_levels:
                switch_mask = (delta >= delta_crit) & (best_neighbor_id != '')
                frac_stays = float(np.mean(~switch_mask))
                
                transfers = {'stays': frac_stays, 'target_cells': {}}
                for oc in other_cells:
                    f_target = float(np.mean(switch_mask & (best_neighbor_id == oc)))
                    if f_target > 0.001:
                        transfers['target_cells'][oc] = round(f_target, 4)
                        
                square_fractions[str(delta)] = transfers
                
            results[str(sq_id)] = {
                'master_cell': best_master,
                'offsets': square_fractions
            }
            
        logger.info(f"[V1.5 Spatial] Matrices calculées pour {len(results)} mailles avec succès.")
        return results

if __name__ == "__main__":
    from src.topology.builder_v1_5 import TopologyBuilderV15
    builder = TopologyBuilderV15()
    topo = builder.generate_topology(row_range=(48, 52), col_range=(48, 52), density=0.25)
    
    # Test sur un petit bloc de 16 cellules (4x4)
    squares = [r * 100 + c + 1 for r in range(48, 52) for c in range(48, 52)]
    sim = SpatialTransferSimulatorV15(grid_resolution=20)
    fractions = sim.compute_transfer_fractions(squares, topo)
    
    print(f"Exemple de fraction précalculée pour maille {squares[0]}:")
    first_sq = fractions.get(str(squares[0]))
    if first_sq:
        print(f"  Master Radio Cell: {first_sq['master_cell']}")
        for d, t_data in first_sq['offsets'].items():
            print(f"  Offset {d} dB -> Reste sur master: {t_data['stays']*100:.1f}%, Délesté: {list(t_data['target_cells'].keys())}")
