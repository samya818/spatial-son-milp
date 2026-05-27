import polars as pl
import numpy as np
import pickle
import json
import yaml
import sys
from pathlib import Path

# Add src to path
sys.path.append('src')
from predictor import TrafficPredictor
from milp_engine import build_H_matrices, solve_congestion_milp

def debug_sim():
    # Load configs
    with open('config/network_topology.yaml', 'r') as f:
        topology = yaml.safe_load(f)
    with open('data/processed/cell_antenna_map_600.json', 'r') as f:
        coverage = json.load(f)
    
    fractions_df = pl.read_parquet('offline/fractions.parquet')
    nominal_caps_df = pl.read_parquet('data/processed/nominal_capacities.parquet')
    
    # Predictor
    predictor = TrafficPredictor(model_path='models/xgb_q80.pkl')
    
    # Test data (one slot from day 56+)
    df_feat = pl.read_parquet('data/processed/features_target_600cells.parquet')
    DAY56_SLOT = 56 * 48
    test_slots = sorted(df_feat.filter(pl.col('slot_30m') >= DAY56_SLOT)['slot_30m'].unique().to_list())
    
    if not test_slots:
        print("Aucun slot de test trouvé.")
        return
        
    slot = test_slots[0]
    slot_df = df_feat.filter(pl.col('slot_30m') == slot)
    
    # 1. Predictions
    preds = predictor.predict(slot_df)
    
    # 2. Aggregation
    cell_to_ant = {}
    for ant, cells in coverage.items():
        for sid in cells:
            cell_to_ant[int(sid)] = ant
            
    antenna_preds = {}
    for sid, pred in zip(slot_df['square_id'], preds):
        ant = cell_to_ant.get(int(sid))
        if ant:
            antenna_preds[ant] = antenna_preds.get(ant, 0.0) + float(pred)
            
    # 3. Stats & Trigger
    antenna_stats = {}
    triggered = []
    
    # Get nominal caps for this slot
    hour = (slot % 48) / 2
    plage = 0 if hour < 6 else (1 if hour < 12 else (2 if hour < 19 else 3))
    is_we = int((slot // 48) % 7 >= 5)
    
    for ant_id, V_pred in antenna_preds.items():
        C_a = topology['antennas'][ant_id]['capacity_mo']
        # Sum nominal caps of cells in coverage
        cells = coverage.get(ant_id, [])
        nom_a = nominal_caps_df.filter(
            (pl.col('square_id').is_in([int(c) for c in cells])) &
            (pl.col('plage') == plage) &
            (pl.col('is_weekend') == is_we)
        )['nominal_capacity'].sum()
        
        antenna_stats[ant_id] = {'V_a': V_pred, 'C_a': C_a}
        if V_pred > nom_a:
            triggered.append(ant_id)
            
    print(f"Slot {slot}: {len(triggered)} antennes déclenchées")
    
    # 4. MILP
    antennas_list, H_deleste, H_recv = build_H_matrices(fractions_df, antenna_preds, coverage)
    delta_levels = sorted(fractions_df['delta_dB'].unique().to_list())
    
    sol, obj = solve_congestion_milp(antennas_list, antenna_stats, H_deleste, H_recv, delta_levels)
    
    if sol:
        print("\n=== DEBUG Slot Calculation ===")
        # Print for some antennas WITH volume
        active_sol_ants = [ant for ant in sol.keys() if antenna_preds.get(ant, 0.0) > 0]
        for ant in active_sol_ants[:5]:
            i = antennas_list.index(ant)
            my_level = delta_levels.index(sol[ant]['delta_dB'])
            déleste = H_deleste[i, my_level]
            # reçu = sum H_recv[i, j, k_j]
            reçu = 0
            for j, aj in enumerate(antennas_list):
                if aj in sol:
                    k_j = delta_levels.index(sol[aj]['delta_dB'])
                    reçu += H_recv[i, j, k_j]
            
            V_orig_real = sum(slot_df.filter(pl.col('square_id').is_in(coverage[ant]))['internet_volume'])
            V_orig_pred = antenna_preds.get(ant, 0.0)
            C_a = antenna_stats.get(ant, {}).get('C_a', 0.0)
            Final = V_orig_real - déleste + reçu
            print(f"{ant}: Real={V_orig_real:.1f}, Pred={V_orig_pred:.1f}, C={C_a:.1f}, Final={Final:.1f}")
    else:
        print("MILP Infeasible or error")

if __name__ == "__main__":
    debug_sim()
