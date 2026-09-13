"""
WiseNet V2.0 - Synthetic Transfer Flows & Spatial Dynamics
Calculates representative horizontal (inter-sector) and vertical (inter-frequency F1 <-> F2)
handover flows for 3GPP dual-carrier hexagonal topology.
"""
from typing import List, Dict, Any
import numpy as np

def generate_spatial_flows(sectors_data: List[Dict[str, Any]], top_n: int = 30) -> List[Dict[str, Any]]:
    """
    Identifies sectors that execute A3 Handover / CIO offsets,
    and maps horizontal transfers to adjacent sectors and vertical offload to F2 (5G NR).
    """
    flows = []
    
    # Active offload sectors: either have an offset applied or elevated load
    active_sectors = [
        s for s in sectors_data 
        if s.get('offset_a3_db', 0.0) > 0.0 or s.get('load_pct', 0.0) >= 70.0
    ]
    
    # Sort by applied offset and load
    active_sectors = sorted(
        active_sectors, 
        key=lambda x: (x.get('offset_a3_db', 0.0), x.get('load_pct', 0.0)), 
        reverse=True
    )
    
    for sec in active_sectors[:top_n]:
        offset_db = sec.get('offset_a3_db', 0.0)
        if offset_db <= 0.0:
            offset_db = 1.5
            
        load_f1 = sec.get('load_f1_mo', sec.get('load_mo', 1000.0) * 0.5)
        cap_f1 = sec.get('cap_f1_mo', 5600.0)
        excess_mo = max(150.0, load_f1 - cap_f1 * 0.70)
        
        site_id = sec['site_id']
        sec_id = sec['sector_id']
        
        # 1. Vertical Flow (F1 LTE 1.8GHz -> F2 5G NR 3.5GHz intra-site)
        vertical_vol = excess_mo * 0.60 * (offset_db / 3.0)
        flows.append({
            'source_id': f"{sec_id}_F1",
            'target_id': f"{sec_id}_F2",
            'source_label': f"{sec_id} (F1 LTE)",
            'target_label': f"{sec_id} (F2 5G NR)",
            'flow_type': 'Vertical (Inter-Carrier F1->F2)',
            'volume_mo': round(vertical_vol, 1),
            'offset_db': offset_db,
            'source_coords': [sec['centroid_lon'], sec['centroid_lat']],
            'target_coords': [sec['centroid_lon'] + 0.0010, sec['centroid_lat'] + 0.0008]
        })
        
        # 2. Horizontal Flow (Neighboring sector handover)
        sec_num = int(sec_id.split('_sec')[-1]) if '_sec' in sec_id else 1
        target_sec_num = 2 if sec_num == 1 else (3 if sec_num == 2 else 1)
        target_sec_id = f"{site_id}_sec{target_sec_num}"
        
        horiz_vol = excess_mo * 0.35 * (offset_db / 3.0)
        flows.append({
            'source_id': f"{sec_id}_F1",
            'target_id': f"{target_sec_id}_F1",
            'source_label': f"{sec_id} (F1)",
            'target_label': f"{target_sec_id} (F1)",
            'flow_type': 'Horizontal (Inter-Sector A3)',
            'volume_mo': round(horiz_vol, 1),
            'offset_db': offset_db,
            'source_coords': [sec['centroid_lon'], sec['centroid_lat']],
            'target_coords': [sec['centroid_lon'] - 0.0016, sec['centroid_lat'] + 0.0014]
        })
        
    return flows
