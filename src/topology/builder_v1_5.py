"""
WiseNet V1.5 - Topology Builder (Sectors + Carriers)
Architecture conforme 3GPP gNodeB 5G / eNodeB LTE:
- 3 secteurs par site (azimut 0°, 120°, 240°)
- 2 porteuses fréquentielles: F1 (1.8 GHz - Couverture) et F2 (3.5 GHz - Haute Capacité)
- Chaque unité de ressource est une cellule radio (secteur, porteuse) (s, f)
"""

import numpy as np
import json
from pathlib import Path
from scipy.spatial import cKDTree
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

# --- CONFIGURATION V1.5 ---
GRID_SIZE = 100
CELL_SIZE_METERS = 235.0  # 235m x 235m par maille Milan
SEED = 42

# Profils par porteuse (F1 = 1.8 GHz, F2 = 3.5 GHz)
CARRIER_PROFILES = {
    'F1_1800': {
        'freq_ghz': 1.8,
        'bw_mhz': 20.0,
        'macro_tx_power_dBm': 46.0,  # 40W
        'micro_tx_power_dBm': 37.0,  # 5W
        'sinr_target_db': 15.0,
        'description': 'Couverture Macro & Mobilité générale'
    },
    'F2_3500': {
        'freq_ghz': 3.5,
        'bw_mhz': 60.0,              # Large bande 5G Mid-band
        'macro_tx_power_dBm': 43.0,  # 20W
        'micro_tx_power_dBm': 30.0,  # 1W
        'sinr_target_db': 20.0,
        'description': 'Très Haut Débit / Haute Capacité'
    }
}

SECTOR_AZIMUTHS = [0.0, 120.0, 240.0]  # 3 secteurs à 120 degrés

def calculate_cell_capacity_mo(bw_mhz: float, sinr_db: float, duration_s: int = 1800, spectral_eff: float = 0.6, utilization: float = 0.6) -> float:
    """
    Calcule la capacité opérationnelle en Mo (Mégaoctets) sur une fenêtre de 30 minutes (1800s)
    selon la formule de Shannon pondérée.
    """
    bw_hz = bw_mhz * 1e6
    sinr_lin = 10.0 ** (sinr_db / 10.0)
    cap_bps = bw_hz * np.log2(1.0 + sinr_lin) * spectral_eff
    volume_mo = (cap_bps * duration_s * utilization) / (8.0 * 1e6)
    return round(volume_mo, 1)

class TopologyBuilderV15:
    """
    Constructeur de topologie 4G/5G réaliste multi-secteurs et multi-fréquences.
    """
    def __init__(self, seed: int = SEED):
        self.rng = np.random.default_rng(seed)

    def generate_topology(self, row_range=(35, 67), col_range=(35, 67), density: float = 0.22) -> dict:
        """
        Génère une topologie de sites physiques avec secteurs et porteuses sur le bloc 1024 cellules.
        """
        r0, r1 = row_range
        c0, c1 = col_range
        area = (r1 - r0) * (c1 - c0)
        n_sites = int(area * density)
        
        logger.info(f"[V1.5] Génération de {n_sites} sites physiques sur {area} mailles...")
        
        sites = {}
        placed_positions = []
        site_types_proba = {'macro': 0.35, 'micro': 0.65}
        
        site_idx = 0
        for _ in range(n_sites * 2):
            if site_idx >= n_sites:
                break
            
            r = self.rng.uniform(r0, r1)
            c = self.rng.uniform(c0, c1)
            
            # Distance minimale entre sites (évite superposition irréaliste)
            if any(np.hypot(r - pr, c - pc) < 0.6 for pr, pc in placed_positions):
                continue
            
            placed_positions.append((r, c))
            site_id = f"site_{site_idx:03d}"
            site_type = self.rng.choice(list(site_types_proba.keys()), p=list(site_types_proba.values()))
            
            # Construction des secteurs et cellules radio (s, f)
            sectors = {}
            for sec_idx, azimuth in enumerate(SECTOR_AZIMUTHS):
                sector_id = f"{site_id}_sec{sec_idx+1}"
                carrier_cells = {}
                
                for carrier_name, c_prof in CARRIER_PROFILES.items():
                    cell_id = f"{sector_id}_{carrier_name}"
                    tx_pwr = c_prof['macro_tx_power_dBm'] if site_type == 'macro' else c_prof['micro_tx_power_dBm']
                    capacity_mo = calculate_cell_capacity_mo(c_prof['bw_mhz'], c_prof['sinr_target_db'])
                    
                    carrier_cells[carrier_name] = {
                        'cell_id': cell_id,
                        'freq_ghz': c_prof['freq_ghz'],
                        'bw_mhz': c_prof['bw_mhz'],
                        'tx_power_dBm': tx_pwr,
                        'capacity_mo': capacity_mo,
                        'sinr_target_db': c_prof['sinr_target_db']
                    }
                
                sectors[sector_id] = {
                    'sector_id': sector_id,
                    'azimuth_deg': azimuth,
                    'beamwidth_deg': 65.0,  # Ouverture standard 3GPP 65°
                    'carriers': carrier_cells
                }
            
            sites[site_id] = {
                'site_id': site_id,
                'site_type': site_type,
                'row': float(r),
                'col': float(c),
                'x_meters': float(c * CELL_SIZE_METERS),
                'y_meters': float(r * CELL_SIZE_METERS),
                'sectors': sectors
            }
            site_idx += 1
            
        logger.info(f"[V1.5] Topologie créée: {len(sites)} sites, {len(sites)*3} secteurs, {len(sites)*6} cellules radio logiques (s, f).")
        return sites

if __name__ == "__main__":
    builder = TopologyBuilderV15()
    topo = builder.generate_topology()
    first_site = list(topo.values())[0]
    print(f"Exemple de site généré: {first_site['site_id']} ({first_site['site_type']})")
    for sec_id, sec_data in first_site['sectors'].items():
        print(f"  -> {sec_id} (Azimuth {sec_data['azimuth_deg']}°)")
        for c_name, c_data in sec_data['carriers'].items():
            print(f"       Cellule {c_data['cell_id']} : Freq={c_data['freq_ghz']} GHz, BW={c_data['bw_mhz']} MHz, Capacité={c_data['capacity_mo']} Mo")
