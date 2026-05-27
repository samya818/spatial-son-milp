import polars as pl
import json
import numpy as np
import sys
from pathlib import Path

# Add src to path
sys.path.append('src')
from milp_engine import build_H_matrices

def debug():
    # Load data
    with open('data/processed/cell_antenna_map_600.json', 'r') as f:
        coverage = json.load(f)
    
    fractions_df = pl.read_parquet('offline/fractions.parquet')
    
    # Simulate antenna predictions (using actual data from one slot)
    df_feat = pl.read_parquet('data/processed/features_target_600cells.parquet')
    slot_0 = df_feat.filter(pl.col('slot_30m') == df_feat['slot_30m'].min())
    
    # Simple aggregation for test
    cell_to_ant = {}
    for ant, cells in coverage.items():
        for sid in cells:
            cell_to_ant[int(sid)] = ant
            
    antenna_preds = {}
    for row in slot_0.iter_rows(named=True):
        sid = row['square_id']
        ant = cell_to_ant.get(sid)
        if ant:
            antenna_preds[ant] = antenna_preds.get(ant, 0.0) + row['target_1h']

    ant_ids, H_deleste, H_recv = build_H_matrices(fractions_df, antenna_preds, coverage)
    ant_idx = {a: i for i, a in enumerate(ant_ids)}
    
    print("\n=== DEBUG H_recv ===")
    # Find antennas in antenna_preds that have non-zero volume
    active_ants = [a for a, v in antenna_preds.items() if v > 0]
    print(f"Antennes actives: {len(active_ants)}")
    
    # Find transfers involving these active antennas
    transfers = fractions_df.filter(
        (pl.col('master_id').is_in(active_ants)) & 
        (pl.col('target_ant').is_in(ant_ids)) &
        (pl.col('master_id') != pl.col('target_ant'))
    )
    
    if not transfers.is_empty():
        print(f"Nombre de lignes de transfert trouvées: {len(transfers)}")
        # Take the first transfer pair
        a = transfers['master_id'][0]
        b = transfers['target_ant'][0]
        
        i_a = ant_idx.get(a)
        i_b = ant_idx.get(b)
        
        print(f"Test transfert de {a} vers {b}")
        for k in range(7):
            val = H_recv[i_b, i_a, k]
            print(f"  k={k}: H_recv[{b} reçoit de {a}] = {val:.2f}")
            
    # Global conservation check for antenna 'a'
    if i_a is not None:
        print(f"\nConservation pour {a}:")
        n_cells_coverage = len(coverage[a])
        n_cells_fractions = fractions_df.filter(pl.col('master_id') == a)['square_id'].n_unique()
        print(f"  Cellules dans coverage: {n_cells_coverage}")
        print(f"  Cellules dans fractions_df: {n_cells_fractions}")
        
        for k in range(7):
            deleste = H_deleste[i_a, k]
            recu_total = H_recv[:, i_a, k].sum()
            print(f"  k={k}: Delesté={deleste:.2f}, Somme reçue par voisins={recu_total:.2f}, Diff={deleste-recu_total:.6f}")
            if deleste < 0 or recu_total < 0:
                print("  !!! VALEUR NÉGATIVE DÉTECTÉE !!!")
        # Check if there are ANY transfers in fractions_df for the master antennas we have
        master_transfers = fractions_df.filter(
            (pl.col('master_id').is_in(active_ants)) & 
            (pl.col('master_id') != pl.col('target_ant'))
        )
        if not master_transfers.is_empty():
            print(f"Transfers exist for masters but target_ant not in coverage: {master_transfers['target_ant'].unique().to_list()}")
        else:
            print("Aucun transfert du tout pour ces masters.")

if __name__ == "__main__":
    debug()
