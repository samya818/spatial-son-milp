import math
import numpy as np
import polars as pl
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import pydeck as pdk

from src.topology.builder_v1_5 import TopologyBuilderV15, CELL_SIZE_METERS, CARRIER_PROFILES, SECTOR_AZIMUTHS

logger = logging.getLogger(__name__)

# Milan center coordinates for the 32x32 block centered in 100x100 grid
CENTER_LAT = 45.4642
CENTER_LON = 9.1900
CENTER_X = (35 + 16) * CELL_SIZE_METERS
CENTER_Y = (35 + 16) * CELL_SIZE_METERS
M_PER_DEG_LAT = 111132.95
M_PER_DEG_LON = 111132.95 * 0.7013

def get_sector_polygon(lon: float, lat: float, azimuth_deg: float, radius_m: float = 280.0, beamwidth_deg: float = 65.0, num_pts: int = 8) -> List[List[float]]:
    half_bw = beamwidth_deg / 2.0
    angles = np.linspace(azimuth_deg - half_bw, azimuth_deg + half_bw, num_pts)
    coords = [[round(lon, 6), round(lat, 6)]]
    for ang in angles:
        rad = math.radians(ang)
        dx = radius_m * math.sin(rad)
        dy = radius_m * math.cos(rad)
        p_lat = lat + (dy / M_PER_DEG_LAT)
        p_lon = lon + (dx / M_PER_DEG_LON)
        coords.append([round(p_lon, 6), round(p_lat, 6)])
    coords.append([round(lon, 6), round(lat, 6)])
    return coords

class HexMapEngine:
    """Generates 3GPP hexagonal site & sector map data with dual-frequency toggle."""
    
    def __init__(self, isd_meters: float = 750.0):
        self.builder = TopologyBuilderV15(isd_meters=isd_meters)
        self.topology = self.builder.generate_hexagonal_topology(row_range=(35, 67), col_range=(35, 67))
        self.sectors_meta = self._build_sectors_meta()
        
    def _build_sectors_meta(self) -> List[Dict[str, Any]]:
        sectors = []
        for s_id, s_data in self.topology.items():
            dx = s_data['x_meters'] - CENTER_X
            dy = s_data['y_meters'] - CENTER_Y
            s_lat = round(CENTER_LAT + (dy / M_PER_DEG_LAT), 6)
            s_lon = round(CENTER_LON + (dx / M_PER_DEG_LON), 6)
            
            for sec_id, sec in s_data['sectors'].items():
                az = sec['azimuth_deg']
                poly = get_sector_polygon(s_lon, s_lat, az, radius_m=320.0, beamwidth_deg=65.0)
                c_f1 = sec['carriers']['F1_1800']['cell_id']
                c_f2 = sec['carriers']['F2_3500']['cell_id']
                cap_f1 = sec['carriers']['F1_1800']['capacity_mo']
                cap_f2 = sec['carriers']['F2_3500']['capacity_mo']
                
                # Arc midpoint for label / centroid
                rad = math.radians(az)
                centroid_lat = s_lat + (180.0 * math.cos(rad) / M_PER_DEG_LAT)
                centroid_lon = s_lon + (180.0 * math.sin(rad) / M_PER_DEG_LON)
                
                sectors.append({
                    'site_id': s_id,
                    'sector_id': sec_id,
                    'site_lat': s_lat,
                    'site_lon': s_lon,
                    'centroid_lat': round(centroid_lat, 6),
                    'centroid_lon': round(centroid_lon, 6),
                    'azimuth_deg': az,
                    'polygon': poly,
                    'f1_cell_id': c_f1,
                    'f2_cell_id': c_f2,
                    'cap_f1_mo': cap_f1,
                    'cap_f2_mo': cap_f2,
                    'total_cap_mo': cap_f1 + cap_f2
                })
        return sectors

    def get_layer_data(
        self, 
        frequency: str = "ALL", 
        policy: str = "milp", 
        loads_dict: Optional[Dict[str, float]] = None,
        offsets_dict: Optional[Dict[str, float]] = None,
        stress_factor: float = 1.0
    ) -> List[Dict[str, Any]]:
        """
        Builds polygon records with real-time color coding according to congestion level.
        Green = < 75%, Amber = 75-100%, Red = > 100% (congested / saturated)
        """
        records = []
        loads = loads_dict or {}
        offsets = offsets_dict or {}
        
        for sec in self.sectors_meta:
            cap_f1 = sec['cap_f1_mo'] * stress_factor
            cap_f2 = sec['cap_f2_mo'] * stress_factor
            load_f1 = loads.get(sec['f1_cell_id'], 0.0)
            load_f2 = loads.get(sec['f2_cell_id'], 0.0)
            offset_applied = offsets.get(sec['f1_cell_id'], 0.0)
            
            if frequency == "F1_1800":
                cell_id = sec['f1_cell_id']
                cap = cap_f1
                load = load_f1
                load_pct = (load / cap * 100.0) if cap > 0 else 0.0
            elif frequency == "F2_3500":
                cell_id = sec['f2_cell_id']
                cap = cap_f2
                load = load_f2
                load_pct = (load / cap * 100.0) if cap > 0 else 0.0
            else: # ALL / COMBINED Dual-Carrier
                cell_id = f"{sec['sector_id']}_BOTH"
                cap = cap_f1 + cap_f2
                load = load_f1 + load_f2
                # In dual carrier, if F1 is congested (> 100%), the carrier bottleneck dominates:
                pct_f1 = (load_f1 / cap_f1 * 100.0) if cap_f1 > 0 else 0.0
                pct_f2 = (load_f2 / cap_f2 * 100.0) if cap_f2 > 0 else 0.0
                pct_comb = (load / cap * 100.0) if cap > 0 else 0.0
                load_pct = max(pct_comb, max(pct_f1, pct_f2))
                
            residual_mo = max(0.0, load - cap) if frequency != "ALL" else (max(0.0, load_f1 - cap_f1) + max(0.0, load_f2 - cap_f2))
            
            # Color logic based on saturation
            if load_pct > 100.0:
                # Saturated / Red
                excess = min(100.0, load_pct - 100.0)
                alpha = int(170 + (excess / 100.0) * 70)
                color = [239, 68, 68, min(240, alpha)]
                status = "CRITICAL (Congested)"
            elif load_pct >= 75.0:
                # Warning / Amber
                color = [245, 158, 11, 190]
                status = "HIGH LOAD (Warning)"
            else:
                # Optimal / Green
                alpha = int(100 + (load_pct / 75.0) * 80)
                color = [0, 212, 170, max(90, alpha)]
                status = "NOMINAL (Balanced)"
                
            records.append({
                'site_id': sec['site_id'],
                'sector_id': sec['sector_id'],
                'cell_id': cell_id,
                'frequency': frequency,
                'azimuth': sec['azimuth_deg'],
                'polygon': sec['polygon'],
                'centroid_lat': sec['centroid_lat'],
                'centroid_lon': sec['centroid_lon'],
                'site_lat': sec['site_lat'],
                'site_lon': sec['site_lon'],
                'load_mo': round(load, 1),
                'capacity_mo': round(cap, 1),
                'load_f1_mo': round(load_f1, 1),
                'load_f2_mo': round(load_f2, 1),
                'cap_f1_mo': round(cap_f1, 1),
                'cap_f2_mo': round(cap_f2, 1),
                'load_pct': round(load_pct, 1),
                'residual_congestion_mo': round(residual_mo, 1),
                'offset_a3_db': round(offset_applied, 1),
                'status': status,
                'color': color,
                'policy': policy
            })
        return records

# Singleton instance
hex_map_engine = HexMapEngine()
