import polars as pl
import numpy as np
import pickle
import json
import yaml
from pathlib import Path
import sys
from tqdm import tqdm

# Ajout du root au path
sys.path.append(str(Path.cwd()))
from src.milp_engine import build_H_matrices, solve_congestion_milp

class SONVerifier:
    def __init__(self, model_name='xgb_q80'):
        self.model_name = model_name
        self.load_assets()

    def load_assets(self):
        with open(f'models/{self.model_name}.pkl', 'rb') as f:
            self.model = pickle.load(f)
        self.fractions_df = pl.read_parquet('offline/fractions_1024.parquet')
        with open('config/network_topology_1024.yaml', 'r') as f:
            self.topology = yaml.safe_load(f)
        with open('data/processed/cell_antenna_map_1024.json', 'r') as f:
            self.coverage_1024 = json.load(f)
        self.cell_to_ant = {}
        for ant_id, cells in self.coverage_1024.items():
            for c in cells: self.cell_to_ant[int(c)] = ant_id
        
        full_df = pl.read_parquet('data/processed/features_target_1024cells.parquet')
        max_slot = full_df['slot_30m'].max()
        self.test_start_slot = max_slot - (48 * 1800)
        self.df_raw = full_df.filter(pl.col('slot_30m') >= self.test_start_slot).sort(['slot_30m', 'square_id'])
        unique_slots = self.df_raw['slot_30m'].unique().sort().to_list()[:48]
        self.df_raw = self.df_raw.filter(pl.col('slot_30m').is_in(unique_slots))
        self.delta_levels = sorted(self.fractions_df['delta_dB'].unique().to_list())
        
        from src.predictor import TrafficPredictor
        self.FEATURE_COLS = TrafficPredictor().feature_cols

    def run_tests(self):
        slots = sorted(self.df_raw['slot_30m'].unique().to_list())
        test_indices = [10, 20, 30] # Equivalent to 100, 200, 300 in a longer sequence
        
        print("\n--- TEST 1 : CONSERVATION DE MASSE ---")
        for idx in test_indices:
            slot = slots[idx]
            slot_df = self.df_raw.filter(pl.col('slot_30m') == slot)
            
            # Predict
            X = slot_df.select(self.FEATURE_COLS).to_numpy()
            preds = self.model.predict(X)
            antenna_preds = {}
            for i, row in enumerate(slot_df.iter_rows(named=True)):
                ant_id = self.cell_to_ant.get(row['square_id'])
                if ant_id:
                    antenna_preds[ant_id] = antenna_preds.get(ant_id, 0.0) + float(preds[i])
            
            ant_stats = {a: {'V_a': v, 'C_a': self.topology['antennas'][a]['capacity_mo']} for a, v in antenna_preds.items()}
            h_antennas, H_deleste, H_recv = build_H_matrices(self.fractions_df, antenna_preds, self.coverage_1024)
            solution, _ = solve_congestion_milp(h_antennas, ant_stats, H_deleste, H_recv, self.delta_levels)
            
            if not solution: continue
            
            # Actual Realization for Mass Check
            v_orig_total = slot_df['internet_volume'].sum()
            current_ant_volumes = {ant_id: 0.0 for ant_id in self.coverage_1024.keys()}
            
            for m_id, cells in self.coverage_1024.items():
                delta = solution[m_id]['delta_dB']
                m_fracs = self.fractions_df.filter((pl.col('master_id') == m_id) & (pl.col('delta_dB') == delta))
                sub_df = slot_df.filter(pl.col('square_id').is_in(cells))
                for row in sub_df.iter_rows(named=True):
                    sid, v_cell = row['square_id'], row['internet_volume']
                    c_fracs = m_fracs.filter(pl.col('square_id') == sid)
                    for f_row in c_fracs.iter_rows(named=True):
                        if f_row['target_ant'] in current_ant_volumes:
                            current_ant_volumes[f_row['target_ant']] += v_cell * f_row['fraction']
            
            v_final_total = sum(current_ant_volumes.values())
            print(f"Slot {idx}: Avant={v_orig_total:.2f}, Après={v_final_total:.2f}, Diff={v_final_total - v_orig_total:.2f}")

        print("\n--- TEST 2 : SATURATION DES RECEVEURS ---")
        # Use last analyzed slot
        # Find antenna with max receiving traffic
        receivers = {}
        for m_id, cells in self.coverage_1024.items():
            delta = solution[m_id]['delta_dB']
            m_fracs = self.fractions_df.filter((pl.col('master_id') == m_id) & (pl.col('delta_dB') == delta) & (pl.col('target_ant') != m_id))
            sub_df = slot_df.filter(pl.col('square_id').is_in(cells))
            for row in sub_df.iter_rows(named=True):
                sid, v_cell = row['square_id'], row['internet_volume']
                c_fracs = m_fracs.filter(pl.col('square_id') == sid)
                for f_row in c_fracs.iter_rows(named=True):
                    t = f_row['target_ant']
                    receivers[t] = receivers.get(t, 0.0) + v_cell * f_row['fraction']
        
        top_receivers = sorted(receivers.items(), key=lambda x: x[1], reverse=True)[:5]
        for ant, v_rec in top_receivers:
            v_init = sum(slot_df.filter(pl.col('square_id').is_in(self.coverage_1024[ant]))['internet_volume'])
            v_final = current_ant_volumes[ant]
            cap = self.topology['antennas'][ant]['capacity_mo']
            print(f"{ant}: Init={v_init:.1f}, Reçu={v_rec:.1f}, Final={v_final:.1f}, Cap={cap:.1f}, Sat={v_final > cap}")

if __name__ == "__main__":
    SONVerifier().run_tests()
