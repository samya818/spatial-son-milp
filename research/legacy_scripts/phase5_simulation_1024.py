import polars as pl
import numpy as np
import pickle
import json
import yaml
from pathlib import Path
import sys
from tqdm import tqdm

# Ajout du root au path pour importer les modules src
sys.path.append(str(Path.cwd()))
from src.milp_engine import build_H_matrices, solve_congestion_milp
from src.predictor import TrafficPredictor

# --- CONFIGURATION BLOC 1024 ---
ROOT = Path.cwd()
DATA_PATH = ROOT / 'data' / 'processed' / 'features_target_1024cells.parquet'
FRACTIONS_PATH = ROOT / 'offline' / 'fractions_1024.parquet'
NOMINAL_CAPS_PATH = ROOT / 'data' / 'processed' / 'nominal_capacities_1024.parquet'
TOPOLOGY_PATH = ROOT / 'config' / 'network_topology_1024.yaml'
MAP_PATH = ROOT / 'data' / 'processed' / 'cell_antenna_map_1024.json'
MODELS_DIR = ROOT / 'models'

class SONSimulator:
    def __init__(self, policy='dynamic', model_name='xgb_q80'):
        self.policy = policy
        self.model_name = model_name
        self.load_assets()
        self.reset()

    def load_assets(self):
        print(f"--- Chargement des assets ({self.policy}/{self.model_name}) ---")
        with open(MODELS_DIR / f'{self.model_name}.pkl', 'rb') as f:
            self.model = pickle.load(f)
        
        self.fractions_df = pl.read_parquet(FRACTIONS_PATH)
        self.nominal_caps = pl.read_parquet(NOMINAL_CAPS_PATH)
        
        with open(TOPOLOGY_PATH, 'r') as f:
            self.topology = yaml.safe_load(f)
        with open(MAP_PATH, 'r') as f:
            self.coverage_1024 = json.load(f)
            
        # Mapping cellule -> antenne maître
        self.cell_to_ant = {}
        for ant_id, cells in self.coverage_1024.items():
            for c in cells: self.cell_to_ant[int(c)] = ant_id
            
        # Données de test (48 slots = 24h)
        full_df = pl.read_parquet(DATA_PATH)
        max_slot = full_df['slot_30m'].max()
        self.test_start_slot = max_slot - (48 * 1800)
        self.df_raw = full_df.filter(pl.col('slot_30m') >= self.test_start_slot).sort(['slot_30m', 'square_id'])
        
        unique_slots = self.df_raw['slot_30m'].unique().sort().to_list()[:48]
        self.df_raw = self.df_raw.filter(pl.col('slot_30m').is_in(unique_slots))
        
        self.delta_levels = sorted(self.fractions_df['delta_dB'].unique().to_list())
        
        # Features list from predictor (it's updated now)
        from src.predictor import TrafficPredictor
        tmp_pred = TrafficPredictor()
        self.FEATURE_COLS = tmp_pred.feature_cols

    def reset(self):
        self.current_offsets = {ant_id: 0.0 for ant_id in self.coverage_1024.keys()}
        self.total_unsatisfied = 0.0
        self.decisions_count = 0

    def run(self):
        slots = sorted(self.df_raw['slot_30m'].unique().to_list())
        
        for slot in tqdm(slots, desc=f"Simulation {self.policy}"):
            slot_df = self.df_raw.filter(pl.col('slot_30m') == slot)
            
            # Prédiction XGB Q80 (Modèle de production)
            X_slot = slot_df.select(self.FEATURE_COLS).to_numpy()
            preds_1h = self.model.predict(X_slot)
            
            antenna_preds = {}
            for i, row in enumerate(slot_df.iter_rows(named=True)):
                ant_id = self.cell_to_ant.get(row['square_id'])
                if ant_id:
                    if ant_id not in antenna_preds:
                        antenna_preds[ant_id] = 0.0
                    antenna_preds[ant_id] += float(preds_1h[i])
            
            ant_stats = {a: {'V_a': v, 'C_a': self.topology['antennas'][a]['capacity_mo']} for a, v in antenna_preds.items()}
            
            # Décision
            if self.policy == 'dynamic':
                congested = [a for a, s in ant_stats.items() if s['V_a'] > s['C_a'] * 1.0]
                if congested:
                    h_antennas, H_deleste, H_recv = build_H_matrices(self.fractions_df, antenna_preds, self.coverage_1024)
                    solution, _ = solve_congestion_milp(h_antennas, ant_stats, H_deleste, H_recv, self.delta_levels)
                    if solution:
                        self.decisions_count += 1
                        for ant_id, res in solution.items():
                            self.current_offsets[ant_id] = res['delta_dB']
                else:
                    for ant_id in self.current_offsets: self.current_offsets[ant_id] = 0.0

            # RÉALISATION
            current_ant_volumes = {ant_id: 0.0 for ant_id in self.coverage_1024.keys()}
            
            for master_id, current_delta in self.current_offsets.items():
                master_fracs = self.fractions_df.filter(
                    (pl.col('master_id') == master_id) & (pl.col('delta_dB') == current_delta)
                )
                cells_in_ant = self.coverage_1024[master_id]
                sub_df = slot_df.filter(pl.col('square_id').is_in(cells_in_ant))
                
                for row in sub_df.iter_rows(named=True):
                    sid = row['square_id']
                    v_cell = row['internet_volume']
                    cell_fracs = master_fracs.filter(pl.col('square_id') == sid)
                    for f_row in cell_fracs.iter_rows(named=True):
                        target_ant = f_row['target_ant']
                        if target_ant in current_ant_volumes:
                            current_ant_volumes[target_ant] += v_cell * f_row['fraction']

            # DEBUG RÉALISATION
            if self.policy == 'dynamic' and self.decisions_count == 1:
                print("\n=== REAL VOLUMES REALIZED ===")
                for ant in h_antennas[:10]:
                    print(f"{ant}: Real_Final={current_ant_volumes[ant]:.1f}")

            # Calcul de l'insatisfaction
            for ant_id, v_final in current_ant_volumes.items():
                cap = self.topology['antennas'][ant_id]['capacity_mo']
                self.total_unsatisfied += max(0.0, v_final - cap)

        return {
            'policy': self.policy,
            'total_unsatisfied': self.total_unsatisfied,
            'decisions_made': self.decisions_count
        }

if __name__ == "__main__":
    sim_static = SONSimulator(policy='static', model_name='xgb_q50')
    res_static = sim_static.run()
    
    sim_dynamic = SONSimulator(policy='dynamic', model_name='xgb_q50')
    res_dynamic = sim_dynamic.run()
    
    print("\n" + "="*40)
    print("RÉSULTATS BLOC 1024 CELLULES (ZONE DENSE)")
    print("="*40)
    print(f"STATIQUE : {res_static['total_unsatisfied']:.2f} Mo")
    print(f"DYNAMIQUE: {res_dynamic['total_unsatisfied']:.2f} Mo")
    gain = (res_static['total_unsatisfied'] - res_dynamic['total_unsatisfied']) / (res_static['total_unsatisfied'] + 1e-6) * 100
    print(f"AMÉLIORATION : {gain:.2f}%")
    print(f"Décisions dynamiques prises : {res_dynamic['decisions_made']}")
