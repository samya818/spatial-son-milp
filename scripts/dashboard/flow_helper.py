"""
WiseNet V2.0 - Synthetic Transfer Flows & Spatial Dynamics
Calculates representative horizontal (inter-sector) and vertical (inter-frequency F1 <-> F2)
handover flows for 3GPP dual-carrier hexagonal topology.
"""
from typing import List, Dict, Any
import numpy as np

def generate_spatial_flows(sectors_data: List[Dict[str, Any]], top_n: int = 25) -> List[Dict[str, Any]]:
    """
    Identifies sectors with high congestion that execute A3 Handover / CIO offsets,
    and maps horizontal transfers to adjacent sectors and vertical offload to F2 (5G NR).
    """
    flows = []
    congested_sectors = [s for s in sectors_data if s.get('load_pct', 0) > 85.0]
    
    # Sort by congestion
    congested_sectors = sorted(congested_sectors, key=lambda x: x.get('load_pct', 0), reverse=True)
    
    for sec in congested_sectors[:top_n]:
        excess_mo = max(10.0, sec.get('load_mo', 0) - sec.get('capacity_mo', 0) * 0.85)
        offset_db = sec.get('offset_a3_db', 1.5)
        if offset_db <= 0:
            offset_db = 1.5
            
        site_id = sec['site_id']
        sec_id = sec['sector_id']
        
        # 1. Vertical Flow (F1 LTE 1.8GHz -> F2 5G NR 3.5GHz intra-site)
        vertical_vol = excess_mo * 0.45 * (offset_db / 3.0)
        flows.append({
            'source_id': f"{sec_id}_F1",
            'target_id': f"{sec_id}_F2",
            'source_label': f"{sec_id} (F1 LTE)",
            'target_label': f"{sec_id} (F2 5G NR)",
            'flow_type': 'Vertical (Inter-Porteuse)',
            'volume_mo': round(vertical_vol, 1),
            'offset_db': offset_db,
            'source_coords': [sec['centroid_lon'], sec['centroid_lat']],
            'target_coords': [sec['centroid_lon'] + 0.0008, sec['centroid_lat'] + 0.0008]
        })
        
        # 2. Horizontal Flow (Neighboring sector handover)
        # S1 -> S2 or S3
        sec_num = int(sec_id.split('_sec')[-1]) if '_sec' in sec_id else 1
        target_sec_num = 2 if sec_num == 1 else (3 if sec_num == 2 else 1)
        target_sec_id = f"{site_id}_sec{target_sec_num}"
        
        horiz_vol = excess_mo * 0.35 * (offset_db / 3.0)
        flows.append({
            'source_id': f"{sec_id}_F1",
            'target_id': f"{target_sec_id}_F1",
            'source_label': f"{sec_id} (F1)",
            'target_label': f"{target_sec_id} (F1)",
            'flow_type': 'Horizontal (Inter-Secteur A3)',
            'volume_mo': round(horiz_vol, 1),
            'offset_db': offset_db,
            'source_coords': [sec['centroid_lon'], sec['centroid_lat']],
            'target_coords': [sec['centroid_lon'] - 0.0015, sec['centroid_lat'] + 0.0012]
        })
        
    return flows
