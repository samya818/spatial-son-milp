"""
WiseNet V1.5 - Topology Builder (3GPP Hexagonal Grid + Sectors + Dual Carriers)
Architecture réaliste conforme aux déploiements TIM Italy & standards 3GPP TR 38.901 :
- Grille hexagonale 3GPP déterministe avec Inter-Site Distance (ISD) = 750 m
- 3 secteurs par site (azimut 0°, 120°, 240°, ouverture 65°)
- 2 porteuses réelles :
    * F1 : 1.8 GHz (LTE Band 3 FDD) — 20 MHz, P_tx=43 dBm (20W), SINR=12 dB
    * F2 : 3.5 GHz (5G NR n78 TDD)  — 80 MHz, P_tx=43 dBm (20W eff.), SINR=15 dB
- Cellule radio élémentaire = couple (secteur, porteuse) (s, f)
"""

import numpy as np
import json
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# --- CONSTANTES GÉOGRAPHIQUES & PHYSIQUES MILAN ---
GRID_SIZE = 100
CELL_SIZE_METERS = 235.0  # Taille d'une maille Telecom Italia Milan (235m x 235m)

# Profils par porteuse (Spectre & Puissance TIM Italy)
CARRIER_PROFILES = {
    'F1_1800': {
        'freq_ghz': 1.8,
        'bw_mhz': 20.0,              # Licence TIM Italy Band 3 FDD (20 MHz)
        'tx_power_dBm': 43.0,         # Ericsson AIR 3246 macro nominal (20W)
        'sinr_target_db': 12.0,       # 3GPP TR 38.901 Dense Urban UMa
        'description': 'Couverture Macro LTE Band 3 (1.8 GHz)'
    },
    'F2_3500': {
        'freq_ghz': 3.5,
        'bw_mhz': 80.0,              # Licence TIM Italy n78 5G NR TDD (80 MHz)
        'tx_power_dBm': 43.0,         # Ericsson AIR 6449 nominal effectif par secteur (3GPP §7.8)
        'sinr_target_db': 15.0,       # 3GPP TR 38.901 Dense Urban UMi 5G
        'description': 'Haute Capacité 5G NR n78 (3.5 GHz)'
    }
}

SECTOR_AZIMUTHS = [0.0, 120.0, 240.0]  # Standard tri-secteur 120°

def calculate_cell_capacity_mo(
    bw_mhz: float,
    sinr_db: float,
    duration_s: int = 1800,
    spectral_eff: float = 0.6,
    utilization: float = 0.6
) -> float:
    """
    Calcule la capacité opérationnelle en Mo (Mégaoctets) sur une fenêtre de 30 minutes (1800s)
    selon la formule de Shannon pondérée 3GPP.
    """
    bw_hz = bw_mhz * 1e6
    sinr_lin = 10.0 ** (sinr_db / 10.0)
    cap_bps = bw_hz * np.log2(1.0 + sinr_lin) * spectral_eff
    volume_mo = (cap_bps * duration_s * utilization) / (8.0 * 1e6)
    return round(float(volume_mo), 1)

class TopologyBuilderV15:
    """
    Constructeur de topologie 3GPP réaliste : Grille hexagonale déterministe avec tri-secteurs & multi-porteuses.
    """
    def __init__(self, isd_meters: float = 750.0):
        self.isd = isd_meters

    def generate_hexagonal_topology(
        self,
        row_range=(35, 67),
        col_range=(35, 67),
        cell_size_meters: float = CELL_SIZE_METERS
    ) -> dict:
        """
        Génère une grille hexagonale régulière de sites 3GPP sur le bloc géographique défini.
        """
        r0, r1 = row_range
        c0, c1 = col_range
        
        # Dimensions physiques de la zone (en mètres)
        x_min = c0 * cell_size_meters
        x_max = c1 * cell_size_meters
        y_min = r0 * cell_size_meters
        y_max = r1 * cell_size_meters
        
        # Pas de la grille hexagonale
        dx = self.isd
        dy = self.isd * np.sqrt(3) / 2.0
        
        sites = {}
        site_idx = 0
        
        # Génération des positions hexagonales avec offset alterné par ligne
        row_hex = 0
        y = y_min + dy / 2.0
        while y < y_max + dy / 2.0:
            x_offset = (dx / 2.0) if (row_hex % 2 == 1) else 0.0
            x = x_min + dx / 2.0 + x_offset - dx  # Marge de sécurité
            while x < x_max + dx:
                if (x_min <= x <= x_max) and (y_min <= y <= y_max):
                    site_id = f"site_{site_idx:03d}"
                    row_grid = y / cell_size_meters
                    col_grid = x / cell_size_meters
                    
                    # Construction des secteurs et cellules radio (s, f)
                    sectors = {}
                    for sec_idx, azimuth in enumerate(SECTOR_AZIMUTHS):
                        sector_id = f"{site_id}_sec{sec_idx+1}"
                        carrier_cells = {}
                        
                        for carrier_name, c_prof in CARRIER_PROFILES.items():
                            cell_id = f"{sector_id}_{carrier_name}"
                            tx_pwr = c_prof['tx_power_dBm']
                            cap_mo = calculate_cell_capacity_mo(c_prof['bw_mhz'], c_prof['sinr_target_db'])
                            
                            carrier_cells[carrier_name] = {
                                'cell_id': cell_id,
                                'freq_ghz': c_prof['freq_ghz'],
                                'bw_mhz': c_prof['bw_mhz'],
                                'tx_power_dBm': tx_pwr,
                                'capacity_mo': cap_mo,
                                'sinr_target_db': c_prof['sinr_target_db']
                            }
                            
                        sectors[sector_id] = {
                            'sector_id': sector_id,
                            'azimuth_deg': azimuth,
                            'beamwidth_deg': 65.0,  # 3GPP standard 65°
                            'carriers': carrier_cells
                        }
                    
                    sites[site_id] = {
                        'site_id': site_id,
                        'site_type': 'macro',
                        'row': float(row_grid),
                        'col': float(col_grid),
                        'x_meters': float(x),
                        'y_meters': float(y),
                        'sectors': sectors
                    }
                    site_idx += 1
                x += dx
            y += dy
            row_hex += 1
            
        logger.info(f"[V1.5 Hex] Topologie hexagonale générée: {len(sites)} sites (ISD={self.isd}m), {len(sites)*3} secteurs, {len(sites)*6} cellules radio (s, f).")
        return sites

    def generate_topology(self, row_range=(35, 67), col_range=(35, 67), density: float = None) -> dict:
        """Méthode principale par défaut qui appelle la grille hexagonale 3GPP."""
        return self.generate_hexagonal_topology(row_range=row_range, col_range=col_range)

if __name__ == "__main__":
    builder = TopologyBuilderV15(isd_meters=750.0)
    topo = builder.generate_hexagonal_topology(row_range=(35, 67), col_range=(35, 67))
    print(f"Sites generes sur bloc 1024 mailles: {len(topo)}")
    first_site = list(topo.values())[0]
    print(f"Exemple site: {first_site['site_id']} a (x={first_site['x_meters']:.0f}m, y={first_site['y_meters']:.0f}m)")
    for sec_id, sec_data in first_site['sectors'].items():
        print(f"  -> Secteur {sec_id} (Azimuth {sec_data['azimuth_deg']} deg)")
        for c_name, c_data in sec_data['carriers'].items():
            print(f"       Cellule {c_data['cell_id']} : Freq={c_data['freq_ghz']} GHz, BW={c_data['bw_mhz']} MHz, P_tx={c_data['tx_power_dBm']} dBm, Capacite={c_data['capacity_mo']} Mo")
